"""Multiplayer game entities for MongoDB documents."""

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field


class MultiplayerModeEntity(BaseModel):
    environment: Literal["indoor", "outdoor", "any"]


class MultiplayerGuessEntity(BaseModel):
    lat: float
    lng: float
    distance_meters: float
    score: int
    submitted_at: datetime


class MultiplayerPlayerEntity(BaseModel):
    user_id: str
    name: str
    avatar_url: str | None = None
    total_score: int = 0
    status: Literal["connected", "disconnected", "forfeited"] = "connected"
    joined_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    disconnected_at: datetime | None = None


class MultiplayerRoundEntity(BaseModel):
    round_id: int
    image_id: str
    image_url: str
    actual_lat: float
    actual_lng: float
    location_name: str | None = None
    started_at: datetime | None = None
    expires_at: datetime | None = None
    guesses: dict[str, MultiplayerGuessEntity] = Field(default_factory=dict)


class MultiplayerGameEntity(BaseModel):
    id: str | None = Field(default=None, alias="_id")
    host_id: str
    invite_code: str
    status: Literal["waiting", "active", "completed", "cancelled", "abandoned"] = (
        "waiting"
    )
    mode: MultiplayerModeEntity
    players: list[MultiplayerPlayerEntity] = Field(default_factory=list)
    rounds: list[MultiplayerRoundEntity] = Field(default_factory=list)
    current_round: int = 0
    lobby_extensions: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    started_at: datetime | None = None
    last_activity_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    model_config = {"populate_by_name": True}
