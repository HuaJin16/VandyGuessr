"""Dependency injection container using lagom."""

import redis.asyncio as aioredis
from fastapi import Depends
from lagom import Container, Singleton
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.db.mongo import get_database
from app.core.db.redis import get_redis
from app.domains.games.daily import DailyChallengeRepository, IDailyChallengeRepository
from app.domains.games.repository import GameRepository, IGameRepository
from app.domains.games.service import GameService
from app.domains.images.repository import IImageRepository, ImageRepository
from app.domains.images.service import ImageService
from app.domains.locations.repository import ILocationRepository, LocationRepository
from app.domains.locations.service import LocationService
from app.domains.multiplayer.connection_manager import ConnectionManager
from app.domains.multiplayer.game_manager import GameManager
from app.domains.multiplayer.repository import (
    IMultiplayerGameRepository,
    MultiplayerGameRepository,
)
from app.domains.multiplayer.service import MultiplayerService
from app.domains.users.repository import IUserRepository, UserRepository
from app.domains.users.service import UserService

# Create the container
container = Container()

# Register database - using a factory that calls get_database()
container[AsyncIOMotorDatabase] = lambda: get_database()

# Register Redis
container[aioredis.Redis] = lambda: get_redis()

# Register repositories
container[IUserRepository] = UserRepository
container[IImageRepository] = ImageRepository
container[ILocationRepository] = LocationRepository
container[IGameRepository] = GameRepository
container[IDailyChallengeRepository] = DailyChallengeRepository

# Register multiplayer repository
container[IMultiplayerGameRepository] = MultiplayerGameRepository

# Register services
container[UserService] = UserService
container[LocationService] = LocationService
container[ImageService] = ImageService
container[GameService] = GameService

# Register multiplayer services (singletons — one instance manages all connections)
container[MultiplayerService] = MultiplayerService
container.define(ConnectionManager, Singleton(ConnectionManager))
container.define(GameManager, Singleton(GameManager))


def deps[T](cls: type[T]) -> T:
    """Resolve a dependency from the container.

    Usage in routers:
        @router.get("/me")
        async def get_me(service: UserService = deps(UserService)):
            ...
    """
    return Depends(lambda: container.resolve(cls))  # type: ignore[return-value]
