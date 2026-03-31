"""Game repository for database operations."""

from typing import Protocol

from bson import ObjectId
from bson.errors import InvalidId
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

    async def compute_score_distribution(
        self, image_id: str, score: int, bucket_count: int = 20
    ) -> dict: ...


class GameRepository:
    """MongoDB implementation of the game repository."""

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.collection = db.games

    @staticmethod
    def _object_id(game_id: str) -> ObjectId | None:
        try:
            return ObjectId(game_id)
        except (InvalidId, TypeError):
            return None

    async def ensure_indexes(self) -> None:
        await self.collection.create_index([("user_id", 1), ("status", 1)])
        await self.collection.create_index([("user_id", 1), ("created_at", -1)])
        await self.collection.create_index([("status", 1), ("created_at", -1)])
        await self.collection.create_index([("status", 1), ("rounds.image_id", 1)])

    async def create(self, game: GameEntity) -> str:
        result = await self.collection.insert_one(
            game.model_dump(by_alias=True, exclude={"id"})
        )
        return str(result.inserted_id)

    async def find_by_id(self, game_id: str) -> dict | None:
        object_id = self._object_id(game_id)
        if object_id is None:
            return None
        return await self.collection.find_one({"_id": object_id})

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
        object_id = self._object_id(game_id)
        if object_id is None:
            return
        update_fields = {f"rounds.{round_index}.{k}": v for k, v in round_data.items()}
        await self.collection.update_one({"_id": object_id}, {"$set": update_fields})

    async def update_game(self, game_id: str, update: dict) -> None:
        object_id = self._object_id(game_id)
        if object_id is None:
            return
        await self.collection.update_one({"_id": object_id}, {"$set": update})

    async def compute_score_distribution(
        self, image_id: str, score: int, bucket_count: int = 20
    ) -> dict:
        """Compute score distribution for a specific image.

        Returns percentile for the given score and a histogram with
        ``bucket_count`` buckets spanning 0-5000.
        """
        bucket_size = 5000 / bucket_count

        pipeline = [
            {"$match": {"status": "completed"}},
            {"$unwind": "$rounds"},
            {
                "$match": {
                    "rounds.image_id": image_id,
                    "rounds.guess": {"$ne": None},
                    "rounds.skipped": {"$ne": True},
                }
            },
            {
                "$facet": {
                    "total": [{"$count": "n"}],
                    "below": [
                        {"$match": {"rounds.score": {"$lt": score}}},
                        {"$count": "n"},
                    ],
                    "histogram": [
                        {
                            "$bucket": {
                                "groupBy": "$rounds.score",
                                "boundaries": [
                                    int(i * bucket_size) for i in range(bucket_count)
                                ]
                                + [5001],
                                "default": "_other",
                                "output": {"count": {"$sum": 1}},
                            }
                        }
                    ],
                }
            },
        ]

        results = await self.collection.aggregate(pipeline).to_list(length=1)
        if not results:
            return {"percentile": 0, "histogram": [0] * bucket_count}

        data = results[0]
        total = data["total"][0]["n"] if data["total"] else 0
        below = data["below"][0]["n"] if data["below"] else 0

        percentile = round((below / total) * 100) if total > 0 else 0

        hist = [0] * bucket_count
        for bucket in data.get("histogram", []):
            bid = bucket["_id"]
            if bid == "_other":
                continue
            idx = min(int(bid / bucket_size), bucket_count - 1)
            hist[idx] = bucket["count"]

        return {"percentile": percentile, "histogram": hist}
