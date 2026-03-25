"""Game HTTP endpoints."""

from fastapi import APIRouter, HTTPException, Query
from pydantic import ValidationError

from app.container import deps
from app.core.auth import CurrentUser
from app.domains.games.difficulty import DEFAULT_DIFFICULTY
from app.domains.games.entities import RoundTilesEntity
from app.domains.games.models import (
    GameModeResponse,
    GameResponse,
    GuessRequest,
    RoundPanoDataResponse,
    RoundResponse,
    RoundTileLevelResponse,
    RoundTilesResponse,
    ScoreDistributionResponse,
    StartGameRequest,
)
from app.domains.games.repository import IGameRepository
from app.domains.games.service import GameError, GameService

router = APIRouter(prefix="/games", tags=["games"])


def _round_tiles_response(payload: object) -> RoundTilesResponse | None:
    if not isinstance(payload, dict):
        return None
    try:
        entity = RoundTilesEntity.model_validate(payload)
    except (ValidationError, KeyError, TypeError, ValueError):
        return None
    pano = entity.base_pano_data
    return RoundTilesResponse(
        version=entity.version,
        baseUrl=entity.base_url,
        tileUrlTemplate=entity.tile_url_template,
        originalWidth=entity.original_width,
        originalHeight=entity.original_height,
        aspectRatio=entity.aspect_ratio,
        basePanoData=RoundPanoDataResponse(
            fullWidth=pano.full_width,
            fullHeight=pano.full_height,
            croppedWidth=pano.cropped_width,
            croppedHeight=pano.cropped_height,
            croppedX=pano.cropped_x,
            croppedY=pano.cropped_y,
        ),
        levels=[
            RoundTileLevelResponse(
                level=lvl.level,
                width=lvl.width,
                height=lvl.height,
                cols=lvl.cols,
                rows=lvl.rows,
            )
            for lvl in entity.levels
        ],
    )


def _to_response(doc: dict) -> GameResponse:
    """Map a raw game document to the API response model."""
    rounds = []
    for rd in doc["rounds"]:
        has_guess = rd.get("guess") is not None
        rounds.append(
            RoundResponse(
                roundId=rd["round_id"],
                imageId=rd["image_id"],
                imageUrl=rd["image_url"],
                imageTiles=_round_tiles_response(rd.get("image_tiles")),
                actual=(
                    {"lat": rd["actual_lat"], "lng": rd["actual_lng"]}
                    if has_guess or rd.get("skipped")
                    else None
                ),
                guess=rd.get("guess"),
                distanceMeters=rd.get("distance_meters"),
                score=rd.get("score"),
                startedAt=rd["started_at"].isoformat() + "Z"
                if rd.get("started_at")
                else None,
                expiresAt=rd["expires_at"].isoformat() + "Z"
                if rd.get("expires_at")
                else None,
                guessedAt=rd["guessed_at"].isoformat() + "Z"
                if rd.get("guessed_at")
                else None,
                skipped=rd.get("skipped", False),
                location_name=rd.get("location_name"),
            )
        )

    mode = doc["mode"]
    return GameResponse(
        id=str(doc["_id"]),
        userId=doc["user_id"],
        mode=GameModeResponse(
            timed=mode["timed"],
            environment=mode["environment"],
            daily=mode["daily"],
            difficulty=mode.get("difficulty", DEFAULT_DIFFICULTY),
        ),
        status=doc["status"],
        rounds=rounds,
        totalScore=doc["total_score"],
        createdAt=doc["created_at"].isoformat() + "Z",
        lastActivityAt=doc["last_activity_at"].isoformat() + "Z",
    )


def _user_id(user: dict) -> str:
    return user["oid"]


@router.post("/start", response_model=GameResponse)
async def start_game(
    body: StartGameRequest,
    current_user: CurrentUser,
    service: GameService = deps(GameService),
) -> GameResponse:
    try:
        doc = await service.start_game(
            user_id=_user_id(current_user),
            timed=body.mode.timed,
            environment=body.mode.environment,
            daily=body.mode.daily,
            difficulty=body.mode.difficulty,
        )
    except GameError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message) from e
    return _to_response(doc)


@router.get("/active", response_model=GameResponse | None)
async def get_active_game(
    current_user: CurrentUser,
    service: GameService = deps(GameService),
) -> GameResponse | None:
    doc = await service.find_active_game(_user_id(current_user))
    if not doc:
        return None
    return _to_response(doc)


@router.get("", response_model=list[GameResponse])
async def list_games(
    current_user: CurrentUser,
    status: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    service: GameService = deps(GameService),
) -> list[GameResponse]:
    docs = await service.list_games(
        user_id=_user_id(current_user),
        status=status,
        limit=limit,
        offset=offset,
    )
    return [_to_response(d) for d in docs]


@router.get(
    "/images/{image_id}/score-distribution",
    response_model=ScoreDistributionResponse,
)
async def get_score_distribution(
    image_id: str,
    _current_user: CurrentUser,
    score: int = Query(ge=0, le=5000),
    repo: IGameRepository = deps(IGameRepository),
) -> ScoreDistributionResponse:
    result = await repo.compute_score_distribution(image_id, score)
    return ScoreDistributionResponse(**result)


@router.get("/{game_id}", response_model=GameResponse)
async def get_game(
    game_id: str,
    current_user: CurrentUser,
    service: GameService = deps(GameService),
) -> GameResponse:
    try:
        doc = await service.get_game(game_id, _user_id(current_user))
    except GameError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message) from e
    return _to_response(doc)


@router.post("/{game_id}/round/{round_number}/guess", response_model=GameResponse)
async def submit_guess(
    game_id: str,
    round_number: int,
    body: GuessRequest,
    current_user: CurrentUser,
    service: GameService = deps(GameService),
) -> GameResponse:
    try:
        doc = await service.submit_guess(
            game_id=game_id,
            user_id=_user_id(current_user),
            round_number=round_number,
            lat=body.lat,
            lng=body.lng,
        )
    except GameError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message) from e
    return _to_response(doc)


@router.post("/{game_id}/end", response_model=GameResponse)
async def end_game(
    game_id: str,
    current_user: CurrentUser,
    service: GameService = deps(GameService),
) -> GameResponse:
    try:
        doc = await service.end_game(game_id, _user_id(current_user))
    except GameError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message) from e
    return _to_response(doc)
