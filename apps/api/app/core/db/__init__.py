"""Database client providers."""

from app.core.db.mongo import (
    close_mongo_connection,
    connect_to_mongo,
    get_database,
)
from app.core.db.redis import (
    close_redis_connection,
    connect_to_redis,
    get_redis,
)

__all__ = [
    "connect_to_mongo",
    "close_mongo_connection",
    "get_database",
    "connect_to_redis",
    "close_redis_connection",
    "get_redis",
]
