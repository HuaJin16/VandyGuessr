"""Image entity for MongoDB documents."""

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field

ModerationStatus = Literal["pending", "approved", "rejected"]


class ImageTileLevelEntity(BaseModel):
    """Tile grid information for one panorama level."""

    level: int
    width: int
    height: int
    cols: int
    rows: int


class ImagePanoDataEntity(BaseModel):
    """Pano crop/full geometry for the tiled viewer."""

    full_width: int
    full_height: int
    cropped_width: int
    cropped_height: int
    cropped_x: int
    cropped_y: int


class ImageTilesEntity(BaseModel):
    """Tiled panorama metadata stored with an image."""

    version: int
    base_url: str
    tile_url_template: str
    level_count: int
    original_width: int
    original_height: int
    aspect_ratio: float
    base_pano_data: ImagePanoDataEntity
    levels: list[ImageTileLevelEntity]


class ImageCompressionEntity(BaseModel):
    """Compression metadata for stored original fallback image."""

    version: int
    source_size_bytes: int
    stored_size_bytes: int
    savings_ratio: float
    quality: int
    format: str
    compressed: bool


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
    thumbnail_url: str | None = None
    thumbnail_version: int | None = None
    tiles: ImageTilesEntity | None = None
    compression: ImageCompressionEntity | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    moderation_status: ModerationStatus = "approved"
    submitted_by_user_id: str | None = None
    submitted_at: datetime | None = None
    reviewed_by_user_id: str | None = None
    reviewed_at: datetime | None = None

    model_config = {"populate_by_name": True}
