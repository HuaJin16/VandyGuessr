from unittest.mock import AsyncMock

import pytest

from app.domains.multiplayer.service import (
    MAX_PLAYERS,
    ROUNDS_PER_GAME,
    MultiplayerError,
    MultiplayerService,
)


def _tiles_payload() -> dict:
    return {
        "version": 1,
        "base_url": "https://cdn.test/images/base.jpg",
        "tile_url_template": "https://cdn.test/images/l{level}/{col}_{row}.jpg",
        "original_width": 4000,
        "original_height": 2000,
        "aspect_ratio": 2.0,
        "base_pano_data": {
            "full_width": 4000,
            "full_height": 2000,
            "cropped_width": 4000,
            "cropped_height": 2000,
            "cropped_x": 0,
            "cropped_y": 0,
        },
        "levels": [
            {
                "level": 0,
                "width": 1024,
                "height": 512,
                "cols": 2,
                "rows": 1,
            }
        ],
    }


def _image_doc(index: int, *, tiles: object | None = None) -> dict:
    payload = {
        "_id": f"img-{index}",
        "url": f"https://cdn.test/images/{index}.jpg",
        "latitude": 36.14 + index,
        "longitude": -86.8 - index,
        "location_name": f"Location {index}",
    }
    if tiles is not None:
        payload["tiles"] = tiles
    return payload


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
async def test_create_game_allows_user_with_existing_active_game() -> None:
    repo = AsyncMock()
    repo.find_by_invite_code = AsyncMock(return_value=None)
    repo.create = AsyncMock(return_value="game-2")
    repo.find_by_id = AsyncMock(
        return_value={
            "_id": "game-2",
            "status": "waiting",
            "invite_code": "XYZ789",
            "players": [],
            "rounds": [],
        }
    )
    image_repo = AsyncMock()
    image_repo.sample_random = AsyncMock(
        return_value=[_image_doc(i) for i in range(ROUNDS_PER_GAME)]
    )
    redis_client = AsyncMock()
    service = _service(repo=repo, image_repo=image_repo, redis_client=redis_client)

    result = await service.create_game(
        host_id="host-1",
        host_name="Host",
        avatar_url=None,
        environment="any",
    )

    assert result["_id"] == "game-2"
    repo.create.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_game_requires_enough_images() -> None:
    repo = AsyncMock()
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
async def test_create_game_carries_valid_image_tiles_into_rounds() -> None:
    repo = AsyncMock()
    repo.find_by_invite_code = AsyncMock(return_value=None)
    repo.create = AsyncMock(return_value="game-1")
    repo.find_by_id = AsyncMock(
        return_value={
            "_id": "game-1",
            "status": "waiting",
            "invite_code": "ABC123",
            "players": [],
            "rounds": [],
        }
    )

    image_repo = AsyncMock()
    image_repo.sample_random = AsyncMock(
        return_value=[
            _image_doc(index, tiles=_tiles_payload())
            for index in range(ROUNDS_PER_GAME)
        ]
    )
    redis_client = AsyncMock()
    service = _service(repo=repo, image_repo=image_repo, redis_client=redis_client)

    await service.create_game(
        host_id="host-1",
        host_name="Host",
        avatar_url=None,
        environment="any",
    )

    created_game = repo.create.await_args.args[0]
    assert all(round_data.image_tiles is not None for round_data in created_game.rounds)


@pytest.mark.asyncio
async def test_create_game_falls_back_when_image_tiles_invalid() -> None:
    repo = AsyncMock()
    repo.find_by_invite_code = AsyncMock(return_value=None)
    repo.create = AsyncMock(return_value="game-1")
    repo.find_by_id = AsyncMock(
        return_value={
            "_id": "game-1",
            "status": "waiting",
            "invite_code": "ABC123",
            "players": [],
            "rounds": [],
        }
    )

    image_repo = AsyncMock()
    image_repo.sample_random = AsyncMock(
        return_value=[
            _image_doc(0, tiles={"version": 1}),
            _image_doc(1),
            _image_doc(2, tiles="bad"),
            *[
                _image_doc(index, tiles=_tiles_payload())
                for index in range(3, ROUNDS_PER_GAME)
            ],
        ]
    )
    redis_client = AsyncMock()
    service = _service(repo=repo, image_repo=image_repo, redis_client=redis_client)

    await service.create_game(
        host_id="host-1",
        host_name="Host",
        avatar_url=None,
        environment="any",
    )

    created_game = repo.create.await_args.args[0]
    assert created_game.rounds[0].image_tiles is None
    assert created_game.rounds[1].image_tiles is None
    assert created_game.rounds[2].image_tiles is None
    assert all(
        round_data.image_tiles is not None for round_data in created_game.rounds[3:]
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
async def test_join_game_rejects_when_lobby_is_full() -> None:
    doc = {
        "_id": "game-1",
        "status": "waiting",
        "invite_code": "ABC123",
        "players": [
            {"user_id": f"player-{index}", "name": f"Player {index}"}
            for index in range(MAX_PLAYERS)
        ],
    }
    repo = AsyncMock()
    repo.find_by_id = AsyncMock(side_effect=[doc, doc])
    repo.add_player_if_waiting_and_not_full = AsyncMock(return_value=False)
    redis_client = AsyncMock()
    redis_client.get = AsyncMock(return_value="game-1")
    redis_client.ttl = AsyncMock(return_value=300)
    service = _service(repo=repo, redis_client=redis_client)

    with pytest.raises(MultiplayerError, match="Game is full") as exc:
        await service.join_game(
            user_id="player-new",
            name="New Player",
            avatar_url=None,
            code="abc123",
        )

    assert exc.value.status_code == 409
    repo.add_player_if_waiting_and_not_full.assert_awaited_once()


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
