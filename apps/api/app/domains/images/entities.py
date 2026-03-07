"""Image entity for MongoDB documents."""

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field


class ImageEntity(BaseModel):
    """Represents an image document in MongoDB."""

    id: str | None = Field(default=None, alias="_id")
    url: str
    latitude: float
    longitude: float
    altitude: float | None = None
    timestamp: datetime | None = None
    width: int | None = None
    height: int | None = None
    format: str | None = None
    environment: Literal["indoor", "outdoor"]
    original_filename: str | None = None
    file_size: int
    location_name: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    model_config = {"populate_by_name": True}
