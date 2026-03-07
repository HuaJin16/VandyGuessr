"""User repository for database operations."""

from typing import Protocol

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.domains.users.entities import UserEntity


class IUserRepository(Protocol):
    """Protocol defining the user repository interface."""

    async def find_by_microsoft_oid(self, oid: str) -> dict | None:
        """Find a user by their Microsoft OID."""
        ...

    async def find_by_username(self, username: str) -> dict | None:
        """Find a user by their username."""
        ...

    async def create(self, user: UserEntity) -> str:
        """Create a new user and return the inserted ID."""
        ...

    async def update_name(self, oid: str, name: str) -> None:
        """Update a user's display name by their Microsoft OID."""
        ...


class UserRepository:
    """MongoDB implementation of the user repository."""

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.collection = db.users

    async def find_by_microsoft_oid(self, oid: str) -> dict | None:
        """Find a user by their Microsoft OID."""
        return await self.collection.find_one({"microsoft_oid": oid})

    async def find_by_username(self, username: str) -> dict | None:
        """Find a user by their username."""
        return await self.collection.find_one({"username": username})

    async def create(self, user: UserEntity) -> str:
        """Create a new user and return the inserted ID."""
        result = await self.collection.insert_one(
            user.model_dump(by_alias=True, exclude={"id"})
        )
        return str(result.inserted_id)

    async def update_name(self, oid: str, name: str) -> None:
        """Update a user's display name by their Microsoft OID."""
        await self.collection.update_one(
            {"microsoft_oid": oid}, {"$set": {"name": name}}
        )
