"""Image repository for database operations."""

from typing import Protocol

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.domains.images.entities import ImageEntity


class IImageRepository(Protocol):
    """Protocol defining the image repository interface."""

    async def create(self, image: ImageEntity) -> str:
        """Create a new image and return the inserted ID."""
        ...


class ImageRepository:
    """MongoDB implementation of the image repository."""

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.collection = db.images

    async def create(self, image: ImageEntity) -> str:
        """Create a new image and return the inserted ID."""
        result = await self.collection.insert_one(
            image.model_dump(by_alias=True, exclude={"id"})
        )
        return str(result.inserted_id)
