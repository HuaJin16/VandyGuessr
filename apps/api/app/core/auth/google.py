"""Google OAuth authentication utilities."""

from typing import Any

import httpx
import structlog
from fastapi import HTTPException, status
from jose import JWTError, jwt

from app.config import Settings

logger = structlog.get_logger()

GOOGLE_ISSUERS = {"accounts.google.com", "https://accounts.google.com"}

_jwks_cache: dict[str, Any] | None = None


def _is_verified_email(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() == "true"
    return False


async def get_jwks(settings: Settings) -> dict[str, Any]:
    global _jwks_cache
    if _jwks_cache is None:
        async with httpx.AsyncClient() as client:
            response = await client.get(settings.google_jwks_url)
            response.raise_for_status()
            _jwks_cache = response.json()
    return _jwks_cache or {}


def get_signing_key(jwks: dict[str, Any], token: str) -> dict[str, Any]:
    header = jwt.get_unverified_header(token)
    kid = header.get("kid")
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return key

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unable to find appropriate key",
    )


async def verify_token_raw(token: str, settings: Settings) -> dict[str, Any]:
    if not settings.google_client_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google OAuth not configured",
        )

    try:
        jwks = await get_jwks(settings)
        signing_key = get_signing_key(jwks, token)
        payload = jwt.decode(
            token,
            signing_key,
            algorithms=[settings.google_algorithms],
            audience=settings.google_client_id,
        )
        issuer = payload.get("iss")
        if issuer not in settings.google_issuers:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token issuer",
            )
        return payload
    except JWTError as e:
        logger.warning("google_jwt_verification_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        ) from e
    except httpx.HTTPError as e:
        logger.error("google_jwks_fetch_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to verify token",
        ) from e


def build_current_user(
    token_payload: dict[str, Any], _settings: Settings
) -> dict[str, Any]:
    email = (token_payload.get("email") or "").strip().lower()
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google account is missing email claim",
        )

    if not _is_verified_email(token_payload.get("email_verified")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google email must be verified",
        )

    sub = token_payload.get("sub")
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google account is missing subject claim",
        )

    name = (token_payload.get("name") or "").strip() or email.split("@")[0]
    return {
        "sub": sub,
        "oid": f"google:{sub}",
        "email": email,
        "name": name,
    }
