"""Multiplayer game manager handling real-time gameplay orchestration."""

import asyncio
import json
import time
from datetime import UTC, datetime, timedelta

import redis.asyncio as redis_lib
import structlog

from app.domains.locations.service import LocationService
from app.domains.multiplayer.connection_manager import ConnectionManager
from app.domains.multiplayer.entities import MultiplayerGuessEntity
from app.domains.multiplayer.events import ClientEvent, ServerEvent
from app.domains.multiplayer.repository import IMultiplayerGameRepository
from app.domains.multiplayer.service import LOBBY_TTL_SECONDS, MAX_LOBBY_EXTENSIONS
from app.shared.scoring import compute_score, haversine

logger = structlog.get_logger()

ROUND_DURATION_SECONDS = 120
RECONNECT_TIMEOUT_SECONDS = 30
ABANDON_TIMEOUT_SECONDS = 60
COUNTDOWN_SECONDS = 3
LOBBY_EXPIRY_WARNING_SECONDS = 300
RATE_LIMIT_MAX = 10
RATE_LIMIT_WINDOW = 1.0


def _iso_utc(value: datetime) -> str:
    dt = value if value.tzinfo else value.replace(tzinfo=UTC)
    return dt.astimezone(UTC).isoformat().replace("+00:00", "Z")


