"""Game repository for database operations."""

from typing import Protocol

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.domains.games.entities import GameEntity


class IGameRepository(Protocol):
    """Protocol defining the game repository interface."""

    async def create(self, game: GameEntity) -> str: ...

    async def find_by_id(self, game_id: str) -> dict | None: ...

    async def find_active_by_user(self, user_id: str) -> dict | None: ...

    async def find_by_user(
        self,
        user_id: str,
        status: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict]: ...

    async def update_round(
        self, game_id: str, round_index: int, round_data: dict
    ) -> None: ...

    async def update_game(self, game_id: str, update: dict) -> None: ...

    async def compute_user_stats(self, user_oid: str) -> dict: ...

    async def compute_rank(self, user_oid: str, user_points: int) -> int: ...


class GameRepository:
    """MongoDB implementation of the game repository."""

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.collection = db.games

    async def create(self, game: GameEntity) -> str:
        result = await self.collection.insert_one(
            game.model_dump(by_alias=True, exclude={"id"})
        )
        return str(result.inserted_id)

    async def find_by_id(self, game_id: str) -> dict | None:
        return await self.collection.find_one({"_id": ObjectId(game_id)})

    async def find_active_by_user(self, user_id: str) -> dict | None:
        return await self.collection.find_one({"user_id": user_id, "status": "active"})

    async def find_by_user(
        self,
        user_id: str,
        status: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict]:
        query: dict = {"user_id": user_id}
        if status:
            query["status"] = status
        cursor = (
            self.collection.find(query).sort("created_at", -1).skip(offset).limit(limit)
        )
        return await cursor.to_list(length=limit)

    async def update_round(
        self, game_id: str, round_index: int, round_data: dict
    ) -> None:
        update_fields = {f"rounds.{round_index}.{k}": v for k, v in round_data.items()}
        await self.collection.update_one(
            {"_id": ObjectId(game_id)}, {"$set": update_fields}
        )

    async def update_game(self, game_id: str, update: dict) -> None:
        await self.collection.update_one({"_id": ObjectId(game_id)}, {"$set": update})

    async def compute_user_stats(self, user_oid: str) -> dict:
        """Aggregate stats for a user from all completed games."""
        pipeline = [
            {"$match": {"user_id": user_oid, "status": "completed"}},
            {
                "$facet": {
                    "game_stats": [
                        {
                            "$group": {
                                "_id": None,
                                "games_played": {"$sum": 1},
                                "total_points": {"$sum": "$total_score"},
                                "avg_score": {"$avg": "$total_score"},
                            }
                        }
                    ],
                    "locations": [
                        {"$unwind": "$rounds"},
                        {
                            "$match": {
                                "rounds.guess": {"$ne": None},
                                "rounds.skipped": {"$ne": True},
                            }
                        },
                        {
                            "$group": {
                                "_id": None,
                                "ids": {"$addToSet": "$rounds.image_id"},
                            }
                        },
                    ],
                }
            },
        ]
        results = await self.collection.aggregate(pipeline).to_list(length=1)
        if not results:
            return {
                "games_played": 0,
                "total_points": 0,
                "avg_score": 0.0,
                "locations_discovered": 0,
            }

        result = results[0]
        game_stats = result["game_stats"][0] if result["game_stats"] else {}
        location_ids = result["locations"][0]["ids"] if result["locations"] else []

        return {
            "games_played": game_stats.get("games_played", 0),
            "total_points": game_stats.get("total_points", 0),
            "avg_score": game_stats.get("avg_score", 0.0),
            "locations_discovered": len(location_ids),
        }

    async def compute_rank(self, user_oid: str, user_points: int) -> int:
        """Count users with more total points from completed games, return 1-based rank."""
        pipeline = [
            {"$match": {"status": "completed"}},
            {"$group": {"_id": "$user_id", "total": {"$sum": "$total_score"}}},
            {"$match": {"total": {"$gt": user_points}, "_id": {"$ne": user_oid}}},
            {"$count": "ahead"},
        ]
        results = await self.collection.aggregate(pipeline).to_list(length=1)
        ahead = results[0]["ahead"] if results else 0
        return ahead + 1
