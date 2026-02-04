"""User endpoints."""

from fastapi import APIRouter, Depends

from app.core.auth import CurrentUser
from app.core.database import get_database
from app.models.user import UserResponse
from app.repositories.user import UserRepository
from app.services.user import UserService

router = APIRouter(prefix="/users", tags=["users"])


def get_user_service() -> UserService:
    """Dependency to get the user service with injected repository."""
    db = get_database()
    repository = UserRepository(db)
    return UserService(repository)


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: CurrentUser,
    user_service: UserService = Depends(get_user_service),
) -> UserResponse:
    """Get or create the current user's profile."""
    user_doc, _ = await user_service.get_or_create_user(
        oid=current_user["oid"],
        email=current_user["email"],
        name=current_user["name"],
    )

    return UserResponse(
        id=str(user_doc["_id"]),
        email=user_doc["email"],
        username=user_doc["username"],
        name=user_doc["name"],
        avatar_url=user_doc.get("avatar_url"),
    )
