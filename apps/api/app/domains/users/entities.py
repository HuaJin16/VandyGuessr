"""User entity for MongoDB documents."""

from datetime import UTC, datetime

from pydantic import BaseModel, Field


class UserEntity(BaseModel):
    """Represents a user document in MongoDB."""

    id: str | None = Field(default=None, alias="_id")
    microsoft_oid: str
    email: str
    username: str
    name: str
    avatar_url: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    model_config = {"populate_by_name": True}
