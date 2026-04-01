"""Response models for queued image submissions."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class SubmissionJobAcceptedResponse(BaseModel):
    """Response payload when a file is accepted into the queue."""

    jobId: str
    status: Literal["queued"]


class SubmissionJobStatusResponse(BaseModel):
    """Status view for a queued image submission job."""

    jobId: str
    status: Literal["queued", "processing", "completed", "failed"]
    filename: str | None = None
    environment: Literal["indoor", "outdoor"]
    error: str | None = None
    imageId: str | None = None
    imageUrl: str | None = None
    createdAt: datetime
    startedAt: datetime | None = None
    completedAt: datetime | None = None
