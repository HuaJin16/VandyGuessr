"""Multiplayer API models for request/response schemas."""

from typing import Literal

from pydantic import BaseModel


class CreateMultiplayerRequest(BaseModel):
    environment: Literal["indoor", "outdoor", "any"] = "any"


class JoinMultiplayerRequest(BaseModel):
    code: str


class MultiplayerPlayerResponse(BaseModel):
    userId: str
    name: str
    avatarUrl: str | None = None
    totalScore: int = 0
    status: str = "connected"
    joinedAt: str


class MultiplayerGuessResponse(BaseModel):
    lat: float
    lng: float
    distanceMeters: float
    score: int
    submittedAt: str


class MultiplayerRoundResponse(BaseModel):
    roundId: int
    imageUrl: str | None = None
    actual: dict | None = None
    locationName: str | None = None
    startedAt: str | None = None
    expiresAt: str | None = None
    guesses: dict[str, MultiplayerGuessResponse] | None = None


class MultiplayerGameResponse(BaseModel):
    id: str
    hostId: str
    inviteCode: str
    status: str
    mode: dict
    players: list[MultiplayerPlayerResponse]
    rounds: list[MultiplayerRoundResponse]
    currentRound: int
    createdAt: str
    startedAt: str | None = None
    lastActivityAt: str
