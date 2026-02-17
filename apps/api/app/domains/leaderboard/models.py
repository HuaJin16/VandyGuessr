"""Leaderboard API models."""

from pydantic import BaseModel


class LeaderboardEntry(BaseModel):
    """Represents a single leaderboard row."""

    rank: int
    userId: str
    name: str
    username: str
    totalPoints: int
    avgScore: float
    gamesPlayed: int


class LeaderboardResponse(BaseModel):
    """Leaderboard response payload."""

    entries: list[LeaderboardEntry]
    userEntry: LeaderboardEntry | None
    contextEntries: list[LeaderboardEntry]
    totalCount: int
