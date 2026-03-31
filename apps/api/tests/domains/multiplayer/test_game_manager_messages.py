from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from app.domains.multiplayer.game_manager_messages import GameManagerMessagesMixin


class _Harness(GameManagerMessagesMixin):
    def __init__(self) -> None:
        self.cm = SimpleNamespace(
            send_to_player=AsyncMock(),
            get_local_connections=Mock(return_value={}),
            mark_pong=Mock(),
        )
        self.allow = True
        self.doc = {"players": [{"user_id": "user-1"}]}
        self._handle_start_game = AsyncMock()
        self._handle_submit_guess = AsyncMock()
        self._handle_forfeit = AsyncMock()
        self._handle_extend_lobby = AsyncMock()
        self._handle_leave_lobby = AsyncMock()
        self._handle_ready_next = AsyncMock()
        self._handle_ready_up = AsyncMock()
        self._handle_unready = AsyncMock()
        self._handle_kick = AsyncMock()
        self._handle_request_rematch = AsyncMock()

    def _check_rate_limit(self, _key: str) -> bool:
        return self.allow

    async def _load(self, _game_id: str) -> dict | None:
        return self.doc


@pytest.mark.asyncio
async def test_handle_message_rejects_rate_limited_requests() -> None:
    harness = _Harness()
    harness.allow = False

    await harness.handle_message("game-1", "user-1", '{"type":"pong"}')

    payload = harness.cm.send_to_player.await_args.args[2]
    assert payload["code"] == "RATE_LIMITED"


@pytest.mark.asyncio
async def test_handle_message_rejects_invalid_json() -> None:
    harness = _Harness()

    await harness.handle_message("game-1", "user-1", "not-json")

    payload = harness.cm.send_to_player.await_args.args[2]
    assert payload["code"] == "INVALID_JSON"


@pytest.mark.asyncio
async def test_handle_message_rejects_unknown_type() -> None:
    harness = _Harness()

    await harness.handle_message("game-1", "user-1", '{"type":"wat"}')

    payload = harness.cm.send_to_player.await_args.args[2]
    assert payload["code"] == "UNKNOWN_TYPE"


@pytest.mark.asyncio
async def test_handle_message_rejects_submit_guess_without_coordinates() -> None:
    harness = _Harness()

    await harness.handle_message("game-1", "user-1", '{"type":"submit_guess"}')

    payload = harness.cm.send_to_player.await_args.args[2]
    assert payload["code"] == "MISSING_FIELD"
    harness._handle_submit_guess.assert_not_called()


@pytest.mark.asyncio
async def test_handle_message_dispatches_submit_guess_with_valid_numbers() -> None:
    harness = _Harness()

    await harness.handle_message(
        "game-1",
        "user-1",
        '{"type":"submit_guess","lat":36.1,"lng":-86.8}',
    )

    harness._handle_submit_guess.assert_awaited_once_with(
        "game-1", "user-1", 36.1, -86.8
    )


@pytest.mark.asyncio
async def test_handle_message_rejects_non_participant() -> None:
    harness = _Harness()
    harness.doc = {"players": [{"user_id": "another-user"}]}

    await harness.handle_message("game-1", "user-1", '{"type":"start_game"}')

    payload = harness.cm.send_to_player.await_args.args[2]
    assert payload["code"] == "UNAUTHORIZED"
    harness._handle_start_game.assert_not_called()
