"""Image repository for database operations."""

from typing import Protocol

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.domains.images.entities import ImageEntity


class IImageRepository(Protocol):
    """Protocol defining the image repository interface."""

    async def create(self, image: ImageEntity) -> str: ...

    async def sample_random(
        self, count: int, environment: str | None = None
    ) -> list[dict]: ...

    async def find_all_ids(self, environment: str | None = None) -> list[str]: ...

    async def find_by_ids(self, image_ids: list[str]) -> list[dict]: ...


class ImageRepository:
    """MongoDB implementation of the image repository."""

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.collection = db.images

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
        if environment and environment != "any":
            pipeline.append({"$match": {"environment": environment}})
        pipeline.append({"$sample": {"size": count}})
        return await self.collection.aggregate(pipeline).to_list(length=count)

    async def find_all_ids(self, environment: str | None = None) -> list[str]:
        """Return all image _id values, optionally filtered by environment."""
        query: dict = {}
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
