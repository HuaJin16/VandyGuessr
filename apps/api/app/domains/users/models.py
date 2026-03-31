"""User API models for request/response schemas."""

from pydantic import BaseModel, Field, field_validator


class UpdateProfileRequest(BaseModel):
    """Request body for updating the current user's profile."""

    name: str = Field(min_length=1, max_length=80)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = " ".join(value.split())
        if not normalized:
            raise ValueError("Name cannot be empty")
        return normalized


class UserResponse(BaseModel):
    """User profile response."""

    id: str
    email: str
    username: str
    name: str
    avatar_url: str | None
    can_review_submissions: bool = False
