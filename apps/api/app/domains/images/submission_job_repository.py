"""MongoDB repository for queued image submission jobs."""

from datetime import UTC, datetime
from typing import Protocol

from bson import ObjectId
from bson.errors import InvalidId
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ReturnDocument

from app.domains.images.submission_job_entities import ImageSubmissionJobEntity


class IImageSubmissionJobRepository(Protocol):
    async def ensure_indexes(self) -> None: ...

    async def create(self, job: ImageSubmissionJobEntity) -> str: ...

    async def find_by_id(self, job_id: str) -> dict | None: ...

    async def find_by_temp_key(self, temp_key: str) -> dict | None: ...

    async def mark_processing(self, job_id: str) -> bool: ...

    async def mark_queued(self, job_id: str, error: str) -> bool: ...

    async def mark_completed(
        self, job_id: str, image_id: str, image_url: str
    ) -> bool: ...

    async def mark_failed(self, job_id: str, error: str) -> bool: ...

    async def increment_attempts(self, job_id: str) -> int | None: ...


class ImageSubmissionJobRepository:
    """Repository for image_submission_jobs collection."""

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.collection = db.image_submission_jobs

    @staticmethod
    def _object_id(job_id: str) -> ObjectId | None:
        try:
            return ObjectId(job_id)
        except (InvalidId, TypeError):
            return None

    async def ensure_indexes(self) -> None:
        await self.collection.create_index([("status", 1), ("created_at", 1)])
        await self.collection.create_index(
            [("submitted_by_user_id", 1), ("created_at", -1)]
        )
        await self.collection.create_index([("temp_key", 1)])

    async def create(self, job: ImageSubmissionJobEntity) -> str:
        result = await self.collection.insert_one(
            job.model_dump(by_alias=True, exclude={"id"})
        )
        return str(result.inserted_id)

    async def find_by_id(self, job_id: str) -> dict | None:
        object_id = self._object_id(job_id)
        if object_id is None:
            return None
        return await self.collection.find_one({"_id": object_id})

    async def find_by_temp_key(self, temp_key: str) -> dict | None:
        return await self.collection.find_one({"temp_key": temp_key})

    async def mark_processing(self, job_id: str) -> bool:
        object_id = self._object_id(job_id)
        if object_id is None:
            return False
        now = datetime.now(UTC)
        result = await self.collection.update_one(
            {"_id": object_id, "status": "queued"},
            {
                "$set": {
                    "status": "processing",
                    "started_at": now,
                    "updated_at": now,
                    "error": None,
                }
            },
        )
        return result.modified_count > 0

    async def mark_queued(self, job_id: str, error: str) -> bool:
        object_id = self._object_id(job_id)
        if object_id is None:
            return False
        now = datetime.now(UTC)
        result = await self.collection.update_one(
            {"_id": object_id},
            {
                "$set": {
                    "status": "queued",
                    "error": error,
                    "updated_at": now,
                }
            },
        )
        return result.modified_count > 0

    async def mark_completed(self, job_id: str, image_id: str, image_url: str) -> bool:
        object_id = self._object_id(job_id)
        if object_id is None:
            return False
        now = datetime.now(UTC)
        result = await self.collection.update_one(
            {"_id": object_id},
            {
                "$set": {
                    "status": "completed",
                    "image_id": image_id,
                    "image_url": image_url,
                    "error": None,
                    "completed_at": now,
                    "updated_at": now,
                }
            },
        )
        return result.modified_count > 0

    async def mark_failed(self, job_id: str, error: str) -> bool:
        object_id = self._object_id(job_id)
        if object_id is None:
            return False
        now = datetime.now(UTC)
        result = await self.collection.update_one(
            {"_id": object_id},
            {
                "$set": {
                    "status": "failed",
                    "error": error,
                    "completed_at": now,
                    "updated_at": now,
                }
            },
        )
        return result.modified_count > 0

    async def increment_attempts(self, job_id: str) -> int | None:
        object_id = self._object_id(job_id)
        if object_id is None:
            return None
        now = datetime.now(UTC)
        result = await self.collection.find_one_and_update(
            {"_id": object_id},
            {"$inc": {"attempts": 1}, "$set": {"updated_at": now}},
            return_document=ReturnDocument.AFTER,
        )
        if not result:
            return None
        attempts = result.get("attempts")
        return attempts if isinstance(attempts, int) else None
