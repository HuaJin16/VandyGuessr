"""Image repository for database operations."""

from typing import Protocol

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.domains.images.entities import ImageEntity

# Legacy documents may omit moderation_status; treat as playable (same as approved).
PLAYABLE_MATCH = {"moderation_status": {"$nin": ["pending", "rejected"]}}


class IImageRepository(Protocol):
    """Protocol defining the image repository interface."""

    async def create(self, image: ImageEntity) -> str: ...

    async def sample_random(
        self, count: int, environment: str | None = None
    ) -> list[dict]: ...

    async def find_all_ids(self, environment: str | None = None) -> list[str]: ...

    async def find_by_ids(self, image_ids: list[str]) -> list[dict]: ...

    async def find_pending_moderation(self, limit: int, skip: int) -> list[dict]: ...

    async def find_by_id(self, image_id: str) -> dict | None: ...

    async def update_moderation(
        self,
        image_id: str,
        *,
        moderation_status: str,
        reviewed_by_user_id: str,
    ) -> bool: ...


class ImageRepository:
    """MongoDB implementation of the image repository."""

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.collection = db.images

    async def ensure_indexes(self) -> None:
        await self.collection.create_index(
            [("moderation_status", 1), ("created_at", -1)]
        )

    async def create(self, image: ImageEntity) -> str:
        result = await self.collection.insert_one(
            image.model_dump(by_alias=True, exclude={"id"})
        )
        return str(result.inserted_id)

    async def sample_random(
        self, count: int, environment: str | None = None
    ) -> list[dict]:
        """Return `count` random image documents using $sample."""
        pipeline: list[dict] = []
        match_query: dict = dict(PLAYABLE_MATCH)
        if environment and environment != "any":
            match_query["environment"] = environment
        pipeline.append({"$match": match_query})
        pipeline.append({"$sample": {"size": count}})
        return await self.collection.aggregate(pipeline).to_list(length=count)

    async def find_all_ids(self, environment: str | None = None) -> list[str]:
        """Return all image _id values, optionally filtered by environment."""
        query: dict = dict(PLAYABLE_MATCH)
        if environment and environment != "any":
            query["environment"] = environment
        cursor = self.collection.find(query, {"_id": 1})
        docs = await cursor.to_list(length=None)
        return [str(doc["_id"]) for doc in docs]

    async def find_by_ids(self, image_ids: list[str]) -> list[dict]:
        """Return image documents matching the given IDs."""
        from bson import ObjectId

        oids = [ObjectId(iid) for iid in image_ids]
        cursor = self.collection.find({"_id": {"$in": oids}})
        return await cursor.to_list(length=len(image_ids))

    async def find_pending_moderation(self, limit: int, skip: int) -> list[dict]:
        cursor = (
            self.collection.find({"moderation_status": "pending"})
            .sort("created_at", -1)
            .skip(skip)
            .limit(limit)
        )
        return await cursor.to_list(length=limit)

    async def find_by_id(self, image_id: str) -> dict | None:
        from bson import ObjectId

        return await self.collection.find_one({"_id": ObjectId(image_id)})

    async def update_moderation(
        self,
        image_id: str,
        *,
        moderation_status: str,
        reviewed_by_user_id: str,
    ) -> bool:
        from datetime import UTC, datetime

        from bson import ObjectId

        if moderation_status not in ("approved", "rejected"):
            return False
        result = await self.collection.update_one(
            {"_id": ObjectId(image_id), "moderation_status": "pending"},
            {
                "$set": {
                    "moderation_status": moderation_status,
                    "reviewed_by_user_id": reviewed_by_user_id,
                    "reviewed_at": datetime.now(UTC),
                }
            },
        )
        return result.modified_count > 0
