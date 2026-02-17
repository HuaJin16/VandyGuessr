"""Multiplayer game repository for MongoDB access."""

from typing import Protocol

from bson import ObjectId
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
    async def add_player(
        self, game_id: str, player: MultiplayerPlayerEntity
    ) -> None: ...
    async def remove_player(self, game_id: str, user_id: str) -> None: ...
    async def update_player(self, game_id: str, user_id: str, update: dict) -> None: ...
    async def set_guess(
        self,
        game_id: str,
        round_index: int,
        user_id: str,
        guess: MultiplayerGuessEntity,
    ) -> None: ...
    async def update_round(
        self, game_id: str, round_index: int, update: dict
    ) -> None: ...
    async def ensure_indexes(self) -> None: ...


class MultiplayerGameRepository:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.collection = db.multiplayer_games

    async def create(self, game: MultiplayerGameEntity) -> str:
        data = game.model_dump(by_alias=True, exclude={"id"})
        result = await self.collection.insert_one(data)
        return str(result.inserted_id)

    async def find_by_id(self, game_id: str) -> dict | None:
        return await self.collection.find_one({"_id": ObjectId(game_id)})

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
        await self.collection.update_one(
            {"_id": ObjectId(game_id)},
            {"$set": update},
        )

    async def add_player(self, game_id: str, player: MultiplayerPlayerEntity) -> None:
        await self.collection.update_one(
            {"_id": ObjectId(game_id)},
            {"$push": {"players": player.model_dump()}},
        )

    async def remove_player(self, game_id: str, user_id: str) -> None:
        await self.collection.update_one(
            {"_id": ObjectId(game_id)},
            {"$pull": {"players": {"user_id": user_id}}},
        )

    async def update_player(self, game_id: str, user_id: str, update: dict) -> None:
        set_fields = {f"players.$.{k}": v for k, v in update.items()}
        await self.collection.update_one(
            {"_id": ObjectId(game_id), "players.user_id": user_id},
            {"$set": set_fields},
        )

    async def set_guess(
        self,
        game_id: str,
        round_index: int,
        user_id: str,
        guess: MultiplayerGuessEntity,
    ) -> None:
        key = f"rounds.{round_index}.guesses.{user_id}"
        await self.collection.update_one(
            {"_id": ObjectId(game_id)},
            {"$set": {key: guess.model_dump()}},
        )

    async def update_round(self, game_id: str, round_index: int, update: dict) -> None:
        set_fields = {f"rounds.{round_index}.{k}": v for k, v in update.items()}
        await self.collection.update_one(
            {"_id": ObjectId(game_id)},
            {"$set": set_fields},
        )

    async def ensure_indexes(self) -> None:
        await self.collection.create_index("invite_code", unique=True)
        await self.collection.create_index([("host_id", 1), ("status", 1)])
        await self.collection.create_index([("players.user_id", 1), ("status", 1)])
