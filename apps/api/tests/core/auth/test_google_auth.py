import pytest
from fastapi import HTTPException

from app.config import Settings
from app.core.auth.google import build_current_user


def test_google_user_maps_to_provider_oid() -> None:
    payload = {
        "sub": "abc123",
        "email": "judge@example.com",
        "email_verified": True,
        "name": "Judge Judy",
    }

    user = build_current_user(payload, Settings())

    assert user["oid"] == "google:abc123"
    assert user["email"] == "judge@example.com"


@pytest.mark.parametrize("verified", [False, "false", None])
def test_google_user_requires_verified_email(verified: object) -> None:
    payload = {
        "sub": "abc123",
        "email": "judge@example.com",
        "email_verified": verified,
    }

    with pytest.raises(HTTPException) as exc:
        build_current_user(payload, Settings())

    assert exc.value.status_code == 401


def test_google_user_allows_vanderbilt_email() -> None:
    payload = {
        "sub": "abc123",
        "email": "student@vanderbilt.edu",
        "email_verified": True,
    }

    user = build_current_user(payload, Settings())

    assert user["email"] == "student@vanderbilt.edu"


def test_google_user_allows_any_verified_email() -> None:
    payload = {
        "sub": "abc123",
        "email": "other@example.com",
        "email_verified": True,
    }

    user = build_current_user(payload, Settings())

    assert user["email"] == "other@example.com"
