"""Image API models for request/response schemas."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.domains.games.models import RoundTilesResponse


class ImageUploadResult(BaseModel):
    """Result for a single image upload."""

    success: bool
    filename: str | None = None
    id: str | None = None
    url: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    error: str | None = None


class ImageResponse(BaseModel):
    """Image response for API."""

    id: str
    url: str
    latitude: float
    longitude: float
    environment: Literal["indoor", "outdoor"]


class PendingSubmissionItem(BaseModel):
    id: str
    url: str
    latitude: float
    longitude: float
    environment: Literal["indoor", "outdoor"]
    location_name: str | None = None
    original_filename: str | None = None
    created_at: datetime
    submitter_name: str | None = None
    submitter_email: str | None = None


class PendingSubmissionsResponse(BaseModel):
    items: list[PendingSubmissionItem]


class TourImageItem(BaseModel):
    id: str
    url: str
    thumbnail_url: str
    latitude: float
    longitude: float
    environment: Literal["indoor", "outdoor"]
    location_name: str | None = None
    created_at: datetime | None = None
    tiles: RoundTilesResponse | None = None


class TourImagesResponse(BaseModel):
    items: list[TourImageItem]
