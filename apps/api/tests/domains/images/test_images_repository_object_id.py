from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.domains.images.repository import ImageRepository


@pytest.mark.asyncio
async def test_find_by_id_invalid_object_id_returns_none_without_query() -> None:
    collection = AsyncMock()
    repository = ImageRepository(SimpleNamespace(images=collection))

    result = await repository.find_by_id("not-an-object-id")

    assert result is None
    collection.find_one.assert_not_awaited()


@pytest.mark.asyncio
async def test_find_by_ids_filters_invalid_object_ids() -> None:
    collection = AsyncMock()
    cursor = AsyncMock()
    cursor.to_list = AsyncMock(return_value=[])
    collection.find.return_value = cursor
    repository = ImageRepository(SimpleNamespace(images=collection))

    result = await repository.find_by_ids(["bad-a", "bad-b"])

    assert result == []
    collection.find.assert_not_called()


@pytest.mark.asyncio
async def test_update_moderation_invalid_object_id_returns_false_without_update() -> (
    None
):
    collection = AsyncMock()
    repository = ImageRepository(SimpleNamespace(images=collection))

    updated = await repository.update_moderation(
        "bad-id",
        moderation_status="approved",
        reviewed_by_user_id="reviewer",
    )

    assert updated is False
    collection.update_one.assert_not_awaited()
