"""Game entity for MongoDB documents."""

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field


class RoundEntity(BaseModel):
    """Represents a single round within a game document."""

    round_id: int
    image_id: str
    image_url: str
    actual_lat: float
    actual_lng: float
    guess: dict | None = None  # {"lat": float, "lng": float}
    distance_meters: float | None = None
    score: int | None = None
    started_at: datetime | None = None
    expires_at: datetime | None = None
    skipped: bool = False
    location_name: str | None = None


class GameEntity(BaseModel):
    """Represents a game document in MongoDB."""

    id: str | None = Field(default=None, alias="_id")
    user_id: str
    mode: dict  # {"timed": bool, "environment": str, "daily": bool}
    status: Literal["active", "completed", "abandoned"] = "active"
    rounds: list[RoundEntity] = Field(default_factory=list)
    total_score: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_activity_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    model_config = {"populate_by_name": True}
