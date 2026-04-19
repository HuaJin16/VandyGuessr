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

    async def claim_next_queued(
        self,
        *,
        worker_id: str,
        lease_expires_at: datetime,
    ) -> dict | None: ...

    async def claim_stale_processing(
        self,
        *,
        worker_id: str,
        lease_expires_at: datetime,
        stale_before: datetime,
    ) -> dict | None: ...

    async def renew_lease(
        self,
        job_id: str,
        *,
        worker_id: str,
        lease_expires_at: datetime,
        processing_stage: str | None = None,
    ) -> bool: ...

    async def mark_queued(self, job_id: str, error: str) -> bool: ...

    async def mark_completed(
        self,
        job_id: str,
        *,
        worker_id: str,
        image_id: str,
        image_url: str,
    ) -> bool: ...

    async def mark_failed(
        self,
        job_id: str,
        *,
        worker_id: str,
        error: str,
    ) -> bool: ...


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

    @staticmethod
    def _claim_update(
        *,
        worker_id: str,
        now: datetime,
        lease_expires_at: datetime,
    ) -> dict:
        return {
            "$set": {
                "status": "processing",
                "claimed_by": worker_id,
                "lease_expires_at": lease_expires_at,
                "heartbeat_at": now,
                "started_at": now,
                "updated_at": now,
                "error": None,
                "processing_stage": "claimed",
            },
            "$inc": {"attempts": 1},
        }

    async def ensure_indexes(self) -> None:
        await self.collection.create_index(
            [("status", 1), ("lease_expires_at", 1), ("created_at", 1)]
        )
        await self.collection.create_index(
            [("submitted_by_user_id", 1), ("created_at", -1)]
        )
        await self.collection.create_index([("temp_key", 1)])
        await self.collection.create_index([("asset_id", 1)])

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

    async def claim_next_queued(
        self,
        *,
        worker_id: str,
        lease_expires_at: datetime,
    ) -> dict | None:
        now = datetime.now(UTC)
        return await self.collection.find_one_and_update(
            {"status": "queued"},
            self._claim_update(
                worker_id=worker_id,
                now=now,
                lease_expires_at=lease_expires_at,
            ),
            sort=[("created_at", 1)],
            return_document=ReturnDocument.AFTER,
        )

    async def claim_stale_processing(
        self,
        *,
        worker_id: str,
        lease_expires_at: datetime,
        stale_before: datetime,
    ) -> dict | None:
        now = datetime.now(UTC)
        stale_filter = {
            "status": "processing",
            "$or": [
                {"lease_expires_at": {"$lte": now}},
                {
                    "lease_expires_at": {"$exists": False},
                    "updated_at": {"$lte": stale_before},
                },
                {
                    "lease_expires_at": None,
                    "updated_at": {"$lte": stale_before},
                },
            ],
        }
        return await self.collection.find_one_and_update(
            stale_filter,
            self._claim_update(
                worker_id=worker_id,
                now=now,
                lease_expires_at=lease_expires_at,
            ),
            sort=[("updated_at", 1), ("created_at", 1)],
            return_document=ReturnDocument.AFTER,
        )

    async def renew_lease(
        self,
        job_id: str,
        *,
        worker_id: str,
        lease_expires_at: datetime,
        processing_stage: str | None = None,
    ) -> bool:
        object_id = self._object_id(job_id)
        if object_id is None:
            return False
        now = datetime.now(UTC)
        set_doc: dict[str, object] = {
            "lease_expires_at": lease_expires_at,
            "heartbeat_at": now,
            "updated_at": now,
        }
        if processing_stage is not None:
            set_doc["processing_stage"] = processing_stage
        result = await self.collection.update_one(
            {
                "_id": object_id,
                "status": "processing",
                "claimed_by": worker_id,
            },
            {"$set": set_doc},
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
                    "processing_stage": None,
                    "claimed_by": None,
                    "lease_expires_at": None,
                    "heartbeat_at": None,
                    "updated_at": now,
                }
            },
        )
        return result.modified_count > 0

    async def mark_completed(
        self,
        job_id: str,
        *,
        worker_id: str,
        image_id: str,
        image_url: str,
    ) -> bool:
        object_id = self._object_id(job_id)
        if object_id is None:
            return False
        now = datetime.now(UTC)
        result = await self.collection.update_one(
            {
                "_id": object_id,
                "status": "processing",
                "claimed_by": worker_id,
            },
            {
                "$set": {
                    "status": "completed",
                    "image_id": image_id,
                    "image_url": image_url,
                    "error": None,
                    "processing_stage": "completed",
                    "completed_at": now,
                    "heartbeat_at": now,
                    "updated_at": now,
                    "claimed_by": None,
                    "lease_expires_at": None,
                }
            },
        )
        return result.modified_count > 0

    async def mark_failed(
        self,
        job_id: str,
        *,
        worker_id: str,
        error: str,
    ) -> bool:
        object_id = self._object_id(job_id)
        if object_id is None:
            return False
        now = datetime.now(UTC)
        result = await self.collection.update_one(
            {
                "_id": object_id,
                "status": "processing",
                "claimed_by": worker_id,
            },
            {
                "$set": {
                    "status": "failed",
                    "error": error,
                    "processing_stage": "failed",
                    "completed_at": now,
                    "heartbeat_at": now,
                    "updated_at": now,
                    "claimed_by": None,
                    "lease_expires_at": None,
                }
            },
        )
        return result.modified_count > 0
