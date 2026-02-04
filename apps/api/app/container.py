"""Dependency injection container using lagom."""

from fastapi import Depends
from lagom import Container
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.db.mongo import get_database
from app.domains.users.repository import IUserRepository, UserRepository
from app.domains.users.service import UserService

# Create the container
container = Container()

# Register database - using a factory that calls get_database()
container[AsyncIOMotorDatabase] = lambda: get_database()

# Register repositories
container[IUserRepository] = UserRepository

# Register services
container[UserService] = UserService


def deps[T](cls: type[T]) -> T:
    """Resolve a dependency from the container.

    Usage in routers:
        @router.get("/me")
        async def get_me(service: UserService = deps(UserService)):
            ...
    """
    return Depends(lambda: container.resolve(cls))  # type: ignore[return-value]
