"""Background worker for queued image submissions."""

from __future__ import annotations

import asyncio

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

    logger.info("image_submission_worker_started", queue_key=settings.upload_queue_key)

    try:
        while True:
            payload = await service.redis.blpop(settings.upload_queue_key, timeout=5)
            if payload is None:
                continue
            _, raw_job_id = payload
            job_id = (
                raw_job_id.decode("utf-8")
                if isinstance(raw_job_id, bytes)
                else str(raw_job_id)
            )
            if not job_id:
                continue
            await service.process_job(job_id)
    finally:
        await close_mongo_connection()
        await close_redis_connection()
        logger.info("image_submission_worker_stopped")


def main() -> None:
    asyncio.run(run_worker())


if __name__ == "__main__":
    main()
