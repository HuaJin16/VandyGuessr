from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.domains.games.repository import GameRepository


@pytest.mark.asyncio
async def test_find_by_id_invalid_object_id_returns_none_without_query() -> None:
    collection = AsyncMock()
    repository = GameRepository(SimpleNamespace(games=collection))

    result = await repository.find_by_id("not-an-object-id")

    assert result is None
    collection.find_one.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_round_invalid_object_id_skips_update() -> None:
    collection = AsyncMock()
    repository = GameRepository(SimpleNamespace(games=collection))

    await repository.update_round("bad-id", round_index=0, round_data={"score": 10})

    collection.update_one.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_game_invalid_object_id_skips_update() -> None:
    collection = AsyncMock()
    repository = GameRepository(SimpleNamespace(games=collection))

    await repository.update_game("bad-id", {"status": "completed"})

    collection.update_one.assert_not_awaited()
