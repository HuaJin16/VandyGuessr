"""
Game API models for request/response schemas.
"""

from typing import Literal

from pydantic import BaseModel

from app.domains.games.difficulty import DEFAULT_DIFFICULTY, Difficulty


class GameModeRequest(BaseModel):
    """Game mode configuration from the client."""

    timed: bool
    environment: Literal["indoor", "outdoor", "any"]
    daily: bool
    difficulty: Difficulty = DEFAULT_DIFFICULTY


class GameModeResponse(BaseModel):
    """Game mode in the response."""

    timed: bool
    environment: str
    daily: bool
    difficulty: Difficulty


class StartGameRequest(BaseModel):
    """Request body for starting a new game."""

    mode: GameModeRequest


class GuessRequest(BaseModel):
    """Request body for submitting a guess."""

    lat: float
    lng: float


class RoundTileLevelResponse(BaseModel):
    level: int
    width: int
    height: int
    cols: int
    rows: int


class RoundPanoDataResponse(BaseModel):
    fullWidth: int
    fullHeight: int
    croppedWidth: int
    croppedHeight: int
    croppedX: int
    croppedY: int


class RoundTilesResponse(BaseModel):
    version: int
    baseUrl: str
    tileUrlTemplate: str
    originalWidth: int
    originalHeight: int
    aspectRatio: float
    basePanoData: RoundPanoDataResponse
    levels: list[RoundTileLevelResponse]


class RoundResponse(BaseModel):
    """Round data in the game response."""

    roundId: int
    imageId: str
    imageUrl: str
    imageTiles: RoundTilesResponse | None = None
    actual: dict | None = None  # {"lat": float, "lng": float} - only after guess
    guess: dict | None = None
    distanceMeters: float | None = None
    score: int | None = None
    startedAt: str | None = None
    expiresAt: str | None = None
    guessedAt: str | None = None
    skipped: bool = False
    location_name: str | None = None


class GameResponse(BaseModel):
    """Full game state response."""

    id: str
    userId: str
    mode: GameModeResponse
    status: str
    rounds: list[RoundResponse]
    totalScore: int
    createdAt: str
    lastActivityAt: str


class ScoreDistributionResponse(BaseModel):
    """Score distribution for a specific image location."""

    percentile: int
    histogram: list[int]
