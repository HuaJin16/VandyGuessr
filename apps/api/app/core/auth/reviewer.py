"""Reviewer allowlist (ENV) authorization."""

from typing import Annotated

from fastapi import Depends, HTTPException, status

from app.config import Settings, get_settings
from app.core.auth.microsoft import get_current_user


def require_reviewer(
    user: Annotated[dict, Depends(get_current_user)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict:
    email = (user.get("email") or "").strip().lower()
    allowed = {e.strip().lower() for e in settings.reviewer_emails}
    if not allowed or email not in allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to review submissions",
        )
    return user


ReviewerUser = Annotated[dict, Depends(require_reviewer)]
