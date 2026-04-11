from datetime import datetime
from types import SimpleNamespace

from app.domains.leaderboard.repository import LeaderboardRepository


def _repo() -> LeaderboardRepository:
    return LeaderboardRepository(SimpleNamespace(games=object()))


def test_build_base_match_all_does_not_filter_daily_mode() -> None:
    repo = _repo()

    start = datetime(2026, 4, 1, 0, 0, 0)
    end = datetime(2026, 4, 2, 0, 0, 0)
    match = repo._build_base_match("all", start, end)

    assert match == {
        "status": "completed",
        "created_at": {"$gte": start, "$lt": end},
    }


def test_build_base_match_daily_filters_daily_challenge_games() -> None:
    repo = _repo()

    match = repo._build_base_match("daily", None, None)

    assert match == {
        "status": "completed",
        "mode.daily": True,
    }


def test_build_base_match_random_filters_random_drop_games() -> None:
    repo = _repo()

    match = repo._build_base_match("random", None, None)

    assert match == {
        "status": "completed",
        "mode.daily": False,
    }
