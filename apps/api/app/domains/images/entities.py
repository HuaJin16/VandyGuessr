"""Image entity for MongoDB documents."""

from datetime import datetime
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
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"populate_by_name": True}
