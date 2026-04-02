"""Provider-aware authentication selector for Microsoft and Google tokens."""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.config import Settings, get_settings
from app.core.auth.google import GOOGLE_ISSUERS
from app.core.auth.google import build_current_user as build_google_user
from app.core.auth.google import verify_token_raw as verify_google_token_raw
from app.core.auth.microsoft import build_current_user as build_microsoft_user
from app.core.auth.microsoft import verify_token_raw as verify_microsoft_token_raw

security = HTTPBearer()


def _get_issuer(token: str) -> str:
    try:
        claims = jwt.get_unverified_claims(token)
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        ) from e

    issuer = claims.get("iss")
    if not isinstance(issuer, str) or not issuer:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token issuer missing",
        )
    return issuer


def _is_microsoft_issuer(issuer: str) -> bool:
    return "login.microsoftonline.com" in issuer.lower()


def _is_google_issuer(issuer: str) -> bool:
    return issuer in GOOGLE_ISSUERS


async def verify_token_raw(token: str, settings: Settings) -> dict:
    issuer = _get_issuer(token)
    if _is_google_issuer(issuer):
        return await verify_google_token_raw(token, settings)
    if _is_microsoft_issuer(issuer):
        return await verify_microsoft_token_raw(token, settings)

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unsupported token issuer",
    )


def build_current_user(token_payload: dict, settings: Settings) -> dict:
    issuer = token_payload.get("iss")
    if isinstance(issuer, str) and _is_google_issuer(issuer):
        return build_google_user(token_payload, settings)
    return build_microsoft_user(token_payload)


async def verify_token(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict:
    return await verify_token_raw(credentials.credentials, settings)


async def get_current_user(
    token_payload: Annotated[dict, Depends(verify_token)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict:
    return build_current_user(token_payload, settings)


CurrentUser = Annotated[dict, Depends(get_current_user)]
