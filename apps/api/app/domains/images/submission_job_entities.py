"""Queue-backed image submission job entities."""

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field

ImageSubmissionJobStatus = Literal["queued", "processing", "completed", "failed"]


class ImageSubmissionJobEntity(BaseModel):
    """Represents a queued image processing task in MongoDB."""

    id: str | None = Field(default=None, alias="_id")
    filename: str | None = None
    content_type: str | None = None
    file_size: int
    environment: Literal["indoor", "outdoor"]
    moderation_status: Literal["approved", "pending"]
    submitted_by_user_id: str | None = None
    temp_key: str
    status: ImageSubmissionJobStatus = "queued"
    attempts: int = 0
    image_id: str | None = None
    image_url: str | None = None
    error: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    started_at: datetime | None = None
    completed_at: datetime | None = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    model_config = {"populate_by_name": True}
