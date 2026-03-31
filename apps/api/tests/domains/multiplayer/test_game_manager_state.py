import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.domains.multiplayer.game_manager_state import GameManagerStateMixin


class _Harness(GameManagerStateMixin):
    def __init__(self) -> None:
        self.cm = AsyncMock()
        self._lobby_ready: dict[str, set[str]] = {}
        self._ready_events: dict[str, asyncio.Event] = {}
        self._ready_players: dict[str, set[str]] = {}
        self._rate_limits: dict[str, list[float]] = {}
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
async def test_maybe_release_ready_event_sets_event_when_all_connected_ready() -> None:
    harness = _Harness()
    event = asyncio.Event()
    harness._ready_events["game-1"] = event
    harness._ready_players["game-1"] = {"u1"}

    doc = {
        "status": "active",
        "players": [
            {"user_id": "u1", "status": "connected"},
            {"user_id": "u2", "status": "forfeited"},
        ],
    }
    await harness._maybe_release_ready_event("game-1", doc)

    assert event.is_set() is True


def test_check_rate_limit_blocks_after_window_threshold() -> None:
    harness = _Harness()

    key = "game-1:u1"
    allowed = [harness._check_rate_limit(key) for _ in range(10)]
    blocked = harness._check_rate_limit(key)

    assert all(allowed)
    assert blocked is False
