"""WebSocket endpoint for multiplayer gameplay."""

import asyncio
from datetime import UTC, datetime

import structlog
from fastapi import WebSocket, WebSocketDisconnect
from jose import JWTError, jwt

from app.config import get_settings
from app.core.auth.microsoft import get_current_user, get_jwks, get_signing_key
from app.domains.multiplayer.connection_manager import ConnectionManager
from app.domains.multiplayer.events import ServerEvent
from app.domains.multiplayer.game_manager import GameManager
from app.domains.multiplayer.service import MultiplayerError, MultiplayerService

logger = structlog.get_logger()

SUPPORTED_VERSIONS = {"1"}
TOKEN_EXPIRY_WARNING_SECONDS = 300
TOKEN_EXPIRY_GRACE_SECONDS = 60


async def _authenticate(token: str) -> dict | None:
    """Validate a JWT and return the user dict, or None on failure."""
    settings = get_settings()
    if not settings.microsoft_client_id:
        return None
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
        return await get_current_user(payload)
    except (JWTError, Exception):
        return None


def _token_exp(token: str) -> int | None:
    """Extract the exp claim without verifying the token."""
    try:
        claims = jwt.get_unverified_claims(token)
        return claims.get("exp")
    except Exception:
        return None


async def multiplayer_ws(
    ws: WebSocket,
    game_id: str,
    service: MultiplayerService,
    connection_manager: ConnectionManager,
    game_manager: GameManager,
) -> None:
    token = ws.query_params.get("token")
    version = ws.query_params.get("v")

    if version not in SUPPORTED_VERSIONS:
        await ws.close(code=4012, reason="Unsupported protocol version")
        return

    if not token:
        await ws.close(code=4001, reason="Authentication failed")
        return

    user = await _authenticate(token)
    if not user:
        await ws.close(code=4001, reason="Authentication failed")
        return

    user_id: str = user["oid"]

    try:
        doc = await service.get_game(game_id, user_id)
    except MultiplayerError:
        await ws.close(code=4004, reason="Game not found")
        return

    if not doc:
        await ws.close(code=4004, reason="Game not found")
        return

    if doc["status"] in ("completed", "cancelled", "abandoned"):
        await ws.close(code=4010, reason="Game is not active")
        return

    is_participant = any(p["user_id"] == user_id for p in doc["players"])
    if not is_participant:
        await ws.close(code=4003, reason="Not a participant")
        return

    await ws.accept()

    await connection_manager.connect(game_id, user_id, ws)
    await game_manager.on_player_connected(game_id, user_id)

    # Schedule token expiry warning
    exp = _token_exp(token)
    expiry_task: asyncio.Task | None = None
    if exp:
        expiry_task = asyncio.create_task(
            _token_expiry_watcher(ws, connection_manager, game_id, user_id, exp)
        )

    try:
        while True:
            raw = await ws.receive_text()

            # Handle token refresh at the WS layer
            import json

            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                data = {}

            if data.get("type") == "refresh_token":
                new_token = data.get("token")
                if not new_token or not isinstance(new_token, str):
                    await connection_manager.send_to_player(
                        game_id,
                        user_id,
                        {
                            "type": ServerEvent.ERROR,
                            "code": "MISSING_FIELD",
                            "message": "token is required for refresh_token",
                        },
                    )
                    continue

                new_user = await _authenticate(new_token)
                if not new_user or new_user["oid"] != user_id:
                    await connection_manager.send_to_player(
                        game_id,
                        user_id,
                        {
                            "type": ServerEvent.ERROR,
                            "code": "INVALID_FIELD",
                            "message": "Invalid refresh token",
                        },
                    )
                    continue

                # Restart expiry watcher with new token
                if expiry_task:
                    expiry_task.cancel()
                new_exp = _token_exp(new_token)
                if new_exp:
                    expiry_task = asyncio.create_task(
                        _token_expiry_watcher(
                            ws, connection_manager, game_id, user_id, new_exp
                        )
                    )
                continue

            await game_manager.handle_message(game_id, user_id, raw)

    except WebSocketDisconnect:
        pass
    except Exception:
        logger.exception("ws_error", game_id=game_id, user_id=user_id)
    finally:
        if expiry_task:
            expiry_task.cancel()
        disconnected = await connection_manager.disconnect(game_id, user_id, ws)
        if disconnected:
            await game_manager.on_player_disconnected(game_id, user_id)


async def _token_expiry_watcher(
    ws: WebSocket,
    cm: ConnectionManager,
    game_id: str,
    user_id: str,
    exp: int,
) -> None:
    """Send a token_expiring warning and close if no refresh is received."""
    try:
        now = datetime.now(UTC).timestamp()
        warn_at = exp - TOKEN_EXPIRY_WARNING_SECONDS
        if warn_at > now:
            await asyncio.sleep(warn_at - now)

        await cm.send_to_player(
            game_id,
            user_id,
            {"type": ServerEvent.TOKEN_EXPIRING},
        )

        await asyncio.sleep(TOKEN_EXPIRY_GRACE_SECONDS)

        # If we reach here, the token was not refreshed
        from starlette.websockets import WebSocketState

        if ws.client_state == WebSocketState.CONNECTED:
            await ws.close(code=4001, reason="Token expired")
    except asyncio.CancelledError:
        pass
