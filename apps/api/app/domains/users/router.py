"""User endpoints."""

from fastapi import APIRouter

from app.container import deps
from app.core.auth import CurrentUser
from app.domains.users.models import UserResponse
from app.domains.users.service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: CurrentUser,
    user_service: UserService = deps(UserService),
) -> UserResponse:
    """Get or create the current user's profile."""
    user_doc, _ = await user_service.get_or_create_user(
        oid=current_user["oid"],
        email=current_user["email"],
        name=current_user["name"],
    )

    stats = await user_service.get_stats_response(user_doc)

    return UserResponse(
        id=str(user_doc["_id"]),
        email=user_doc["email"],
        username=user_doc["username"],
        name=user_doc["name"],
        avatar_url=user_doc.get("avatar_url"),
        stats=stats,
    )
