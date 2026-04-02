"""Queue-backed image submission orchestration."""

from __future__ import annotations

import uuid
from typing import Literal

import redis.asyncio as redis
import structlog

from app.config import get_settings
from app.domains.images.service import ImageService, ImageUploadError
from app.domains.images.submission_job_entities import ImageSubmissionJobEntity
from app.domains.images.submission_job_models import (
    SubmissionJobAcceptedResponse,
    SubmissionJobStatusResponse,
)
from app.domains.images.submission_job_repository import IImageSubmissionJobRepository
from app.shared.exif import extract_metadata
from app.shared.s3 import delete_object, download_bytes, upload_bytes

logger = structlog.get_logger()


class SubmissionJobService:
    """Handles enqueueing and processing upload submissions."""

    def __init__(
        self,
        image_service: ImageService,
        job_repository: IImageSubmissionJobRepository,
        redis_client: redis.Redis,
    ) -> None:
        self.image_service = image_service
        self.job_repository = job_repository
        self.redis = redis_client

    async def enqueue_submission(
        self,
        *,
        file_bytes: bytes,
        filename: str | None,
        content_type: str | None,
        environment: Literal["indoor", "outdoor"],
        moderation_status: Literal["approved", "pending"],
        submitted_by_user_id: str | None,
    ) -> SubmissionJobAcceptedResponse:
        settings = get_settings()
        self.image_service._validate_file(filename, content_type, len(file_bytes))

        metadata = extract_metadata(file_bytes)
        self.image_service._validate_image_geometry(
            metadata.get("width"), metadata.get("height")
        )
        if metadata.get("latitude") is None or metadata.get("longitude") is None:
            raise ImageUploadError("Image is missing GPS EXIF data")

        temp_key = f"{settings.upload_temp_prefix}/{uuid.uuid4()}.bin"
        await upload_bytes(temp_key, file_bytes, content_type, public=False)

        job = ImageSubmissionJobEntity(
            filename=filename,
            content_type=content_type,
            file_size=len(file_bytes),
            environment=environment,
            moderation_status=moderation_status,
            submitted_by_user_id=submitted_by_user_id,
            temp_key=temp_key,
            status="queued",
        )
        job_id = await self.job_repository.create(job)
        await self.redis.rpush(settings.upload_queue_key, job_id)
        logger.info(
            "submission_job_enqueued",
            job_id=job_id,
            filename=filename,
            moderation_status=moderation_status,
            environment=environment,
        )
        return SubmissionJobAcceptedResponse(jobId=job_id, status="queued")

    async def get_job_status(
        self,
        *,
        job_id: str,
        requester_oid: str | None,
        require_owner: bool,
    ) -> SubmissionJobStatusResponse | None:
        doc = await self.job_repository.find_by_id(job_id)
        if not doc:
            return None
        if require_owner and doc.get("submitted_by_user_id") != requester_oid:
            return None
        return SubmissionJobStatusResponse(
            jobId=str(doc["_id"]),
            status=doc["status"],
            filename=doc.get("filename"),
            environment=doc["environment"],
            error=doc.get("error"),
            imageId=doc.get("image_id"),
            imageUrl=doc.get("image_url"),
            createdAt=doc["created_at"],
            startedAt=doc.get("started_at"),
            completedAt=doc.get("completed_at"),
        )

    async def process_job(self, job_id: str) -> bool:
        settings = get_settings()
        doc = await self.job_repository.find_by_id(job_id)
        if not doc:
            logger.warning("submission_job_missing", job_id=job_id)
            return True
        status = doc.get("status")
        if status not in {"queued", "processing"}:
            logger.info("submission_job_skipped", job_id=job_id, status=status)
            return True

        attempts = await self.job_repository.increment_attempts(job_id)
        if attempts is None:
            logger.warning("submission_job_attempt_increment_failed", job_id=job_id)
            return True

        if not await self.job_repository.mark_processing(job_id):
            logger.info("submission_job_processing_lock_miss", job_id=job_id)
            return True
        temp_key = doc.get("temp_key")
        if not isinstance(temp_key, str) or not temp_key:
            await self.job_repository.mark_failed(
                job_id, "Missing temporary object key"
            )
            return True

        try:
            file_bytes = await download_bytes(temp_key)
            result = await self.image_service.upload_image(
                file_bytes=file_bytes,
                filename=doc.get("filename"),
                content_type=doc.get("content_type"),
                environment=doc["environment"],
                moderation_status=doc["moderation_status"],
                submitted_by_user_id=doc.get("submitted_by_user_id"),
            )
            if result.success and result.id and result.url:
                await self.job_repository.mark_completed(job_id, result.id, result.url)
                await delete_object(temp_key)
                logger.info(
                    "submission_job_completed", job_id=job_id, image_id=result.id
                )
                return True

            error = result.error or "Upload failed"
            if attempts < settings.upload_queue_max_attempts:
                await self.job_repository.mark_queued(job_id, error)
                await self.redis.rpush(settings.upload_queue_key, job_id)
                logger.warning(
                    "submission_job_requeued",
                    job_id=job_id,
                    attempts=attempts,
                    max_attempts=settings.upload_queue_max_attempts,
                    error=error,
                )
                return False

            await self.job_repository.mark_failed(job_id, error)
            await delete_object(temp_key)
            logger.warning(
                "submission_job_failed",
                job_id=job_id,
                attempts=attempts,
                error=error,
            )
            return True
        except Exception as exc:
            error = str(exc) or "Unexpected worker error"
            if attempts < settings.upload_queue_max_attempts:
                await self.job_repository.mark_queued(job_id, error)
                await self.redis.rpush(settings.upload_queue_key, job_id)
                logger.warning(
                    "submission_job_exception_requeued",
                    job_id=job_id,
                    attempts=attempts,
                    max_attempts=settings.upload_queue_max_attempts,
                    error=error,
                )
                return False

            await self.job_repository.mark_failed(job_id, error)
            await delete_object(temp_key)
            logger.error(
                "submission_job_exception_failed",
                job_id=job_id,
                attempts=attempts,
                error=error,
            )
            return True

    async def get_job_status_by_code(
        self,
        *,
        job_id: str,
    ) -> SubmissionJobStatusResponse | None:
        return await self.get_job_status(
            job_id=job_id,
            requester_oid=None,
            require_owner=False,
        )
