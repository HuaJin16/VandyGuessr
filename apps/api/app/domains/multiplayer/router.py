"""Multiplayer HTTP and WebSocket endpoints."""

from fastapi import APIRouter, HTTPException, WebSocket

from app.container import deps
from app.core.auth import CurrentUser
from app.domains.multiplayer.connection_manager import ConnectionManager
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


def _to_response(doc: dict) -> MultiplayerGameResponse:
    """Map a raw multiplayer game document to the API response model."""
    players = [
        MultiplayerPlayerResponse(
            userId=p["user_id"],
            name=p["name"],
            avatarUrl=p.get("avatar_url"),
            totalScore=p.get("total_score", 0),
            status=p.get("status", "connected"),
            joinedAt=p["joined_at"].isoformat() + "Z"
            if hasattr(p["joined_at"], "isoformat")
            else str(p["joined_at"]),
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
                    submittedAt=g["submitted_at"].isoformat() + "Z"
                    if hasattr(g["submitted_at"], "isoformat")
                    else str(g["submitted_at"]),
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
                startedAt=rd["started_at"].isoformat() + "Z"
                if has_started and hasattr(rd["started_at"], "isoformat")
                else None,
                expiresAt=rd["expires_at"].isoformat() + "Z"
                if rd.get("expires_at") and hasattr(rd["expires_at"], "isoformat")
                else None,
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
        createdAt=doc["created_at"].isoformat() + "Z"
        if hasattr(doc["created_at"], "isoformat")
        else str(doc["created_at"]),
        startedAt=doc["started_at"].isoformat() + "Z"
        if doc.get("started_at") and hasattr(doc["started_at"], "isoformat")
        else None,
        lastActivityAt=doc["last_activity_at"].isoformat() + "Z"
        if hasattr(doc["last_activity_at"], "isoformat")
        else str(doc["last_activity_at"]),
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
) -> MultiplayerGameResponse:
    try:
        doc = await service.join_game(
            user_id=_user_id(current_user),
            name=current_user.get("name") or "Player",
            avatar_url=None,
            code=body.code,
        )
    except MultiplayerError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message) from e
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