class GameManager:
    def __init__(
        self,
        repository: IMultiplayerGameRepository,
        connection_manager: ConnectionManager,
        location_service: LocationService,
        redis_client: redis_lib.Redis,
    ) -> None:
        self.repo = repository
        self.cm = connection_manager
        self.location_service = location_service
        self.redis = redis_client
        self._round_locks: dict[str, asyncio.Lock] = {}
        self._timer_tasks: dict[str, asyncio.Task] = {}
        self._reconnect_tasks: dict[str, asyncio.Task] = {}
        self._abandon_tasks: dict[str, asyncio.Task] = {}
        self._lobby_tasks: dict[str, asyncio.Task] = {}
        self._rate_limits: dict[str, list[float]] = {}

    def _get_lock(self, game_id: str) -> asyncio.Lock:
        if game_id not in self._round_locks:
            self._round_locks[game_id] = asyncio.Lock()
        return self._round_locks[game_id]

    async def handle_message(self, game_id: str, user_id: str, raw: str) -> None:
        if not self._check_rate_limit(f"{game_id}:{user_id}"):
            await self.cm.send_to_player(
                game_id,
                user_id,
                {
                    "type": ServerEvent.ERROR,
                    "code": "RATE_LIMITED",
                    "message": "Too many messages",
                },
            )
            return

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            await self.cm.send_to_player(
                game_id,
                user_id,
                {
                    "type": ServerEvent.ERROR,
                    "code": "INVALID_JSON",
                    "message": "Message is not valid JSON",
                },
            )
            return

        msg_type = data.get("type")
        if not isinstance(msg_type, str):
            await self.cm.send_to_player(
                game_id,
                user_id,
                {
                    "type": ServerEvent.ERROR,
                    "code": "MISSING_TYPE",
                    "message": "Message must include a 'type' field",
                },
            )
            return

        try:
            event = ClientEvent(msg_type)
        except ValueError:
            await self.cm.send_to_player(
                game_id,
                user_id,
                {
                    "type": ServerEvent.ERROR,
                    "code": "UNKNOWN_TYPE",
                    "message": f"Unknown message type: {msg_type}",
                },
            )
            return

        if event == ClientEvent.START_GAME:
            await self._handle_start_game(game_id, user_id)
        elif event == ClientEvent.SUBMIT_GUESS:
            lat = data.get("lat")
            lng = data.get("lng")
            if lat is None or lng is None:
                await self.cm.send_to_player(
                    game_id,
                    user_id,
                    {
                        "type": ServerEvent.ERROR,
                        "code": "MISSING_FIELD",
                        "message": "lat and lng are required for submit_guess",
                    },
                )
                return
            if not isinstance(lat, int | float) or not (-90 <= lat <= 90):
                await self.cm.send_to_player(
                    game_id,
                    user_id,
                    {
                        "type": ServerEvent.ERROR,
                        "code": "INVALID_FIELD",
                        "message": "lat must be a number between -90 and 90",
                    },
                )
                return
            if not isinstance(lng, int | float) or not (-180 <= lng <= 180):
                await self.cm.send_to_player(
                    game_id,
                    user_id,
                    {
                        "type": ServerEvent.ERROR,
                        "code": "INVALID_FIELD",
                        "message": "lng must be a number between -180 and 180",
                    },
                )
                return
            await self._handle_submit_guess(game_id, user_id, float(lat), float(lng))
        elif event == ClientEvent.FORFEIT:
            await self._handle_forfeit(game_id, user_id)
        elif event == ClientEvent.EXTEND_LOBBY:
            await self._handle_extend_lobby(game_id, user_id)
        elif event == ClientEvent.LEAVE_LOBBY:
            await self._handle_leave_lobby(game_id, user_id)
        elif event == ClientEvent.REFRESH_TOKEN:
            pass  # Token refresh handled at WS layer

    async def on_player_connected(self, game_id: str, user_id: str) -> None:
        doc = await self._load(game_id)
        if not doc:
            return

        player = next((p for p in doc["players"] if p["user_id"] == user_id), None)
        if not player:
            return

        reconnect_key = f"{game_id}:{user_id}"
        if reconnect_key in self._reconnect_tasks:
            self._reconnect_tasks[reconnect_key].cancel()
            del self._reconnect_tasks[reconnect_key]

        if player.get("status") == "disconnected":
            await self.repo.update_player(
                game_id,
                user_id,
                {
                    "status": "connected",
                    "disconnected_at": None,
                },
            )

            await self.cm.broadcast(
                game_id,
                {
                    "type": ServerEvent.PLAYER_RECONNECTED,
                    "userId": user_id,
                },
                exclude=user_id,
            )

        abandon_key = game_id
        if abandon_key in self._abandon_tasks:
            self._abandon_tasks[abandon_key].cancel()
            del self._abandon_tasks[abandon_key]

        if doc["status"] in ("active", "waiting"):
            await self._send_game_state(game_id, user_id, doc)

        if doc["status"] == "waiting" and game_id not in self._lobby_tasks:
            self._lobby_tasks[game_id] = asyncio.create_task(
                self._lobby_expiry_watcher(game_id, doc["invite_code"], doc["host_id"])
            )

    async def on_player_disconnected(self, game_id: str, user_id: str) -> None:
        doc = await self._load(game_id)
        if not doc:
            return

        player = next((p for p in doc["players"] if p["user_id"] == user_id), None)
        if not player:
            return

        if player["status"] == "forfeited":
            return

        if player["status"] == "disconnected":
            return

        if self.cm.has_local_connection(game_id, user_id):
            return

        await self.repo.update_player(
            game_id,
            user_id,
            {
                "status": "disconnected",
                "disconnected_at": datetime.now(UTC),
            },
        )

        deadline = datetime.now(UTC) + timedelta(seconds=RECONNECT_TIMEOUT_SECONDS)

        await self.cm.broadcast(
            game_id,
            {
                "type": ServerEvent.PLAYER_DISCONNECTED,
                "userId": user_id,
                "reconnectDeadline": _iso_utc(deadline),
            },
        )

        reconnect_key = f"{game_id}:{user_id}"
        self._reconnect_tasks[reconnect_key] = asyncio.create_task(
            self._reconnect_timeout(game_id, user_id)
        )

        fresh = await self._load(game_id)
        active_players = [
            p for p in (fresh["players"] if fresh else []) if p["status"] != "forfeited"
        ]
        if (
            fresh
            and fresh["status"] == "active"
            and active_players
            and all(p["status"] == "disconnected" for p in active_players)
            and game_id not in self._abandon_tasks
        ):
            self._abandon_tasks[game_id] = asyncio.create_task(
                self._abandon_timeout(game_id)
            )

    async def cleanup_game(self, game_id: str) -> None:
        self._round_locks.pop(game_id, None)
        for key in [k for k in self._timer_tasks if k.startswith(game_id)]:
            self._timer_tasks[key].cancel()
            del self._timer_tasks[key]
        for key in [k for k in self._reconnect_tasks if k.startswith(game_id)]:
            self._reconnect_tasks[key].cancel()
            del self._reconnect_tasks[key]
        if game_id in self._abandon_tasks:
            self._abandon_tasks[game_id].cancel()
            del self._abandon_tasks[game_id]
        if game_id in self._lobby_tasks:
            self._lobby_tasks[game_id].cancel()
            del self._lobby_tasks[game_id]

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

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
        guess_building = await self.location_service.resolve_location_name(lat, lng)
        same_building = (
            actual_building is not None
            and guess_building is not None
            and actual_building == guess_building
        )
        score = compute_score(distance, same_building=same_building)

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
        if doc:
            await self._check_last_player_standing(game_id, doc)

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

    # ------------------------------------------------------------------
    # Round lifecycle
    # ------------------------------------------------------------------

    async def _start_round(self, game_id: str, round_index: int) -> None:
        doc = await self._load(game_id)
        if not doc:
            return

        if round_index >= len(doc["rounds"]):
            await self._complete_game(game_id)
            return

        now = datetime.now(UTC)
        expires_at = now + timedelta(seconds=ROUND_DURATION_SECONDS)

        await self.repo.update_round(
            game_id,
            round_index,
            {
                "started_at": now,
                "expires_at": expires_at,
            },
        )
        await self.repo.update_game(
            game_id,
            {
                "current_round": round_index + 1,
                "last_activity_at": now,
            },
        )

        rd = doc["rounds"][round_index]

        await self.cm.broadcast(
            game_id,
            {
                "type": ServerEvent.ROUND_START,
                "round": round_index + 1,
                "imageUrl": rd["image_url"],
                "expiresAt": _iso_utc(expires_at),
            },
        )

        timer_key = f"{game_id}:round:{round_index}"
        if timer_key in self._timer_tasks:
            self._timer_tasks[timer_key].cancel()
        self._timer_tasks[timer_key] = asyncio.create_task(
            self._round_timer(game_id, round_index, ROUND_DURATION_SECONDS)
        )

    async def _round_timer(
        self, game_id: str, round_index: int, seconds: float
    ) -> None:
        try:
            await asyncio.sleep(seconds)
            await self._try_resolve_round(game_id, round_index)
        except asyncio.CancelledError:
            pass

    async def _try_resolve_round(self, game_id: str, round_index: int) -> None:
        lock = self._get_lock(game_id)
        async with lock:
            doc = await self._load(game_id)
            if not doc or doc["status"] != "active":
                return

            if round_index >= len(doc["rounds"]):
                return

            resolved = await self.repo.mark_round_resolved(game_id, round_index)
            if not resolved:
                return

            timer_key = f"{game_id}:round:{round_index}"
            if timer_key in self._timer_tasks:
                self._timer_tasks[timer_key].cancel()
                del self._timer_tasks[timer_key]

            doc = await self._load(game_id)
            if not doc:
                return
            rd = doc["rounds"][round_index]

            active_players = [p for p in doc["players"] if p["status"] != "forfeited"]
            guesses = rd.get("guesses", {})

            results = []
            for p in active_players:
                g = guesses.get(p["user_id"])
                if g:
                    results.append(
                        {
                            "userId": p["user_id"],
                            "name": p["name"],
                            "score": g["score"],
                            "distanceMeters": g["distance_meters"],
                            "guess": {"lat": g["lat"], "lng": g["lng"]},
                        }
                    )
                else:
                    results.append(
                        {
                            "userId": p["user_id"],
                            "name": p["name"],
                            "score": 0,
                            "distanceMeters": None,
                            "guess": None,
                        }
                    )

            results.sort(key=lambda r: r["score"], reverse=True)

            standings = [
                {
                    "userId": p["user_id"],
                    "name": p["name"],
                    "totalScore": p.get("total_score", 0),
                }
                for p in doc["players"]
            ]

            standings.sort(key=lambda s: s["totalScore"], reverse=True)
            for i, s in enumerate(standings):
                s["rank"] = i + 1

            await self.cm.broadcast(
                game_id,
                {
                    "type": ServerEvent.ROUND_RESULT,
                    "round": round_index + 1,
                    "results": results,
                    "actual": {"lat": rd["actual_lat"], "lng": rd["actual_lng"]},
                    "locationName": rd.get("location_name"),
                    "standings": standings,
                },
            )

            await self.repo.update_game(
                game_id, {"last_activity_at": datetime.now(UTC)}
            )

            next_index = round_index + 1
            if next_index >= len(doc["rounds"]):
                await self._complete_game(game_id)
            else:
                # Brief pause before next round
                await asyncio.sleep(1)
                await self._start_round(game_id, next_index)

    async def _complete_game(self, game_id: str) -> None:
        doc = await self._load(game_id)
        if not doc:
            return

        await self.repo.update_game(
            game_id,
            {
                "status": "completed",
                "last_activity_at": datetime.now(UTC),
            },
        )

        player_distances: dict[str, float] = {}
        player_times: dict[str, float] = {}
        for p in doc["players"]:
            total_dist = 0.0
            total_time = 0.0
            for rd in doc["rounds"]:
                g = rd.get("guesses", {}).get(p["user_id"])
                if g:
                    total_dist += g.get("distance_meters", 0)
                    if g.get("submitted_at") and rd.get("started_at"):
                        submitted = g["submitted_at"]
                        started = rd["started_at"]
                        if isinstance(submitted, datetime):
                            total_time += (submitted - started).total_seconds()
            player_distances[p["user_id"]] = total_dist
            player_times[p["user_id"]] = total_time

        standings = [
            {
                "userId": p["user_id"],
                "name": p["name"],
                "totalScore": p.get("total_score", 0),
            }
            for p in doc["players"]
        ]
        standings.sort(
            key=lambda s: (
                -s["totalScore"],
                player_distances.get(s["userId"], float("inf")),
                player_times.get(s["userId"], float("inf")),
            )
        )
        for i, s in enumerate(standings):
            s["rank"] = i + 1

        winner_id = standings[0]["userId"] if standings else None

        round_results = []
        for ri, rd in enumerate(doc["rounds"]):
            guesses = rd.get("guesses", {})
            player_results = []
            for p in doc["players"]:
                g = guesses.get(p["user_id"])
                if g:
                    player_results.append(
                        {
                            "userId": p["user_id"],
                            "name": p["name"],
                            "score": g["score"],
                            "distanceMeters": g["distance_meters"],
                            "guess": {"lat": g["lat"], "lng": g["lng"]},
                        }
                    )
                else:
                    player_results.append(
                        {
                            "userId": p["user_id"],
                            "name": p["name"],
                            "score": 0,
                            "distanceMeters": None,
                            "guess": None,
                        }
                    )
            player_results.sort(key=lambda r: r["score"], reverse=True)
            round_results.append(
                {
                    "round": ri + 1,
                    "results": player_results,
                    "actual": {"lat": rd["actual_lat"], "lng": rd["actual_lng"]},
                    "locationName": rd.get("location_name"),
                }
            )

        await self.cm.broadcast(
            game_id,
            {
                "type": ServerEvent.GAME_OVER,
                "winnerId": winner_id,
                "standings": standings,
                "rounds": round_results,
            },
        )

        await self.cleanup_game(game_id)

    async def _check_last_player_standing(self, game_id: str, doc: dict) -> None:
        if doc["status"] != "active":
            return

        active = [p for p in doc["players"] if p["status"] != "forfeited"]
        if len(active) <= 1:
            await self._complete_game(game_id)

    # ------------------------------------------------------------------
    # Timeout handlers
    # ------------------------------------------------------------------

    async def _reconnect_timeout(self, game_id: str, user_id: str) -> None:
        try:
            await asyncio.sleep(RECONNECT_TIMEOUT_SECONDS)

            doc = await self._load(game_id)
            if not doc:
                return

            player = next((p for p in doc["players"] if p["user_id"] == user_id), None)
            if not player:
                return

            if player["status"] != "disconnected":
                return

            if self.cm.has_local_connection(game_id, user_id):
                return

            if doc["status"] == "waiting":
                if doc["host_id"] == user_id:
                    await self.repo.update_game(game_id, {"status": "cancelled"})
                    await self.cm.broadcast(
                        game_id,
                        {
                            "type": ServerEvent.GAME_CANCELLED,
                            "reason": "Host disconnected",
                        },
                    )
                    await self.cleanup_game(game_id)
                else:
                    await self.repo.remove_player(game_id, user_id)
                    fresh = await self._load(game_id)
                    remaining = (
                        len(fresh["players"])
                        if fresh
                        else max(0, len(doc["players"]) - 1)
                    )
                    await self.cm.broadcast(
                        game_id,
                        {
                            "type": ServerEvent.PLAYER_LEFT,
                            "userId": user_id,
                            "playerCount": remaining,
                        },
                    )
            elif doc["status"] == "active":
                await self.repo.update_player(game_id, user_id, {"status": "forfeited"})
                await self.cm.broadcast(
                    game_id,
                    {
                        "type": ServerEvent.PLAYER_FORFEITED,
                        "userId": user_id,
                    },
                )
                fresh_doc = await self._load(game_id)
                if fresh_doc:
                    await self._check_last_player_standing(game_id, fresh_doc)
        except asyncio.CancelledError:
            pass
        finally:
            reconnect_key = f"{game_id}:{user_id}"
            self._reconnect_tasks.pop(reconnect_key, None)

    async def _abandon_timeout(self, game_id: str) -> None:
        try:
            await asyncio.sleep(ABANDON_TIMEOUT_SECONDS)

            doc = await self._load(game_id)
            if not doc or doc["status"] != "active":
                return

            active_players = [p for p in doc["players"] if p["status"] != "forfeited"]
            if not active_players:
                return
            if any(p["status"] != "disconnected" for p in active_players):
                return

            abandoned = await self.repo.update_game_if_status(
                game_id,
                "active",
                {
                    "status": "abandoned",
                    "last_activity_at": datetime.now(UTC),
                },
            )
            if not abandoned:
                return

            logger.info("game_abandoned", game_id=game_id)
            await self.cleanup_game(game_id)
        except asyncio.CancelledError:
            pass
        finally:
            self._abandon_tasks.pop(game_id, None)

    async def _lobby_expiry_watcher(
        self, game_id: str, invite_code: str, host_id: str
    ) -> None:
        try:
            last_warned_extension = -1
            while True:
                await asyncio.sleep(30)

                doc = await self._load(game_id)
                if not doc or doc["status"] != "waiting":
                    return

                ttl = await self.redis.ttl(f"mp:lobby:{invite_code}")

                if ttl < 0:
                    if doc["status"] == "waiting":
                        await self.repo.update_game(
                            game_id,
                            {
                                "status": "cancelled",
                                "last_activity_at": datetime.now(UTC),
                            },
                        )
                        await self.cm.broadcast(
                            game_id,
                            {
                                "type": ServerEvent.GAME_CANCELLED,
                                "reason": "Lobby expired",
                            },
                        )
                        await self.cleanup_game(game_id)
                    return

                extension_count = doc.get("lobby_extensions", 0)
                if (
                    ttl <= LOBBY_EXPIRY_WARNING_SECONDS
                    and extension_count != last_warned_extension
                ):
                    last_warned_extension = extension_count
                    await self.cm.send_to_player(
                        game_id,
                        host_id,
                        {
                            "type": ServerEvent.LOBBY_EXPIRING,
                        },
                    )
        except asyncio.CancelledError:
            pass
        finally:
            self._lobby_tasks.pop(game_id, None)

    # ------------------------------------------------------------------
    # State sync
    # ------------------------------------------------------------------

    async def _send_game_state(self, game_id: str, user_id: str, doc: dict) -> None:
        current_round = doc.get("current_round", 0)
        round_index = current_round - 1

        round_data = None
        players_guessed: list[str] = []
        has_guessed = False
        previous_rounds: list[dict] = []

        if 0 <= round_index < len(doc["rounds"]):
            rd = doc["rounds"][round_index]
            round_data = {
                "round": current_round,
                "imageUrl": rd["image_url"],
                "expiresAt": _iso_utc(rd["expires_at"])
                if rd.get("expires_at")
                else None,
            }
            guesses = rd.get("guesses", {})
            players_guessed = list(guesses.keys())
            has_guessed = user_id in guesses

        for i in range(round_index):
            rd = doc["rounds"][i]
            g = rd.get("guesses", {}).get(user_id)
            if g:
                previous_rounds.append(
                    {
                        "round": i + 1,
                        "score": g["score"],
                        "distanceMeters": g["distance_meters"],
                    }
                )
            else:
                previous_rounds.append(
                    {
                        "round": i + 1,
                        "score": 0,
                        "distanceMeters": None,
                    }
                )

        players = [
            {
                "userId": p["user_id"],
                "name": p["name"],
                "status": p["status"],
                "totalScore": p.get("total_score", 0),
            }
            for p in doc["players"]
        ]

        await self.cm.send_to_player(
            game_id,
            user_id,
            {
                "type": ServerEvent.GAME_STATE,
                "status": doc["status"],
                "currentRound": current_round,
                "round": round_data,
                "playersGuessed": players_guessed,
                "hasGuessedThisRound": has_guessed,
                "players": players,
                "previousRounds": previous_rounds,
            },
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _load(self, game_id: str) -> dict | None:
        doc = await self.repo.find_by_id(game_id)
        if doc:
            doc["_id"] = str(doc["_id"])
        return doc

    def _check_rate_limit(self, key: str) -> bool:
        now = time.monotonic()
        if key not in self._rate_limits:
            self._rate_limits[key] = []

        timestamps = self._rate_limits[key]
        cutoff = now - RATE_LIMIT_WINDOW
        self._rate_limits[key] = [t for t in timestamps if t > cutoff]

        if len(self._rate_limits[key]) >= RATE_LIMIT_MAX:
            return False

        self._rate_limits[key].append(now)
        return True
