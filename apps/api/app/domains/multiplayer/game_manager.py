"""Multiplayer game manager handling real-time gameplay orchestration."""

import asyncio
import contextlib
from datetime import UTC, datetime

import redis.asyncio as redis_lib
import structlog

from app.domains.games.difficulty import DEFAULT_DIFFICULTY
from app.domains.locations.service import LocationService
from app.domains.multiplayer.connection_manager import ConnectionManager
from app.domains.multiplayer.entities import MultiplayerGuessEntity
from app.domains.multiplayer.events import ServerEvent
from app.domains.multiplayer.game_manager_lifecycle import GameManagerLifecycleMixin
from app.domains.multiplayer.game_manager_messages import GameManagerMessagesMixin
from app.domains.multiplayer.game_manager_rounds import GameManagerRoundsMixin
from app.domains.multiplayer.game_manager_shared import (
    COUNTDOWN_SECONDS,
    REMATCH_LOCK_TTL_SECONDS,
)
from app.domains.multiplayer.game_manager_state import GameManagerStateMixin
from app.domains.multiplayer.game_manager_timeouts import GameManagerTimeoutsMixin
from app.domains.multiplayer.repository import IMultiplayerGameRepository
from app.domains.multiplayer.service import (
    LOBBY_TTL_SECONDS,
    MAX_LOBBY_EXTENSIONS,
    MultiplayerService,
)
from app.shared.scoring import compute_score, haversine

logger = structlog.get_logger()


