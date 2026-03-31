from unittest.mock import AsyncMock

import pytest

from app.domains.multiplayer.service import MultiplayerError, MultiplayerService


def _service(
    repo: AsyncMock | None = None,
    image_repo: AsyncMock | None = None,
    redis_client: AsyncMock | None = None,
) -> MultiplayerService:
    return MultiplayerService(
        multiplayer_repository=repo or AsyncMock(),
        image_repository=image_repo or AsyncMock(),
        location_service=AsyncMock(),
        redis_client=redis_client or AsyncMock(),
    )


@pytest.mark.asyncio
async def test_create_game_rejects_when_user_already_has_active_game() -> None:
    repo = AsyncMock()
    repo.find_active_by_user = AsyncMock(return_value={"_id": "existing"})
    image_repo = AsyncMock()
    service = _service(repo=repo, image_repo=image_repo)

    with pytest.raises(
        MultiplayerError, match="already have an active multiplayer game"
    ):
        await service.create_game(
            host_id="host-1",
            host_name="Host",
            avatar_url=None,
            environment="any",
        )

    image_repo.sample_random.assert_not_called()


@pytest.mark.asyncio
async def test_create_game_requires_enough_images() -> None:
    repo = AsyncMock()
    repo.find_active_by_user = AsyncMock(return_value=None)
    image_repo = AsyncMock()
    image_repo.sample_random = AsyncMock(return_value=[{"_id": "img-1"}])
    service = _service(repo=repo, image_repo=image_repo)

    with pytest.raises(MultiplayerError, match="Not enough images available"):
        await service.create_game(
            host_id="host-1",
            host_name="Host",
            avatar_url=None,
            environment="any",
        )


@pytest.mark.asyncio
async def test_join_game_rejects_invalid_or_expired_code() -> None:
    repo = AsyncMock()
    repo.find_by_invite_code = AsyncMock(return_value=None)
    redis_client = AsyncMock()
    redis_client.get = AsyncMock(return_value=None)
    service = _service(repo=repo, redis_client=redis_client)

    with pytest.raises(MultiplayerError, match="Invalid or expired invite code") as exc:
        await service.join_game(
            user_id="player-1",
            name="Player",
            avatar_url=None,
            code="abc123",
        )

    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_join_game_returns_existing_player_without_readding() -> None:
    doc = {
        "_id": "game-1",
        "status": "waiting",
        "invite_code": "ABC123",
        "players": [{"user_id": "player-1", "name": "Player"}],
    }
    repo = AsyncMock()
    repo.find_by_id = AsyncMock(return_value=doc)
    redis_client = AsyncMock()
    redis_client.get = AsyncMock(return_value="game-1")
    redis_client.ttl = AsyncMock(return_value=300)
    service = _service(repo=repo, redis_client=redis_client)

    result_doc, player = await service.join_game(
        user_id="player-1",
        name="Player",
        avatar_url=None,
        code="abc123",
    )

    assert player is None
    assert result_doc["_id"] == "game-1"
    repo.add_player_if_waiting_and_not_full.assert_not_called()


@pytest.mark.asyncio
async def test_get_game_expires_waiting_lobby_when_redis_key_missing() -> None:
    doc = {
        "_id": "game-1",
        "status": "waiting",
        "invite_code": "ABC123",
        "players": [{"user_id": "player-1"}],
    }
    repo = AsyncMock()
    repo.find_by_id = AsyncMock(return_value=doc)
    redis_client = AsyncMock()
    redis_client.ttl = AsyncMock(return_value=-2)
    service = _service(repo=repo, redis_client=redis_client)

    result = await service.get_game("game-1", "player-1")

    assert result["status"] == "cancelled"
    repo.update_game.assert_awaited_once_with("game-1", {"status": "cancelled"})
