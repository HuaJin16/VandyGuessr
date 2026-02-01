"""MongoDB database connection management."""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config import get_settings

# Global database client and database instances
_client: AsyncIOMotorClient | None = None
_database: AsyncIOMotorDatabase | None = None


async def connect_to_mongo() -> None:
    """Connect to MongoDB."""
    global _client, _database
    settings = get_settings()

    _client = AsyncIOMotorClient(settings.mongodb_url)
    _database = _client[settings.mongodb_database]

    # Verify connection
    await _client.admin.command("ping")
    print(f"Connected to MongoDB: {settings.mongodb_database}")


async def close_mongo_connection() -> None:
    """Close MongoDB connection."""
    global _client, _database
    if _client:
        _client.close()
        _client = None
        _database = None
        print("Closed MongoDB connection")


def get_database() -> AsyncIOMotorDatabase:
    """Get the database instance.

    Returns:
        The MongoDB database instance.

    Raises:
        RuntimeError: If database is not connected.
    """
    if _database is None:
        raise RuntimeError("Database not connected. Call connect_to_mongo() first.")
    return _database


def get_collection(name: str):
    """Get a collection from the database.

    Args:
        name: The name of the collection.

    Returns:
        The MongoDB collection.
    """
    return get_database()[name]
