"""Multiplayer game service containing lobby and game setup business logic."""

import secrets
import string
from datetime import UTC, datetime
from typing import Literal, cast

import redis.asyncio as redis
import structlog

from app.domains.images.repository import IImageRepository
from app.domains.locations.service import LocationService
from app.domains.multiplayer.entities import (
    MultiplayerGameEntity,
    MultiplayerModeEntity,
    MultiplayerPlayerEntity,
    MultiplayerRoundEntity,
)
from app.domains.multiplayer.repository import IMultiplayerGameRepository

logger = structlog.get_logger()

ROUNDS_PER_GAME = 5
INVITE_CODE_LENGTH = 6
INVITE_CODE_CHARS = string.ascii_uppercase + string.digits
MAX_PLAYERS = 5
LOBBY_TTL_SECONDS = 600
MAX_LOBBY_EXTENSIONS = 6


class MultiplayerError(Exception):
    def __init__(self, message: str, status_code: int = 400) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class MultiplayerService:
    def __init__(
        self,
        multiplayer_repository: IMultiplayerGameRepository,
        image_repository: IImageRepository,
        location_service: LocationService,
        redis_client: redis.Redis,
    ) -> None:
        self.repo = multiplayer_repository
        self.image_repo = image_repository
        self.location_service = location_service
        self.redis = redis_client

    async def create_game(
        self,
        host_id: str,
        host_name: str,
        avatar_url: str | None,
        environment: str,
    ) -> dict:
        existing = await self.repo.find_active_by_user(host_id)
        if existing:
            raise MultiplayerError("You already have an active multiplayer game.")

        images = await self.image_repo.sample_random(ROUNDS_PER_GAME, environment)
        if len(images) < ROUNDS_PER_GAME:
            raise MultiplayerError(
                f"Not enough images available (need {ROUNDS_PER_GAME}, found {len(images)})."
            )

        invite_code = await self._generate_invite_code()
        now = datetime.now(UTC)
        mode_environment = cast(Literal["indoor", "outdoor", "any"], environment)

        rounds = [
            MultiplayerRoundEntity(
                round_id=i + 1,
                image_id=str(img["_id"]),
                image_url=img["url"],
                actual_lat=img["latitude"],
                actual_lng=img["longitude"],
                location_name=img.get("location_name"),
            )
            for i, img in enumerate(images)
        ]

        host_player = MultiplayerPlayerEntity(
            user_id=host_id,
            name=host_name,
            avatar_url=avatar_url,
            joined_at=now,
        )

        game = MultiplayerGameEntity(
            host_id=host_id,
            invite_code=invite_code,
            mode=MultiplayerModeEntity(environment=mode_environment),
            players=[host_player],
            rounds=rounds,
            created_at=now,
            last_activity_at=now,
        )

        game_id = await self.repo.create(game)

        await self.redis.set(
            f"mp:lobby:{invite_code}",
            game_id,
            ex=LOBBY_TTL_SECONDS,
        )

        logger.info(
            "multiplayer_game_created",
            game_id=game_id,
            host_id=host_id,
            invite_code=invite_code,
            environment=environment,
        )

        return await self._reload(game_id)

    async def join_game(
        self,
        user_id: str,
        name: str,
        avatar_url: str | None,
        code: str,
    ) -> tuple[dict, MultiplayerPlayerEntity | None]:
        code = code.upper().strip()

        game_id = await self.redis.get(f"mp:lobby:{code}")
        if game_id:
            doc = await self.repo.find_by_id(game_id)
        else:
            doc = await self.repo.find_by_invite_code(code)

        if not doc:
            raise MultiplayerError("Invalid or expired invite code.", 404)

        doc["_id"] = str(doc["_id"])
        game_id = doc["_id"]

        await self._check_lobby_expiry(doc)

        if doc["status"] != "waiting":
            raise MultiplayerError("This game is no longer accepting players.", 409)

        for p in doc["players"]:
            if p["user_id"] == user_id:
                return doc, None

        existing = await self.repo.find_active_by_user(user_id)
        if existing and str(existing["_id"]) != game_id:
            raise MultiplayerError("You already have an active multiplayer game.")

        player = MultiplayerPlayerEntity(
            user_id=user_id,
            name=name,
            avatar_url=avatar_url,
            joined_at=datetime.now(UTC),
        )

        joined = await self.repo.add_player_if_waiting_and_not_full(
            game_id,
            player,
            MAX_PLAYERS,
        )

        if not joined:
            fresh = await self._reload(game_id)
            if fresh["status"] != "waiting":
                raise MultiplayerError("This game is no longer accepting players.", 409)

            for p in fresh["players"]:
                if p["user_id"] == user_id:
                    return fresh, None

            if len(fresh["players"]) >= MAX_PLAYERS:
                raise MultiplayerError("Game is full.", 409)

            raise MultiplayerError("Unable to join game. Please try again.", 409)

        logger.info("player_joined_multiplayer", game_id=game_id, user_id=user_id)

        return await self._reload(game_id), player

    async def get_game(self, game_id: str, user_id: str) -> dict:
        doc = await self.repo.find_by_id(game_id)
        if not doc:
            raise MultiplayerError("Game not found.", 404)

        doc["_id"] = str(doc["_id"])

        is_participant = any(p["user_id"] == user_id for p in doc["players"])
        if not is_participant:
            raise MultiplayerError("Game not found.", 404)

        if doc["status"] == "waiting":
            await self._check_lobby_expiry(doc)

        return doc

    async def get_active_game(self, user_id: str) -> dict | None:
        doc = await self.repo.find_active_by_user(user_id)
        if not doc:
            return None
        doc["_id"] = str(doc["_id"])
        if doc["status"] == "waiting":
            await self._check_lobby_expiry(doc)
            if doc["status"] != "waiting":
                return None
        return doc

    async def extend_lobby(self, game_id: str, host_id: str) -> None:
        doc = await self.repo.find_by_id(game_id)
        if not doc:
            raise MultiplayerError("Game not found.", 404)

        doc["_id"] = str(doc["_id"])

        if doc["host_id"] != host_id:
            raise MultiplayerError("Only the host can extend the lobby.", 403)
        if doc["status"] != "waiting":
            raise MultiplayerError("Game is not in lobby phase.", 409)
        if doc.get("lobby_extensions", 0) >= MAX_LOBBY_EXTENSIONS:
            raise MultiplayerError("Maximum lobby extensions reached.", 409)

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

    async def _generate_invite_code(self) -> str:
        for _ in range(10):
            code = "".join(
                secrets.choice(INVITE_CODE_CHARS) for _ in range(INVITE_CODE_LENGTH)
            )
            existing = await self.repo.find_by_invite_code(code)
            if not existing:
                return code
        raise MultiplayerError("Failed to generate unique invite code. Try again.")

    async def _reload(self, game_id: str) -> dict:
        doc = await self.repo.find_by_id(game_id)
        if not doc:
            raise MultiplayerError("Game not found.", 404)
        doc["_id"] = str(doc["_id"])
        return doc

    async def _check_lobby_expiry(self, doc: dict) -> None:
        if doc["status"] != "waiting":
            return

        lobby_key = f"mp:lobby:{doc['invite_code']}"
        ttl = await self.redis.ttl(lobby_key)

        # Key expired or doesn't exist — lobby has expired
        if ttl < 0:
            await self.repo.update_game(doc["_id"], {"status": "cancelled"})
            doc["status"] = "cancelled"
            logger.info("lobby_expired", game_id=doc["_id"])
