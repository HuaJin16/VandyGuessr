from unittest.mock import ANY, AsyncMock

import pytest

from app.domains.leaderboard.service import LeaderboardService


def _raw_entry(user_doc_id: str, user_oid: str) -> dict:
    return {
        "user_doc_id": user_doc_id,
        "user_oid": user_oid,
        "name": f"User {user_doc_id}",
        "username": f"user{user_doc_id}",
        "total_points": 5000,
        "avg_score": 1000.0,
        "games_played": 5,
        "rounds_played": 25,
    }


@pytest.mark.asyncio
async def test_get_leaderboard_uses_game_type_in_cache_key() -> None:
    repo = AsyncMock()
    repo.get_leaderboard_page = AsyncMock(return_value=([_raw_entry("1", "oid-1")], 1))
    repo.get_user_entry = AsyncMock(return_value=None)

    redis_client = AsyncMock()
    redis_client.get = AsyncMock(return_value=None)
    redis_client.setex = AsyncMock()

    service = LeaderboardService(repo, redis_client)

    result = await service.get_leaderboard(
        user_id="oid-1",
        timeframe="daily",
        mode="all",
        game_type="daily",
        limit=20,
        offset=0,
    )

    assert result["total_count"] == 1
    redis_client.get.assert_awaited_once_with("lb:v4:daily:all:daily:0:20")

    kwargs = repo.get_leaderboard_page.await_args.kwargs
    assert kwargs["mode"] == "all"
    assert kwargs["game_type"] == "daily"
    assert kwargs["limit"] == 20
    assert kwargs["offset"] == 0
    assert kwargs["start"] is not None
    assert kwargs["end"] is not None

    redis_client.setex.assert_awaited_once_with(
        "lb:v4:daily:all:daily:0:20",
        300,
        ANY,
    )


@pytest.mark.asyncio
async def test_get_leaderboard_threads_game_type_to_user_and_context_queries() -> None:
    repo = AsyncMock()
    repo.get_leaderboard_page = AsyncMock(return_value=([], 0))
    repo.get_user_entry = AsyncMock(return_value=_raw_entry("7", "oid-7"))
    repo.count_users_ahead = AsyncMock(return_value=10)
    repo.get_entries_by_offset = AsyncMock(
        return_value=[
            _raw_entry("8", "oid-8"),
            _raw_entry("9", "oid-9"),
            _raw_entry("10", "oid-10"),
        ]
    )

    redis_client = AsyncMock()
    redis_client.get = AsyncMock(return_value=None)
    redis_client.setex = AsyncMock()

    service = LeaderboardService(repo, redis_client)

    result = await service.get_leaderboard(
        user_id="oid-7",
        timeframe="weekly",
        mode="indoor",
        game_type="random",
        limit=20,
        offset=0,
    )

    assert result["user_entry"] is not None

    user_entry_kwargs = repo.get_user_entry.await_args.kwargs
    assert user_entry_kwargs["mode"] == "indoor"
    assert user_entry_kwargs["game_type"] == "random"

    count_ahead_kwargs = repo.count_users_ahead.await_args.kwargs
    assert count_ahead_kwargs["mode"] == "indoor"
    assert count_ahead_kwargs["game_type"] == "random"

    context_kwargs = repo.get_entries_by_offset.await_args.kwargs
    assert context_kwargs["mode"] == "indoor"
    assert context_kwargs["game_type"] == "random"
