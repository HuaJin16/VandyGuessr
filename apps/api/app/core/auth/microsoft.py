"""Microsoft OAuth authentication utilities."""

from typing import Annotated

import httpx
import structlog
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.config import Settings, get_settings

logger = structlog.get_logger()

security = HTTPBearer()

# Cache for JWKS
_jwks_cache: dict | None = None


def _is_vanderbilt_email(email: str | None) -> bool:
    if not email:
        return False
    return email.lower().endswith("@vanderbilt.edu")


async def get_jwks(settings: Settings) -> dict:
    """Fetch and cache JWKS from Microsoft OAuth."""
    global _jwks_cache
    if _jwks_cache is None:
        async with httpx.AsyncClient() as client:
            response = await client.get(settings.microsoft_jwks_url)
            response.raise_for_status()
            _jwks_cache = response.json()
    return _jwks_cache or {}


def get_signing_key(jwks: dict, token: str) -> str:
    """Extract the signing key from JWKS based on token header."""
    unverified_header = jwt.get_unverified_header(token)
    kid = unverified_header.get("kid")

    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return key

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unable to find appropriate key",
    )


async def verify_token(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict:
    """Verify JWT token from Microsoft OAuth.

    Returns the decoded token payload if valid.
    Raises HTTPException if invalid.
    """
    token = credentials.credentials

    if not settings.microsoft_client_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Microsoft OAuth not configured",
        )

    try:
        jwks = await get_jwks(settings)
        signing_key = get_signing_key(jwks, token)

        decode_options = {}
        issuer = settings.microsoft_issuer
        if settings.microsoft_tenant_id == "common":
            decode_options = {"verify_iss": False}
            issuer = None

        payload = jwt.decode(
            token,
            signing_key,
            algorithms=[settings.microsoft_algorithms],
            audience=settings.microsoft_client_id,
            issuer=issuer,
            options=decode_options,
        )

        return payload

    except JWTError as e:
        logger.warning("jwt_verification_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {e!s}",
        ) from e
    except httpx.HTTPError as e:
        logger.error("jwks_fetch_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Unable to verify token: {e!s}",
        ) from e


async def get_current_user(
    token_payload: Annotated[dict, Depends(verify_token)],
) -> dict:
    """Get the current user from the verified token.

    Returns user information extracted from token.
    """
    email = token_payload.get("email") or token_payload.get("preferred_username")
    if not _is_vanderbilt_email(email):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized email domain",
        )

    return {
        "sub": token_payload.get("sub"),
        "oid": token_payload.get("oid"),
        "email": email,
        "name": token_payload.get("name"),
    }


# Type alias for dependency injection
CurrentUser = Annotated[dict, Depends(get_current_user)]
