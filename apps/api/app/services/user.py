"""User service for business logic."""

import re
from datetime import datetime

from app.entities.user import UserEntity
from app.repositories.user import IUserRepository


class UserService:
    """Service for user-related business logic."""

    def __init__(self, user_repository: IUserRepository) -> None:
        self.user_repository = user_repository

    @staticmethod
    def generate_username(email: str) -> str:
        """Generate a username from the email local part."""
        local_part = email.split("@")[0]
        # Remove special characters, keep only alphanumeric
        return re.sub(r"[^a-zA-Z0-9]", "", local_part.lower())

    async def ensure_unique_username(self, username: str) -> str:
        """Ensure the username is unique by appending a number if needed."""
        base_username = username
        counter = 1

        while await self.user_repository.find_by_username(username):
            username = f"{base_username}{counter}"
            counter += 1

        return username

    async def get_or_create_user(
        self, oid: str, email: str, name: str | None
    ) -> tuple[dict, bool]:
        """Get an existing user or create a new one.

        Args:
            oid: Microsoft OAuth object ID
            email: User's email address
            name: User's display name from Microsoft profile

        Returns:
            Tuple of (user_doc, was_created)
        """
        # Try to find existing user
        user_doc = await self.user_repository.find_by_microsoft_oid(oid)
        if user_doc:
            return user_doc, False

        # Create new user
        display_name = name or email.split("@")[0]
        username = self.generate_username(email)
        username = await self.ensure_unique_username(username)

        user = UserEntity(
            microsoft_oid=oid,
            email=email,
            username=username,
            name=display_name,
            created_at=datetime.utcnow(),
        )

        user_id = await self.user_repository.create(user)

        # Return the created user as a dict
        user_doc = user.model_dump()
        user_doc["_id"] = user_id

        return user_doc, True
