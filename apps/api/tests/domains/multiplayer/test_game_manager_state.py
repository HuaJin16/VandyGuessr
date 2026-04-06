from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.domains.multiplayer.game_manager import GameManager
from app.domains.multiplayer.game_manager_shared import (
    READY_ADVANCE_LOCK_TTL_SECONDS,
    READY_BARRIER_TTL_SECONDS,
)
from app.domains.multiplayer.game_manager_state import GameManagerStateMixin


class _Harness(GameManagerStateMixin):
    def __init__(self) -> None:
        self.cm = SimpleNamespace(send_to_player=AsyncMock(), worker_id="worker-1")
        self.redis = AsyncMock()
        self._lobby_ready: dict[str, set[str]] = {}
        self._rate_limits: dict[str, list[float]] = {}
        self._start_round = AsyncMock()
        self.repo = SimpleNamespace(find_by_id=AsyncMock())


def _sample_doc() -> dict:
    now = datetime.now(UTC)
    return {
        "_id": "game-1",
        "status": "active",
        "current_round": 1,
        "players": [
            {
                "user_id": "u1",
                "name": "One",
                "status": "connected",
                "total_score": 0,
            },
            {
                "user_id": "u2",
                "name": "Two",
                "status": "forfeited",
                "total_score": 10,
            },
        ],
        "rounds": [
            {
                "actual_lat": 36.0,
                "actual_lng": -86.8,
                "image_url": "https://img.test/1.jpg",
                "location_name": "Commons",
                "expires_at": now,
                "guesses": {
                    "u1": {
                        "lat": 36.0,
                        "lng": -86.8,
                        "score": 5000,
                        "distance_meters": 0.1,
                    }
                },
            }
        ],
    }


def test_build_round_result_payload_excludes_forfeited_players_by_default() -> None:
    harness = _Harness()
    payload = harness._build_round_result_payload(_sample_doc(), 0)

    assert len(payload["results"]) == 1
    assert payload["results"][0]["userId"] == "u1"
    assert len(payload["standings"]) == 1


def test_build_round_result_payload_can_include_forfeited_players() -> None:
    harness = _Harness()
    payload = harness._build_round_result_payload(
        _sample_doc(),
        0,
        include_forfeited=True,
    )

    assert {r["userId"] for r in payload["results"]} == {"u1", "u2"}


@pytest.mark.asyncio
async def test_send_game_state_includes_round_snapshot_and_ready_players() -> None:
    harness = _Harness()
    doc = _sample_doc()
    harness._lobby_ready["game-1"] = {"u1"}

    await harness._send_game_state("game-1", "u1", doc)

    message = harness.cm.send_to_player.await_args.args[2]
    assert message["currentRound"] == 1
    assert message["round"]["imageUrl"] == "https://img.test/1.jpg"
    assert message["hasGuessedThisRound"] is True
    assert message["readyPlayers"] == ["u1"]


@pytest.mark.asyncio
async def test_mark_player_ready_for_next_round_writes_to_redis_set() -> None:
    harness = _Harness()

    await harness._mark_player_ready_for_next_round("game-1", 2, "u1")

    harness.redis.sadd.assert_awaited_once_with("mp:ready:game-1:2", "u1")
    harness.redis.expire.assert_awaited_once_with(
        "mp:ready:game-1:2",
        READY_BARRIER_TTL_SECONDS,
    )


@pytest.mark.asyncio
async def test_maybe_advance_ready_barrier_starts_next_round_once_barrier_is_met() -> (
    None
):
    harness = _Harness()

    doc = {
        "_id": "game-1",
        "status": "active",
        "current_round": 1,
        "players": [
            {"user_id": "u1", "status": "connected"},
            {"user_id": "u2", "status": "connected"},
            {"user_id": "u3", "status": "forfeited"},
        ],
        "rounds": [{"_resolved": True}, {"_resolved": False}],
    }
    harness.redis.smembers = AsyncMock(return_value={"u1", "u2"})
    harness.redis.set = AsyncMock(return_value=True)
    harness.repo.find_by_id = AsyncMock(return_value=doc)

    await harness._maybe_advance_ready_barrier("game-1", doc)

    harness.redis.set.assert_awaited_once_with(
        "mp:ready-lock:game-1:1",
        "worker-1",
        ex=READY_ADVANCE_LOCK_TTL_SECONDS,
        nx=True,
    )
    harness._start_round.assert_awaited_once_with("game-1", 1)
    harness.redis.delete.assert_awaited_once_with(
        "mp:ready:game-1:1",
        "mp:ready-lock:game-1:1",
    )


