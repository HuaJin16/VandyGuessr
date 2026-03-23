"""User API models for request/response schemas."""

from pydantic import BaseModel


class UserResponse(BaseModel):
    """User profile response."""

    id: str
    email: str
    username: str
    name: str
    avatar_url: str | None
    can_review_submissions: bool = False
