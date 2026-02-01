"""Auth0 authentication utilities."""

from typing import Annotated

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.config import Settings, get_settings

security = HTTPBearer()

# Cache for JWKS
_jwks_cache: dict | None = None


async def get_jwks(settings: Settings) -> dict:
    """Fetch and cache JWKS from Auth0."""
    global _jwks_cache
    if _jwks_cache is None:
        async with httpx.AsyncClient() as client:
            response = await client.get(settings.auth0_jwks_url)
            response.raise_for_status()
            _jwks_cache = response.json()
    return _jwks_cache


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
    """Verify JWT token from Auth0.

    Returns the decoded token payload if valid.
    Raises HTTPException if invalid.
    """
    token = credentials.credentials

    if not settings.auth0_domain:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Auth0 not configured",
        )

    try:
        jwks = await get_jwks(settings)
        signing_key = get_signing_key(jwks, token)

        payload = jwt.decode(
            token,
            signing_key,
            algorithms=[settings.auth0_algorithms],
            audience=settings.auth0_api_audience,
            issuer=settings.auth0_issuer,
        )

        return payload

    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {e!s}",
        ) from e
    except httpx.HTTPError as e:
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
    return {
        "sub": token_payload.get("sub"),
        "email": token_payload.get("email"),
        "permissions": token_payload.get("permissions", []),
    }


# Type alias for dependency injection
CurrentUser = Annotated[dict, Depends(get_current_user)]