@pytest.mark.asyncio
async def test_maybe_advance_ready_barrier_does_not_start_round_before_all_ready() -> (
    None
):
    harness = _Harness()

    doc = {
        "_id": "game-1",
        "status": "active",
        "current_round": 1,
        "players": [
            {"user_id": "u1", "status": "connected"},
            {"user_id": "u2", "status": "connected"},
        ],
        "rounds": [{"_resolved": True}, {"_resolved": False}],
    }
    harness.redis.smembers = AsyncMock(return_value={"u1"})
    harness.redis.set = AsyncMock(return_value=True)

    await harness._maybe_advance_ready_barrier("game-1", doc)

    harness.redis.set.assert_not_awaited()
    harness._start_round.assert_not_awaited()


@pytest.mark.asyncio
async def test_maybe_advance_ready_barrier_skips_when_lock_not_acquired() -> None:
    harness = _Harness()

    doc = {
        "_id": "game-1",
        "status": "active",
        "current_round": 1,
        "players": [
            {"user_id": "u1", "status": "connected"},
            {"user_id": "u2", "status": "connected"},
        ],
        "rounds": [{"_resolved": True}, {"_resolved": False}],
    }
    harness.redis.smembers = AsyncMock(return_value={"u1", "u2"})
    harness.redis.set = AsyncMock(return_value=False)

    await harness._maybe_advance_ready_barrier("game-1", doc)

    harness._start_round.assert_not_awaited()


def test_check_rate_limit_blocks_after_window_threshold() -> None:
    harness = _Harness()

    key = "game-1:u1"
    allowed = [harness._check_rate_limit(key) for _ in range(10)]
    blocked = harness._check_rate_limit(key)

    assert all(allowed)
    assert blocked is False


def _build_game_manager(doc: dict) -> GameManager:
    repo = AsyncMock()
    repo.find_by_id = AsyncMock(return_value=doc)

    manager = GameManager(
        repository=repo,
        connection_manager=SimpleNamespace(worker_id="worker-1"),
        location_service=AsyncMock(),
        multiplayer_service=AsyncMock(),
        redis_client=AsyncMock(),
    )
    manager._mark_player_ready_for_next_round = AsyncMock()
    manager._maybe_advance_ready_barrier = AsyncMock()
    return manager


@pytest.mark.asyncio
async def test_handle_ready_next_marks_player_and_checks_barrier_when_round_resolved() -> (
    None
):
    doc = {
        "_id": "game-1",
        "status": "active",
        "current_round": 1,
        "players": [{"user_id": "u1", "status": "connected"}],
        "rounds": [{"_resolved": True}, {"_resolved": False}],
    }
    manager = _build_game_manager(doc)

    await manager._handle_ready_next("game-1", "u1")

    manager._mark_player_ready_for_next_round.assert_awaited_once_with(
        "game-1",
        1,
        "u1",
    )
    manager._maybe_advance_ready_barrier.assert_awaited_once_with("game-1", doc)


@pytest.mark.asyncio
async def test_handle_ready_next_ignores_unresolved_round() -> None:
    doc = {
        "_id": "game-1",
        "status": "active",
        "current_round": 1,
        "players": [{"user_id": "u1", "status": "connected"}],
        "rounds": [{"_resolved": False}, {"_resolved": False}],
    }
    manager = _build_game_manager(doc)

    await manager._handle_ready_next("game-1", "u1")

    manager._mark_player_ready_for_next_round.assert_not_awaited()
    manager._maybe_advance_ready_barrier.assert_not_awaited()


@pytest.mark.asyncio
async def test_handle_ready_next_ignores_disconnected_or_final_round_cases() -> None:
    disconnected_doc = {
        "_id": "game-1",
        "status": "active",
        "current_round": 1,
        "players": [{"user_id": "u1", "status": "disconnected"}],
        "rounds": [{"_resolved": True}, {"_resolved": False}],
    }
    disconnected_manager = _build_game_manager(disconnected_doc)

    await disconnected_manager._handle_ready_next("game-1", "u1")

    disconnected_manager._mark_player_ready_for_next_round.assert_not_awaited()

    final_round_doc = {
        "_id": "game-1",
        "status": "active",
        "current_round": 1,
        "players": [{"user_id": "u1", "status": "connected"}],
        "rounds": [{"_resolved": True}],
    }
    final_round_manager = _build_game_manager(final_round_doc)

    await final_round_manager._handle_ready_next("game-1", "u1")

    final_round_manager._mark_player_ready_for_next_round.assert_not_awaited()
