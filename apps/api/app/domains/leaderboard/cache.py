"""Shared leaderboard cache invalidation helpers."""

import redis.asyncio as redis
import structlog

logger = structlog.get_logger()

LEADERBOARD_CACHE_PREFIX = "lb:v4:*"
DELETE_BATCH_SIZE = 200


async def invalidate_leaderboard_cache(redis_client: redis.Redis) -> None:
    keys: list[str] = []

    try:
        async for key in redis_client.scan_iter(match=LEADERBOARD_CACHE_PREFIX):
            if isinstance(key, bytes):
                keys.append(key.decode())
            else:
                keys.append(str(key))

            if len(keys) >= DELETE_BATCH_SIZE:
                await redis_client.delete(*keys)
                keys.clear()

        if keys:
            await redis_client.delete(*keys)
    except Exception as exc:
        logger.warning("leaderboard_cache_invalidation_failed", error=str(exc))
