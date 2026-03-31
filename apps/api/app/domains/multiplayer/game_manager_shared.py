"""Shared constants and helpers for multiplayer game manager modules."""

from datetime import UTC, datetime

ROUND_DURATION_SECONDS = 120
RECONNECT_TIMEOUT_SECONDS = 30
ABANDON_TIMEOUT_SECONDS = 60
COUNTDOWN_SECONDS = 3
LOBBY_EXPIRY_WARNING_SECONDS = 300
RATE_LIMIT_MAX = 10
RATE_LIMIT_WINDOW = 1.0
REMATCH_LOCK_TTL_SECONDS = 120


def iso_utc(value: datetime) -> str:
    dt = value if value.tzinfo else value.replace(tzinfo=UTC)
    return dt.astimezone(UTC).isoformat().replace("+00:00", "Z")
