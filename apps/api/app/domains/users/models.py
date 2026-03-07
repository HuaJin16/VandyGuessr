"""User API models for request/response schemas."""

from pydantic import BaseModel


class UserStatsResponse(BaseModel):
    """Stats block returned with the user profile."""

    gamesPlayed: int
    totalPoints: int
    avgScore: float
    locationsDiscovered: int
    rank: int | None = None


class UserResponse(BaseModel):
    """User profile response."""

    id: str
    email: str
    username: str
    name: str
    avatar_url: str | None
    stats: UserStatsResponse
