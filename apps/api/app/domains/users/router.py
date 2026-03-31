"""User endpoints."""

from fastapi import APIRouter, Depends

from app.config import Settings, get_settings
from app.container import deps
from app.core.auth import CurrentUser
from app.domains.users.models import UpdateProfileRequest, UserResponse
from app.domains.users.service import UserService

router = APIRouter(prefix="/users", tags=["users"])


def _can_review_submissions(user_doc: dict, settings: Settings) -> bool:
    email_norm = (user_doc["email"] or "").strip().lower()
    allow = {e.strip().lower() for e in settings.reviewer_emails}
    return bool(allow) and email_norm in allow


def _to_user_response(user_doc: dict, settings: Settings) -> UserResponse:
    return UserResponse(
        id=str(user_doc["_id"]),
        email=user_doc["email"],
        username=user_doc["username"],
        name=user_doc["name"],
        avatar_url=user_doc.get("avatar_url"),
        can_review_submissions=_can_review_submissions(user_doc, settings),
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: CurrentUser,
    user_service: UserService = deps(UserService),
    settings: Settings = Depends(get_settings),
) -> UserResponse:
    """Get or create the current user's profile."""
    user_doc, _ = await user_service.get_or_create_user(
        oid=current_user["oid"],
        email=current_user["email"],
        name=current_user["name"],
    )
    return _to_user_response(user_doc, settings)


@router.patch("/me", response_model=UserResponse)
async def update_current_user_profile(
    body: UpdateProfileRequest,
    current_user: CurrentUser,
    user_service: UserService = deps(UserService),
    settings: Settings = Depends(get_settings),
) -> UserResponse:
    """Update the current user's editable profile fields."""
    user_doc = await user_service.update_display_name(
        oid=current_user["oid"],
        email=current_user["email"],
        name=body.name,
    )
    return _to_user_response(user_doc, settings)
