"""Background worker for queued image submissions."""

from __future__ import annotations

import asyncio
import uuid

import structlog

from app.config import get_settings
from app.container import container
from app.core.db import (
    close_mongo_connection,
    close_redis_connection,
    connect_to_mongo,
    connect_to_redis,
)
from app.domains.images.submission_job_service import SubmissionJobService

logger = structlog.get_logger()


async def run_worker() -> None:
    settings = get_settings()
    await connect_to_mongo()
    await connect_to_redis()
    service = container.resolve(SubmissionJobService)
    worker_id = f"image-worker-{uuid.uuid4()}"

    logger.info(
        "image_submission_worker_started",
        queue_key=settings.upload_queue_key,
        worker_id=worker_id,
    )

    try:
        while True:
            claimed = await service.claim_next_job(worker_id)
            if claimed is None:
                await service.wait_for_job_signal()
                continue
            try:
                await service.process_claimed_job(claimed, worker_id=worker_id)
            except Exception as exc:
                logger.exception(
                    "image_submission_worker_job_crashed",
                    worker_id=worker_id,
                    job_id=str(claimed.get("_id")),
                    error=str(exc),
                )
    finally:
        await close_mongo_connection()
        await close_redis_connection()
        logger.info("image_submission_worker_stopped", worker_id=worker_id)


def main() -> None:
    asyncio.run(run_worker())


if __name__ == "__main__":
    main()
