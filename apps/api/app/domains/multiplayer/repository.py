"""Multiplayer game repository for MongoDB access."""

from datetime import UTC, datetime
from typing import Protocol

from bson import ObjectId
from bson.errors import InvalidId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.domains.multiplayer.entities import (
    MultiplayerGameEntity,
    MultiplayerGuessEntity,
    MultiplayerPlayerEntity,
)


class IMultiplayerGameRepository(Protocol):
    async def create(self, game: MultiplayerGameEntity) -> str: ...
    async def find_by_id(self, game_id: str) -> dict | None: ...
    async def find_by_invite_code(self, code: str) -> dict | None: ...
    async def find_active_by_user(self, user_id: str) -> dict | None: ...
    async def update_game(self, game_id: str, update: dict) -> None: ...
    async def update_game_if_status(
        self, game_id: str, expected_status: str, update: dict
    ) -> bool: ...
    async def add_player(
        self, game_id: str, player: MultiplayerPlayerEntity
    ) -> None: ...
    async def add_player_if_waiting_and_not_full(
        self,
        game_id: str,
        player: MultiplayerPlayerEntity,
        max_players: int,
    ) -> bool: ...
    async def remove_player(self, game_id: str, user_id: str) -> None: ...
    async def update_player(self, game_id: str, user_id: str, update: dict) -> None: ...
    async def increment_player_score(
        self, game_id: str, user_id: str, score: int
    ) -> None: ...
    async def set_guess(
        self,
        game_id: str,
        round_index: int,
        user_id: str,
        guess: MultiplayerGuessEntity,
    ) -> bool: ...
    async def mark_round_resolved(self, game_id: str, round_index: int) -> bool: ...
    async def update_round(
        self, game_id: str, round_index: int, update: dict
    ) -> None: ...
    async def ensure_indexes(self) -> None: ...


class MultiplayerGameRepository:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.collection = db.multiplayer_games

    def _object_id(self, game_id: str) -> ObjectId | None:
        try:
            return ObjectId(game_id)
        except (InvalidId, TypeError):
            return None

    async def create(self, game: MultiplayerGameEntity) -> str:
        data = game.model_dump(by_alias=True, exclude={"id"})
        result = await self.collection.insert_one(data)
        return str(result.inserted_id)

    async def find_by_id(self, game_id: str) -> dict | None:
        object_id = self._object_id(game_id)
        if object_id is None:
            return None
        return await self.collection.find_one({"_id": object_id})

    async def find_by_invite_code(self, code: str) -> dict | None:
        return await self.collection.find_one({"invite_code": code})

    async def find_active_by_user(self, user_id: str) -> dict | None:
        return await self.collection.find_one(
            {
                "players.user_id": user_id,
                "status": {"$in": ["waiting", "active"]},
            }
        )

    async def update_game(self, game_id: str, update: dict) -> None:
        object_id = self._object_id(game_id)
        if object_id is None:
            return
        await self.collection.update_one(
            {"_id": object_id},
            {"$set": update},
        )

    async def update_game_if_status(
        self, game_id: str, expected_status: str, update: dict
    ) -> bool:
        object_id = self._object_id(game_id)
        if object_id is None:
            return False
        result = await self.collection.update_one(
            {
                "_id": object_id,
                "status": expected_status,
            },
            {"$set": update},
        )
        return result.modified_count == 1

    async def add_player(self, game_id: str, player: MultiplayerPlayerEntity) -> None:
        object_id = self._object_id(game_id)
        if object_id is None:
            return
        await self.collection.update_one(
            {"_id": object_id},
            {"$push": {"players": player.model_dump()}},
        )

    async def add_player_if_waiting_and_not_full(
        self,
        game_id: str,
        player: MultiplayerPlayerEntity,
        max_players: int,
    ) -> bool:
        object_id = self._object_id(game_id)
        if object_id is None:
            return False
        now = datetime.now(UTC)
        result = await self.collection.update_one(
            {
                "_id": object_id,
                "status": "waiting",
                "players.user_id": {"$ne": player.user_id},
                f"players.{max_players - 1}": {"$exists": False},
            },
            {
                "$push": {"players": player.model_dump()},
                "$set": {"last_activity_at": now},
            },
        )
        return result.modified_count == 1

    async def remove_player(self, game_id: str, user_id: str) -> None:
        object_id = self._object_id(game_id)
        if object_id is None:
            return
        await self.collection.update_one(
            {"_id": object_id},
            {"$pull": {"players": {"user_id": user_id}}},
        )

    async def update_player(self, game_id: str, user_id: str, update: dict) -> None:
        object_id = self._object_id(game_id)
        if object_id is None:
            return
        set_fields = {f"players.$.{k}": v for k, v in update.items()}
        await self.collection.update_one(
            {"_id": object_id, "players.user_id": user_id},
            {"$set": set_fields},
        )

    async def increment_player_score(
        self, game_id: str, user_id: str, score: int
    ) -> None:
        object_id = self._object_id(game_id)
        if object_id is None:
            return
        await self.collection.update_one(
            {
                "_id": object_id,
                "players.user_id": user_id,
            },
            {
                "$inc": {"players.$.total_score": score},
            },
        )

    async def set_guess(
        self,
        game_id: str,
        round_index: int,
        user_id: str,
        guess: MultiplayerGuessEntity,
    ) -> bool:
        object_id = self._object_id(game_id)
        if object_id is None:
            return False
        key = f"rounds.{round_index}.guesses.{user_id}"
        result = await self.collection.update_one(
            {
                "_id": object_id,
                key: {"$exists": False},
            },
            {"$set": {key: guess.model_dump()}},
        )
        return result.modified_count == 1

    async def mark_round_resolved(self, game_id: str, round_index: int) -> bool:
        object_id = self._object_id(game_id)
        if object_id is None:
            return False
        key = f"rounds.{round_index}._resolved"
        result = await self.collection.update_one(
            {
                "_id": object_id,
                "status": "active",
                key: {"$ne": True},
            },
            {
                "$set": {key: True},
            },
        )
        return result.modified_count == 1

    async def update_round(self, game_id: str, round_index: int, update: dict) -> None:
        object_id = self._object_id(game_id)
        if object_id is None:
            return
        set_fields = {f"rounds.{round_index}.{k}": v for k, v in update.items()}
        await self.collection.update_one(
            {"_id": object_id},
            {"$set": set_fields},
        )

    async def ensure_indexes(self) -> None:
        await self.collection.create_index("invite_code", unique=True)
        await self.collection.create_index([("host_id", 1), ("status", 1)])
        await self.collection.create_index([("players.user_id", 1), ("status", 1)])
