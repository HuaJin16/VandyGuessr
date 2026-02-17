"""Multiplayer HTTP and WebSocket endpoints."""

from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, WebSocket

from app.container import deps
from app.core.auth import CurrentUser
from app.domains.multiplayer.connection_manager import ConnectionManager
from app.domains.multiplayer.events import ServerEvent
from app.domains.multiplayer.game_manager import GameManager
from app.domains.multiplayer.models import (
    CreateMultiplayerRequest,
    JoinMultiplayerRequest,
    MultiplayerGameResponse,
    MultiplayerGuessResponse,
    MultiplayerPlayerResponse,
    MultiplayerRoundResponse,
)
from app.domains.multiplayer.service import MultiplayerError, MultiplayerService
from app.domains.multiplayer.ws import multiplayer_ws

router = APIRouter(prefix="/multiplayer", tags=["multiplayer"])


def _iso_utc(value: object) -> str:
    if not isinstance(value, datetime):
        return str(value)

    dt = value if value.tzinfo else value.replace(tzinfo=UTC)
    return dt.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _to_response(doc: dict) -> MultiplayerGameResponse:
    """Map a raw multiplayer game document to the API response model."""
    players = [
        MultiplayerPlayerResponse(
            userId=p["user_id"],
            name=p["name"],
            avatarUrl=p.get("avatar_url"),
            totalScore=p.get("total_score", 0),
            status=p.get("status", "connected"),
            joinedAt=_iso_utc(p["joined_at"]),
        )
        for p in doc["players"]
    ]

    rounds = []
    for rd in doc["rounds"]:
        guesses = None
        if rd.get("guesses"):
            guesses = {
                uid: MultiplayerGuessResponse(
                    lat=g["lat"],
                    lng=g["lng"],
                    distanceMeters=g["distance_meters"],
                    score=g["score"],
                    submittedAt=_iso_utc(g["submitted_at"]),
                )
                for uid, g in rd["guesses"].items()
            }

        # Only expose actual location and image for resolved rounds
        has_started = rd.get("started_at") is not None
        has_resolved = rd.get("_resolved", False)

        rounds.append(
            MultiplayerRoundResponse(
                roundId=rd["round_id"],
                imageUrl=None,  # Never exposed in REST responses
                actual={"lat": rd["actual_lat"], "lng": rd["actual_lng"]}
                if has_resolved
                else None,
                locationName=rd.get("location_name") if has_resolved else None,
                startedAt=_iso_utc(rd["started_at"]) if has_started else None,
                expiresAt=_iso_utc(rd["expires_at"]) if rd.get("expires_at") else None,
                guesses=guesses if has_resolved else None,
            )
        )

    mode = doc["mode"]
    if isinstance(mode, dict):
        mode_dict = mode
    else:
        mode_dict = (
            mode.model_dump() if hasattr(mode, "model_dump") else {"environment": "any"}
        )

    return MultiplayerGameResponse(
        id=str(doc["_id"]),
        hostId=doc["host_id"],
        inviteCode=doc["invite_code"],
        status=doc["status"],
        mode=mode_dict,
        players=players,
        rounds=rounds,
        currentRound=doc.get("current_round", 0),
        createdAt=_iso_utc(doc["created_at"]),
        startedAt=_iso_utc(doc["started_at"]) if doc.get("started_at") else None,
        lastActivityAt=_iso_utc(doc["last_activity_at"]),
    )


def _user_id(user: dict) -> str:
    return user["oid"]


@router.post("/create", response_model=MultiplayerGameResponse)
async def create_game(
    body: CreateMultiplayerRequest,
    current_user: CurrentUser,
    service: MultiplayerService = deps(MultiplayerService),
) -> MultiplayerGameResponse:
    try:
        doc = await service.create_game(
            host_id=_user_id(current_user),
            host_name=current_user.get("name") or "Player",
            avatar_url=None,
            environment=body.environment,
        )
    except MultiplayerError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message) from e
    return _to_response(doc)


@router.post("/join", response_model=MultiplayerGameResponse)
async def join_game(
    body: JoinMultiplayerRequest,
    current_user: CurrentUser,
    service: MultiplayerService = deps(MultiplayerService),
    connection_manager: ConnectionManager = deps(ConnectionManager),
) -> MultiplayerGameResponse:
    try:
        doc, joined_player = await service.join_game(
            user_id=_user_id(current_user),
            name=current_user.get("name") or "Player",
            avatar_url=None,
            code=body.code,
        )
    except MultiplayerError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message) from e

    if joined_player:
        await connection_manager.broadcast(
            doc["_id"],
            {
                "type": ServerEvent.PLAYER_JOINED,
                "player": {
                    "userId": joined_player.user_id,
                    "name": joined_player.name,
                    "avatarUrl": joined_player.avatar_url,
                },
                "playerCount": len(doc["players"]),
            },
        )

    return _to_response(doc)


@router.get("/active", response_model=MultiplayerGameResponse | None)
async def get_active_game(
    current_user: CurrentUser,
    service: MultiplayerService = deps(MultiplayerService),
) -> MultiplayerGameResponse | None:
    doc = await service.get_active_game(_user_id(current_user))
    if not doc:
        return None
    return _to_response(doc)


@router.get("/{game_id}", response_model=MultiplayerGameResponse)
async def get_game(
    game_id: str,
    current_user: CurrentUser,
    service: MultiplayerService = deps(MultiplayerService),
) -> MultiplayerGameResponse:
    try:
        doc = await service.get_game(game_id, _user_id(current_user))
    except MultiplayerError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message) from e
    return _to_response(doc)


@router.websocket("/{game_id}/ws")
async def websocket_endpoint(
    ws: WebSocket,
    game_id: str,
    service: MultiplayerService = deps(MultiplayerService),
    connection_manager: ConnectionManager = deps(ConnectionManager),
    game_manager: GameManager = deps(GameManager),
) -> None:
    await multiplayer_ws(ws, game_id, service, connection_manager, game_manager)
