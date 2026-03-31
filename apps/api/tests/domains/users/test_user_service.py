from unittest.mock import AsyncMock

import pytest

from app.domains.users.service import UserService


def test_generate_username_removes_non_alphanumeric_characters() -> None:
    assert (
        UserService.generate_username("Ryan.Mc-Cauley+dev@vanderbilt.edu")
        == "ryanmccauleydev"
    )


@pytest.mark.asyncio
async def test_ensure_unique_username_appends_incrementing_suffix() -> None:
    repository = AsyncMock()
    repository.find_by_username = AsyncMock(
        side_effect=[{"_id": "1"}, {"_id": "2"}, None]
    )
    service = UserService(repository)

    username = await service.ensure_unique_username("ryan")

    assert username == "ryan2"


@pytest.mark.asyncio
async def test_get_or_create_user_returns_existing_user_without_creating() -> None:
    repository = AsyncMock()
    existing = {
        "_id": "user-123",
        "microsoft_oid": "oid-1",
        "email": "user@example.com",
        "username": "user",
        "name": "User",
    }
    repository.find_by_microsoft_oid = AsyncMock(return_value=existing)
    service = UserService(repository)

    user, created = await service.get_or_create_user(
        oid="oid-1",
        email="user@example.com",
        name="User Name",
    )

    assert created is False
    assert user == existing
    repository.create.assert_not_called()


@pytest.mark.asyncio
async def test_get_or_create_user_creates_new_user_with_fallback_name() -> None:
    repository = AsyncMock()
    repository.find_by_microsoft_oid = AsyncMock(return_value=None)
    repository.find_by_username = AsyncMock(return_value=None)
    repository.create = AsyncMock(return_value="new-user-id")
    service = UserService(repository)

    user, created = await service.get_or_create_user(
        oid="oid-2",
        email="new.user@example.com",
        name=None,
    )

    assert created is True
    assert user["_id"] == "new-user-id"
    assert user["username"] == "newuser"
    assert user["name"] == "new.user"
    repository.create.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_display_name_updates_when_name_changes() -> None:
    repository = AsyncMock()
    repository.find_by_microsoft_oid = AsyncMock(
        return_value={
            "_id": "user-123",
            "microsoft_oid": "oid-1",
            "email": "user@example.com",
            "username": "user",
            "name": "Old Name",
        }
    )
    service = UserService(repository)

    user = await service.update_display_name(
        oid="oid-1",
        email="user@example.com",
        name="New Name",
    )

    assert user["name"] == "New Name"
    repository.update_name.assert_awaited_once_with("oid-1", "New Name")


@pytest.mark.asyncio
async def test_update_display_name_noops_when_name_matches() -> None:
    repository = AsyncMock()
    repository.find_by_microsoft_oid = AsyncMock(
        return_value={
            "_id": "user-123",
            "microsoft_oid": "oid-1",
            "email": "user@example.com",
            "username": "user",
            "name": "Same Name",
        }
    )
    service = UserService(repository)

    user = await service.update_display_name(
        oid="oid-1",
        email="user@example.com",
        name="Same Name",
    )

    assert user["name"] == "Same Name"
    repository.update_name.assert_not_called()
