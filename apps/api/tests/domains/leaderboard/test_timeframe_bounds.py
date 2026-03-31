from datetime import datetime
from unittest.mock import AsyncMock

from app.domains.leaderboard.service import CHICAGO_TZ, LeaderboardService


def _service() -> LeaderboardService:
    return LeaderboardService(
        leaderboard_repository=AsyncMock(), redis_client=AsyncMock()
    )


def test_daily_timeframe_uses_chicago_midnight_across_dst_start() -> None:
    service = _service()

    class _DstStartService(LeaderboardService):
        @staticmethod
        def _now_local() -> datetime:
            return datetime(2026, 3, 8, 12, 0, 0, tzinfo=CHICAGO_TZ)

    dst_service = _DstStartService(service.leaderboard_repo, service.redis)
    start, end = dst_service._timeframe_bounds("daily")

    assert start == datetime(2026, 3, 8, 6, 0, 0)
    assert end == datetime(2026, 3, 9, 5, 0, 0)


def test_daily_timeframe_uses_chicago_midnight_across_dst_end() -> None:
    service = _service()

    class _DstEndService(LeaderboardService):
        @staticmethod
        def _now_local() -> datetime:
            return datetime(2026, 11, 1, 12, 0, 0, tzinfo=CHICAGO_TZ)

    dst_service = _DstEndService(service.leaderboard_repo, service.redis)
    start, end = dst_service._timeframe_bounds("daily")

    assert start == datetime(2026, 11, 1, 5, 0, 0)
    assert end == datetime(2026, 11, 2, 6, 0, 0)


def test_alltime_timeframe_returns_unbounded() -> None:
    service = _service()
    start, end = service._timeframe_bounds("alltime")

    assert start is None
    assert end is None
