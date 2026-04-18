"""Queue-backed image submission orchestration."""

from __future__ import annotations

import asyncio
import contextlib
import uuid
from datetime import UTC, datetime, timedelta
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

    @staticmethod
    def _job_id(doc: dict) -> str:
        return str(doc["_id"])

    def _lease_expires_at(self) -> datetime:
        settings = get_settings()
        return datetime.now(UTC) + timedelta(
            seconds=settings.upload_processing_lease_seconds
        )

    @staticmethod
    def _asset_id_from_job(doc: dict) -> str | None:
        asset_id = doc.get("asset_id")
        if isinstance(asset_id, str) and asset_id:
            return asset_id
        temp_key = doc.get("temp_key")
        if not isinstance(temp_key, str) or not temp_key:
            return None
        name = temp_key.rsplit("/", 1)[-1]
        stem = name.rsplit(".", 1)[0]
        return stem or None

    async def _wake_worker(self, signal: str) -> None:
        settings = get_settings()
        await self.redis.rpush(settings.upload_queue_key, signal)

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
        effective_content_type = self.image_service._validate_file(
            filename, content_type, len(file_bytes)
        )

        metadata = self.image_service.extract_upload_metadata(file_bytes)
        self.image_service._validate_image_geometry(
            metadata.get("width"), metadata.get("height")
        )
        if metadata.get("latitude") is None or metadata.get("longitude") is None:
            raise ImageUploadError("Image is missing GPS EXIF data")

        asset_id = str(uuid.uuid4())
        temp_key = f"{settings.upload_temp_prefix}/{asset_id}.bin"
        await upload_bytes(temp_key, file_bytes, effective_content_type, public=False)

        job = ImageSubmissionJobEntity(
            filename=filename,
            content_type=effective_content_type,
            file_size=len(file_bytes),
            environment=environment,
            moderation_status=moderation_status,
            submitted_by_user_id=submitted_by_user_id,
            asset_id=asset_id,
            temp_key=temp_key,
            status="queued",
        )
        job_id = await self.job_repository.create(job)
        await self._wake_worker(job_id)
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
            attempts=doc.get("attempts", 0),
            processingStage=doc.get("processing_stage"),
            imageId=doc.get("image_id"),
            imageUrl=doc.get("image_url"),
            createdAt=doc["created_at"],
            startedAt=doc.get("started_at"),
            heartbeatAt=doc.get("heartbeat_at"),
            completedAt=doc.get("completed_at"),
            updatedAt=doc["updated_at"],
        )

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

    async def claim_next_job(self, worker_id: str) -> dict | None:
        settings = get_settings()
        lease_expires_at = self._lease_expires_at()
        stale_before = datetime.now(UTC) - timedelta(
            seconds=settings.upload_processing_lease_seconds
        )

        doc = await self.job_repository.claim_stale_processing(
            worker_id=worker_id,
            lease_expires_at=lease_expires_at,
            stale_before=stale_before,
        )
        if doc:
            logger.warning(
                "submission_job_reclaimed",
                job_id=self._job_id(doc),
                worker_id=worker_id,
                attempts=doc.get("attempts", 0),
            )
            return doc

        doc = await self.job_repository.claim_next_queued(
            worker_id=worker_id,
            lease_expires_at=lease_expires_at,
        )
        if doc:
            logger.info(
                "submission_job_claimed",
                job_id=self._job_id(doc),
                worker_id=worker_id,
                attempts=doc.get("attempts", 0),
            )
        return doc

    async def wait_for_job_signal(self) -> bool:
        settings = get_settings()
        payload = await self.redis.blpop(
            settings.upload_queue_key,
            timeout=settings.upload_worker_idle_timeout_seconds,
        )
        return payload is not None

    async def _update_stage(
        self,
        job_id: str,
        *,
        worker_id: str,
        stage: str,
    ) -> None:
        renewed = await self.job_repository.renew_lease(
            job_id,
            worker_id=worker_id,
            lease_expires_at=self._lease_expires_at(),
            processing_stage=stage,
        )
        if not renewed:
            logger.warning(
                "submission_job_stage_update_missed",
                job_id=job_id,
                worker_id=worker_id,
                stage=stage,
            )

    async def _run_heartbeat(
        self,
        *,
        job_id: str,
        worker_id: str,
        stop: asyncio.Event,
    ) -> None:
        settings = get_settings()
        interval = settings.upload_processing_heartbeat_seconds
        while not stop.is_set():
            try:
                await asyncio.wait_for(stop.wait(), timeout=interval)
                break
            except TimeoutError:
                renewed = await self.job_repository.renew_lease(
                    job_id,
                    worker_id=worker_id,
                    lease_expires_at=self._lease_expires_at(),
                )
                if not renewed:
                    logger.warning(
                        "submission_job_heartbeat_stopped",
                        job_id=job_id,
                        worker_id=worker_id,
                    )
                    return

    async def process_claimed_job(self, doc: dict, *, worker_id: str) -> bool:
        settings = get_settings()
        job_id = self._job_id(doc)
        attempts = doc.get("attempts", 0)
        temp_key = doc.get("temp_key")
        asset_id = self._asset_id_from_job(doc)

        if not isinstance(temp_key, str) or not temp_key:
            await self.job_repository.mark_failed(
                job_id,
                worker_id=worker_id,
                error="Missing temporary object key",
            )
            return True
        if asset_id is None:
            await self.job_repository.mark_failed(
                job_id,
                worker_id=worker_id,
                error="Missing image asset id",
            )
            return True

        stop_heartbeat = asyncio.Event()
        heartbeat_task = asyncio.create_task(
            self._run_heartbeat(
                job_id=job_id,
                worker_id=worker_id,
                stop=stop_heartbeat,
            )
        )

        async def stage_callback(stage: str) -> None:
            await self._update_stage(job_id, worker_id=worker_id, stage=stage)

        try:
            await stage_callback("downloading_temp")
            file_bytes = await download_bytes(temp_key)
            result = await self.image_service.upload_image(
                file_bytes=file_bytes,
                filename=doc.get("filename"),
                content_type=doc.get("content_type"),
                environment=doc["environment"],
                moderation_status=doc["moderation_status"],
                submitted_by_user_id=doc.get("submitted_by_user_id"),
                asset_id=asset_id,
                progress_callback=stage_callback,
            )
            if result.success and result.id and result.url:
                await stage_callback("finalizing")
                completed = await self.job_repository.mark_completed(
                    job_id,
                    worker_id=worker_id,
                    image_id=result.id,
                    image_url=result.url,
                )
                if not completed:
                    raise RuntimeError("Failed to finalize submission job")
                with contextlib.suppress(Exception):
                    await delete_object(temp_key)
                logger.info(
                    "submission_job_completed",
                    job_id=job_id,
                    image_id=result.id,
                    worker_id=worker_id,
                )
                return True

            error = result.error or "Upload failed"
            if attempts < settings.upload_queue_max_attempts:
                await self.job_repository.mark_queued(job_id, error)
                await self._wake_worker(job_id)
                logger.warning(
                    "submission_job_requeued",
                    job_id=job_id,
                    attempts=attempts,
                    max_attempts=settings.upload_queue_max_attempts,
                    error=error,
                    worker_id=worker_id,
                )
                return False

            await self.job_repository.mark_failed(
                job_id,
                worker_id=worker_id,
                error=error,
            )
            with contextlib.suppress(Exception):
                await delete_object(temp_key)
            logger.warning(
                "submission_job_failed",
                job_id=job_id,
                attempts=attempts,
                error=error,
                worker_id=worker_id,
            )
            return True
        except Exception as exc:
            error = str(exc) or "Unexpected worker error"
            if attempts < settings.upload_queue_max_attempts:
                await self.job_repository.mark_queued(job_id, error)
                await self._wake_worker(job_id)
                logger.warning(
                    "submission_job_exception_requeued",
                    job_id=job_id,
                    attempts=attempts,
                    max_attempts=settings.upload_queue_max_attempts,
                    error=error,
                    worker_id=worker_id,
                )
                return False

            await self.job_repository.mark_failed(
                job_id,
                worker_id=worker_id,
                error=error,
            )
            with contextlib.suppress(Exception):
                await delete_object(temp_key)
            logger.error(
                "submission_job_exception_failed",
                job_id=job_id,
                attempts=attempts,
                error=error,
                worker_id=worker_id,
            )
            return True
        finally:
            stop_heartbeat.set()
            with contextlib.suppress(Exception):
                await heartbeat_task
