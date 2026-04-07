"""Shared constants and helpers for multiplayer game manager modules."""

from datetime import UTC, datetime

from pydantic import ValidationError

from app.domains.games.entities import RoundTilesEntity

ROUND_DURATION_SECONDS = 120
RECONNECT_TIMEOUT_SECONDS = 30
ABANDON_TIMEOUT_SECONDS = 60
COUNTDOWN_SECONDS = 3
LOBBY_EXPIRY_WARNING_SECONDS = 300
RATE_LIMIT_MAX = 10
RATE_LIMIT_WINDOW = 1.0
REMATCH_LOCK_TTL_SECONDS = 120
READY_BARRIER_TTL_SECONDS = 3600
READY_ADVANCE_LOCK_TTL_SECONDS = 30


def iso_utc(value: datetime) -> str:
    dt = value if value.tzinfo else value.replace(tzinfo=UTC)
    return dt.astimezone(UTC).isoformat().replace("+00:00", "Z")


def round_tiles_payload(payload: object) -> dict | None:
    if not isinstance(payload, dict):
        return None

    try:
        entity = RoundTilesEntity.model_validate(payload)
    except (ValidationError, KeyError, TypeError, ValueError):
        return None

    pano = entity.base_pano_data
    return {
        "version": entity.version,
        "baseUrl": entity.base_url,
        "tileUrlTemplate": entity.tile_url_template,
        "originalWidth": entity.original_width,
        "originalHeight": entity.original_height,
        "aspectRatio": entity.aspect_ratio,
        "basePanoData": {
            "fullWidth": pano.full_width,
            "fullHeight": pano.full_height,
            "croppedWidth": pano.cropped_width,
            "croppedHeight": pano.cropped_height,
            "croppedX": pano.cropped_x,
            "croppedY": pano.cropped_y,
        },
        "levels": [
            {
                "level": level.level,
                "width": level.width,
                "height": level.height,
                "cols": level.cols,
                "rows": level.rows,
            }
            for level in entity.levels
        ],
    }
