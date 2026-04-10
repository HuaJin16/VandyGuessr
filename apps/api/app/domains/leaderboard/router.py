"""Leaderboard endpoints."""

from typing import Literal

from fastapi import APIRouter, HTTPException, Query

from app.container import deps
from app.core.auth import CurrentUser
from app.domains.leaderboard.models import LeaderboardEntry, LeaderboardResponse
from app.domains.leaderboard.service import LeaderboardError, LeaderboardService

router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])


def _to_entry(doc: dict) -> LeaderboardEntry:
    return LeaderboardEntry(
        rank=doc["rank"],
        userId=doc["user_id"],
        name=doc["name"],
        username=doc["username"],
        totalPoints=doc["total_points"],
        avgScore=doc["avg_score"],
        gamesPlayed=doc["games_played"],
        roundsPlayed=doc["rounds_played"],
    )


@router.get("", response_model=LeaderboardResponse)
async def get_leaderboard(
    current_user: CurrentUser,
    timeframe: Literal["daily", "weekly", "alltime"] = Query(default="alltime"),
    mode: Literal["all", "indoor", "outdoor"] = Query(default="all"),
    game_type: Literal["all", "daily", "random"] = Query(default="all"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    service: LeaderboardService = deps(LeaderboardService),
) -> LeaderboardResponse:
    try:
        data = await service.get_leaderboard(
            user_id=current_user["oid"],
            timeframe=timeframe,
            mode=mode,
            game_type=game_type,
            limit=limit,
            offset=offset,
        )
    except LeaderboardError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    entries = [_to_entry(entry) for entry in data["entries"]]
    user_entry = _to_entry(data["user_entry"]) if data.get("user_entry") else None
    context_entries = [_to_entry(entry) for entry in data.get("context_entries", [])]

    return LeaderboardResponse(
        entries=entries,
        userEntry=user_entry,
        contextEntries=context_entries,
        totalCount=data["total_count"],
    )