class GameManager(
    GameManagerMessagesMixin,
    GameManagerLifecycleMixin,
    GameManagerTimeoutsMixin,
    GameManagerRoundsMixin,
    GameManagerStateMixin,
):
    def __init__(
        self,
        repository: IMultiplayerGameRepository,
        connection_manager: ConnectionManager,
        location_service: LocationService,
        multiplayer_service: MultiplayerService,
        redis_client: redis_lib.Redis,
    ) -> None:
        self.repo = repository
        self.cm = connection_manager
        self.location_service = location_service
        self.multiplayer_service = multiplayer_service
        self.redis = redis_client
        self._round_locks: dict[str, asyncio.Lock] = {}
        self._timer_tasks: dict[str, asyncio.Task] = {}
        self._reconnect_tasks: dict[str, asyncio.Task] = {}
        self._abandon_tasks: dict[str, asyncio.Task] = {}
        self._lobby_tasks: dict[str, asyncio.Task] = {}
        self._rate_limits: dict[str, list[float]] = {}
        self._lobby_ready: dict[str, set[str]] = {}

    def _get_lock(self, game_id: str) -> asyncio.Lock:
        if game_id not in self._round_locks:
            self._round_locks[game_id] = asyncio.Lock()
        return self._round_locks[game_id]

    async def _handle_start_game(self, game_id: str, user_id: str) -> None:
        doc = await self._load(game_id)
        if not doc:
            return

        if doc["status"] != "waiting":
            await self.cm.send_to_player(
                game_id,
                user_id,
                {
                    "type": ServerEvent.ERROR,
                    "code": "INVALID_ACTION",
                    "message": "Game is not in lobby phase",
                },
            )
            return

        if doc["host_id"] != user_id:
            await self.cm.send_to_player(
                game_id,
                user_id,
                {
                    "type": ServerEvent.ERROR,
                    "code": "UNAUTHORIZED",
                    "message": "Only the host can start the game",
                },
            )
            return

        active_players = [p for p in doc["players"] if p["status"] != "forfeited"]
        if len(active_players) < 2:
            await self.cm.send_to_player(
                game_id,
                user_id,
                {
                    "type": ServerEvent.ERROR,
                    "code": "INVALID_ACTION",
                    "message": "Need at least 2 players to start",
                },
            )
            return

        lobby_ready = self._lobby_ready.setdefault(game_id, set())
        if any(player["user_id"] not in lobby_ready for player in active_players):
            await self.cm.send_to_player(
                game_id,
                user_id,
                {
                    "type": ServerEvent.ERROR,
                    "code": "INVALID_ACTION",
                    "message": "All players must be ready before starting",
                },
            )
            return

        if game_id in self._lobby_tasks:
            self._lobby_tasks[game_id].cancel()
            del self._lobby_tasks[game_id]

        await self.cm.broadcast(
            game_id,
            {
                "type": ServerEvent.GAME_STARTING,
                "countdown": COUNTDOWN_SECONDS,
            },
        )

        await asyncio.sleep(COUNTDOWN_SECONDS)

        fresh = await self._load(game_id)
        if not fresh:
            return

        if fresh["status"] != "waiting" or fresh["host_id"] != user_id:
            return

        active_players = [p for p in fresh["players"] if p["status"] != "forfeited"]
        if len(active_players) < 2:
            return

        lobby_ready = self._lobby_ready.setdefault(game_id, set())
        if any(player["user_id"] not in lobby_ready for player in active_players):
            return

        now = datetime.now(UTC)
        started = await self.repo.update_game_if_status(
            game_id,
            "waiting",
            {
                "status": "active",
                "started_at": now,
                "current_round": 1,
                "last_activity_at": now,
            },
        )

        if not started:
            return

        self._lobby_ready.pop(game_id, None)
        await self._start_round(game_id, 0)

    async def _handle_submit_guess(
        self, game_id: str, user_id: str, lat: float, lng: float
    ) -> None:
        doc = await self._load(game_id)
        if not doc:
            return

        if doc["status"] != "active":
            await self.cm.send_to_player(
                game_id,
                user_id,
                {
                    "type": ServerEvent.ERROR,
                    "code": "INVALID_ACTION",
                    "message": "Game is not active",
                },
            )
            return

        round_index = doc["current_round"] - 1
        submitted_round = doc["current_round"]
        rd = doc["rounds"][round_index]

        if user_id in rd.get("guesses", {}):
            return  # duplicate guess, silently ignore

        now = datetime.now(UTC)
        distance = haversine(lat, lng, rd["actual_lat"], rd["actual_lng"])

        actual_building = rd.get("location_name")
        guess_building = await self.location_service.resolve_location_name(
            lat,
            lng,
            difficulty=DEFAULT_DIFFICULTY,
        )
        same_building = (
            actual_building is not None
            and guess_building is not None
            and actual_building == guess_building
        )
        score = compute_score(
            distance,
            same_building=same_building,
            difficulty=DEFAULT_DIFFICULTY,
        )

        guess = MultiplayerGuessEntity(
            lat=lat,
            lng=lng,
            distance_meters=round(distance, 2),
            score=score,
            submitted_at=now,
        )

        set_guess = await self.repo.set_guess(game_id, round_index, user_id, guess)
        if not set_guess:
            return

        await self.repo.increment_player_score(game_id, user_id, score)

        await self.cm.send_to_player(
            game_id,
            user_id,
            {
                "type": ServerEvent.GUESS_ACCEPTED,
                "round": submitted_round,
            },
        )

        refreshed = await self._load(game_id)
        if not refreshed:
            return

        current_round_index = refreshed["current_round"] - 1
        if current_round_index != round_index:
            return

        if current_round_index < 0 or current_round_index >= len(refreshed["rounds"]):
            return

        active_players = [p for p in refreshed["players"] if p["status"] != "forfeited"]
        guesses = refreshed["rounds"][current_round_index].get("guesses", {})
        guessed_count = len(guesses)
        remaining = len(active_players) - guessed_count

        await self.cm.broadcast(
            game_id,
            {
                "type": ServerEvent.PLAYER_GUESSED,
                "userId": user_id,
                "remainingPlayers": max(0, remaining),
            },
            exclude=user_id,
        )

        if remaining <= 0:
            await self._try_resolve_round(game_id, current_round_index)

    async def _handle_forfeit(self, game_id: str, user_id: str) -> None:
        await self.repo.update_player(game_id, user_id, {"status": "forfeited"})

        await self.cm.broadcast(
            game_id,
            {
                "type": ServerEvent.PLAYER_FORFEITED,
                "userId": user_id,
            },
        )

        doc = await self._load(game_id)
        if not doc:
            return

        await self._check_last_player_standing(game_id, doc)
        updated = await self._load(game_id)
        await self._maybe_advance_ready_barrier(game_id, updated)

    async def _handle_extend_lobby(self, game_id: str, user_id: str) -> None:
        doc = await self._load(game_id)
        if not doc:
            return

        if doc["host_id"] != user_id:
            await self.cm.send_to_player(
                game_id,
                user_id,
                {
                    "type": ServerEvent.ERROR,
                    "code": "UNAUTHORIZED",
                    "message": "Only the host can extend the lobby",
                },
            )
            return

        if doc["status"] != "waiting":
            return

        if doc.get("lobby_extensions", 0) >= MAX_LOBBY_EXTENSIONS:
            await self.cm.send_to_player(
                game_id,
                user_id,
                {
                    "type": ServerEvent.ERROR,
                    "code": "INVALID_ACTION",
                    "message": "Maximum lobby extensions reached",
                },
            )
            return

        new_count = doc.get("lobby_extensions", 0) + 1
        await self.repo.update_game(
            game_id,
            {
                "lobby_extensions": new_count,
                "last_activity_at": datetime.now(UTC),
            },
        )

        await self.redis.set(
            f"mp:lobby:{doc['invite_code']}",
            game_id,
            ex=LOBBY_TTL_SECONDS,
        )

    async def _handle_leave_lobby(self, game_id: str, user_id: str) -> None:
        doc = await self._load(game_id)
        if not doc or doc["status"] != "waiting":
            return

        if doc["host_id"] == user_id:
            await self.cm.send_to_player(
                game_id,
                user_id,
                {
                    "type": ServerEvent.ERROR,
                    "code": "INVALID_ACTION",
                    "message": "Host cannot leave the lobby; the game would be cancelled",
                },
            )
            return

        await self.repo.remove_player(game_id, user_id)
        await self.repo.update_game(game_id, {"last_activity_at": datetime.now(UTC)})

        self._lobby_ready.setdefault(game_id, set()).discard(user_id)

        reconnect_key = f"{game_id}:{user_id}"
        if reconnect_key in self._reconnect_tasks:
            self._reconnect_tasks[reconnect_key].cancel()
            del self._reconnect_tasks[reconnect_key]

        fresh = await self._load(game_id)
        player_count = (
            len(fresh["players"]) if fresh else max(0, len(doc["players"]) - 1)
        )
        await self.cm.broadcast(
            game_id,
            {
                "type": ServerEvent.PLAYER_LEFT,
                "userId": user_id,
                "playerCount": player_count,
            },
        )

    async def _handle_ready_next(self, game_id: str, user_id: str) -> None:
        doc = await self._load(game_id)
        if not doc or doc["status"] != "active":
            return

        round_number = doc.get("current_round", 0)
        round_index = round_number - 1
        if round_index < 0 or round_index >= len(doc["rounds"]):
            return

        round_data = doc["rounds"][round_index]
        if not round_data.get("_resolved"):
            return

        if round_index + 1 >= len(doc["rounds"]):
            return

        player = next((p for p in doc["players"] if p["user_id"] == user_id), None)
        if not player or player["status"] != "connected":
            return

        await self._mark_player_ready_for_next_round(game_id, round_number, user_id)
        logger.info(
            "ready_next_marked",
            game_id=game_id,
            round=round_number,
            user_id=user_id,
            worker_id=self.cm.worker_id,
        )

        await self._maybe_advance_ready_barrier(game_id, doc)

    async def _handle_ready_up(self, game_id: str, user_id: str) -> None:
        doc = await self._load(game_id)
        if not doc or doc["status"] != "waiting":
            return

        is_player = any(p["user_id"] == user_id for p in doc["players"])
        if not is_player:
            return

        ready = self._lobby_ready.setdefault(game_id, set())
        if user_id in ready:
            return

        ready.add(user_id)
        await self.repo.update_game(game_id, {"last_activity_at": datetime.now(UTC)})
        await self.cm.broadcast(
            game_id,
            {
                "type": ServerEvent.PLAYER_READY,
                "userId": user_id,
            },
        )

    async def _handle_unready(self, game_id: str, user_id: str) -> None:
        doc = await self._load(game_id)
        if not doc or doc["status"] != "waiting":
            return

        ready = self._lobby_ready.setdefault(game_id, set())
        if user_id not in ready:
            return

        ready.discard(user_id)
        await self.repo.update_game(game_id, {"last_activity_at": datetime.now(UTC)})
        await self.cm.broadcast(
            game_id,
            {
                "type": ServerEvent.PLAYER_UNREADY,
                "userId": user_id,
            },
        )

    async def _handle_kick(
        self, game_id: str, user_id: str, target_user_id: str
    ) -> None:
        doc = await self._load(game_id)
        if not doc:
            return

        if doc["status"] != "waiting":
            await self.cm.send_to_player(
                game_id,
                user_id,
                {
                    "type": ServerEvent.ERROR,
                    "code": "INVALID_ACTION",
                    "message": "Kick is only available in the lobby",
                },
            )
            return

        if doc["host_id"] != user_id:
            await self.cm.send_to_player(
                game_id,
                user_id,
                {
                    "type": ServerEvent.ERROR,
                    "code": "UNAUTHORIZED",
                    "message": "Only the host can kick players",
                },
            )
            return

        if target_user_id == doc["host_id"]:
            await self.cm.send_to_player(
                game_id,
                user_id,
                {
                    "type": ServerEvent.ERROR,
                    "code": "INVALID_ACTION",
                    "message": "Host cannot be kicked",
                },
            )
            return

        target = next(
            (p for p in doc["players"] if p["user_id"] == target_user_id), None
        )
        if not target:
            return

        await self.repo.remove_player(game_id, target_user_id)
        await self.repo.update_game(game_id, {"last_activity_at": datetime.now(UTC)})

        self._lobby_ready.setdefault(game_id, set()).discard(target_user_id)

        reconnect_key = f"{game_id}:{target_user_id}"
        if reconnect_key in self._reconnect_tasks:
            self._reconnect_tasks[reconnect_key].cancel()
            del self._reconnect_tasks[reconnect_key]

        await self.cm.send_to_player(
            game_id,
            target_user_id,
            {
                "type": ServerEvent.KICKED,
            },
        )

        target_ws = self.cm.get_local_connections(game_id).get(target_user_id)
        if target_ws:
            with contextlib.suppress(Exception):
                await target_ws.close(code=4011, reason="Kicked by host")

        fresh = await self._load(game_id)
        player_count = (
            len(fresh["players"]) if fresh else max(0, len(doc["players"]) - 1)
        )
        await self.cm.broadcast(
            game_id,
            {
                "type": ServerEvent.PLAYER_LEFT,
                "userId": target_user_id,
                "playerCount": player_count,
            },
        )

    async def _handle_request_rematch(self, game_id: str, user_id: str) -> None:
        doc = await self._load(game_id)
        if not doc:
            return

        if doc["status"] != "completed":
            await self.cm.send_to_player(
                game_id,
                user_id,
                {
                    "type": ServerEvent.ERROR,
                    "code": "INVALID_ACTION",
                    "message": "Rematch is only available after the game ends",
                },
            )
            return

        if doc["host_id"] != user_id:
            await self.cm.send_to_player(
                game_id,
                user_id,
                {
                    "type": ServerEvent.ERROR,
                    "code": "UNAUTHORIZED",
                    "message": "Only the host can start a rematch",
                },
            )
            return

        rematch_lock_key = f"mp:rematch:{game_id}"
        acquired = await self.redis.set(
            rematch_lock_key,
            user_id,
            ex=REMATCH_LOCK_TTL_SECONDS,
            nx=True,
        )
        if not acquired:
            await self.cm.send_to_player(
                game_id,
                user_id,
                {
                    "type": ServerEvent.ERROR,
                    "code": "INVALID_ACTION",
                    "message": "Rematch is already starting",
                },
            )
            return

        host_player = next((p for p in doc["players"] if p["user_id"] == user_id), None)
        if not host_player:
            with contextlib.suppress(Exception):
                await self.redis.delete(rematch_lock_key)
            return

        try:
            mode = doc.get("mode", {})
            environment = mode.get("environment", "any")
            new_game = await self.multiplayer_service.create_game(
                host_id=user_id,
                host_name=host_player.get("name") or "Player",
                avatar_url=host_player.get("avatar_url"),
                environment=environment,
            )

            new_game_id = new_game["_id"]
            invite_code = new_game["invite_code"]
            included_user_ids = {user_id}

            for player in doc["players"]:
                player_id = player["user_id"]
                if player_id == user_id:
                    continue

                try:
                    await self.multiplayer_service.join_game(
                        user_id=player_id,
                        name=player.get("name") or "Player",
                        avatar_url=player.get("avatar_url"),
                        code=invite_code,
                    )
                    included_user_ids.add(player_id)
                except Exception:
                    logger.warning(
                        "rematch_player_join_failed",
                        game_id=game_id,
                        new_game_id=new_game_id,
                        user_id=player_id,
                    )

            await self.cm.broadcast(
                game_id,
                {
                    "type": ServerEvent.REMATCH_STARTING,
                    "newGameId": new_game_id,
                    "inviteCode": invite_code,
                    "includedUserIds": list(included_user_ids),
                },
            )
        except Exception:
            with contextlib.suppress(Exception):
                await self.redis.delete(rematch_lock_key)
            logger.exception("rematch_start_failed", game_id=game_id, user_id=user_id)
            await self.cm.send_to_player(
                game_id,
                user_id,
                {
                    "type": ServerEvent.ERROR,
                    "code": "INVALID_ACTION",
                    "message": "Unable to start rematch right now",
                },
            )
