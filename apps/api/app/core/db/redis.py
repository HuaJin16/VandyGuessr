"""Redis connection management."""

import redis.asyncio as redis
import structlog

from app.config import get_settings

logger = structlog.get_logger()

# Global Redis client
_redis_client: redis.Redis | None = None


async def connect_to_redis() -> None:
    """Connect to Redis."""
    global _redis_client
    settings = get_settings()

    _redis_client = redis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True,
    )

    # Verify connection
    await _redis_client.ping()
    logger.info("redis_connected", url=settings.redis_url)


async def close_redis_connection() -> None:
    """Close Redis connection."""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
        logger.info("redis_disconnected")


def get_redis() -> redis.Redis:
    """Get the Redis client instance.

    Returns:
        The Redis client.

    Raises:
        RuntimeError: If Redis is not connected.
    """
    if _redis_client is None:
        raise RuntimeError("Redis not connected. Call connect_to_redis() first.")
    return _redis_client
