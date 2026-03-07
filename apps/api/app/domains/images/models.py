"""Image API models for request/response schemas."""

from typing import Literal

from pydantic import BaseModel


class ImageUploadResult(BaseModel):
    """Result for a single image upload."""

    success: bool
    filename: str | None = None
    id: str | None = None
    url: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    error: str | None = None


class ImageUploadResponse(BaseModel):
    """Response for image upload endpoint."""

    total: int
    successful: int
    failed: int
    results: list[ImageUploadResult]


class ImageResponse(BaseModel):
    """Image response for API."""

    id: str
    url: str
    latitude: float
    longitude: float
    environment: Literal["indoor", "outdoor"]
