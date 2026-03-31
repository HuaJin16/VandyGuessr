"""Leaderboard service for ranking and caching."""

import json
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import redis.asyncio as redis
import structlog

from app.domains.leaderboard.repository import ILeaderboardRepository

logger = structlog.get_logger()

CHICAGO_TZ = ZoneInfo("America/Chicago")
CACHE_TTLS = {"daily": 300, "weekly": 300, "alltime": 900}


class LeaderboardError(Exception):
    def __init__(self, message: str, status_code: int = 400) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class LeaderboardService:
    def __init__(
        self,
        leaderboard_repository: ILeaderboardRepository,
        redis_client: redis.Redis,
    ) -> None:
        self.leaderboard_repo = leaderboard_repository
        self.redis = redis_client

    @staticmethod
    def _now_local() -> datetime:
        return datetime.now(tz=CHICAGO_TZ)

    async def get_leaderboard(
        self,
        user_id: str,
        timeframe: str,
        mode: str,
        limit: int,
        offset: int,
    ) -> dict:
        start, end = self._timeframe_bounds(timeframe)
        cache_key = f"lb:v3:{timeframe}:{mode}:{offset}:{limit}"
        cached = await self._read_cache(cache_key)

        if cached is None:
            raw_entries, total_count = await self.leaderboard_repo.get_leaderboard_page(
                mode=mode,
                start=start,
                end=end,
                limit=limit,
                offset=offset,
            )
            entries = [
                self._map_entry(raw, offset + idx + 1)
                for idx, raw in enumerate(raw_entries)
            ]
            await self._write_cache(
                cache_key,
                {"entries": entries, "total_count": total_count},
                self._cache_ttl(timeframe),
            )
        else:
            entries = cached["entries"]
            total_count = cached["total_count"]

        user_entry = await self._build_user_entry(user_id, mode, start, end)
        context_entries = await self._build_context_entries(
            user_entry,
            entries,
            mode,
            start,
            end,
        )

        return {
            "entries": entries,
            "user_entry": user_entry,
            "context_entries": context_entries,
            "total_count": total_count,
        }

    def _timeframe_bounds(
        self, timeframe: str
    ) -> tuple[datetime | None, datetime | None]:
        if timeframe == "alltime":
            return None, None

        now_cst = self._now_local()
        if timeframe == "daily":
            start_cst = now_cst.replace(hour=0, minute=0, second=0, microsecond=0)
            end_cst = start_cst + timedelta(days=1)
        else:
            end_cst = now_cst
            start_cst = end_cst - timedelta(days=7)

        start_utc = start_cst.astimezone(UTC).replace(tzinfo=None)
        end_utc = end_cst.astimezone(UTC).replace(tzinfo=None)
        return start_utc, end_utc

    @staticmethod
    def _cache_ttl(timeframe: str) -> int:
        return CACHE_TTLS.get(timeframe, 300)

    @staticmethod
    def _map_entry(raw: dict, rank: int) -> dict:
        return {
            "rank": rank,
            "user_id": str(raw["user_doc_id"]),
            "name": raw["name"],
            "username": raw["username"],
            "total_points": int(raw["total_points"]),
            "avg_score": float(raw["avg_score"]),
            "games_played": int(raw["games_played"]),
            "rounds_played": int(raw["rounds_played"]),
        }

    async def _build_user_entry(
        self,
        user_id: str,
        mode: str,
        start: datetime | None,
        end: datetime | None,
    ) -> dict | None:
        raw = await self.leaderboard_repo.get_user_entry(
            user_id=user_id,
            mode=mode,
            start=start,
            end=end,
        )
        if not raw:
            return None

        ahead = await self.leaderboard_repo.count_users_ahead(
            user_id=user_id,
            avg_score=float(raw["avg_score"]),
            total_points=int(raw["total_points"]),
            games_played=int(raw["games_played"]),
            mode=mode,
            start=start,
            end=end,
        )
        return self._map_entry(raw, ahead + 1)

    async def _build_context_entries(
        self,
        user_entry: dict | None,
        entries: list[dict],
        mode: str,
        start: datetime | None,
        end: datetime | None,
    ) -> list[dict]:
        if not user_entry:
            return []

        in_page = any(entry["user_id"] == user_entry["user_id"] for entry in entries)
        if in_page:
            return []

        user_rank = user_entry["rank"]
        start_offset = max(user_rank - 2, 0)
        raw_entries = await self.leaderboard_repo.get_entries_by_offset(
            mode=mode,
            start=start,
            end=end,
            offset=start_offset,
            limit=3,
        )
        mapped = [
            self._map_entry(raw, start_offset + idx + 1)
            for idx, raw in enumerate(raw_entries)
        ]
        return [entry for entry in mapped if entry["user_id"] != user_entry["user_id"]]

    async def _read_cache(self, key: str) -> dict | None:
        try:
            cached = await self.redis.get(key)
        except Exception as exc:
            logger.warning("leaderboard_cache_read_failed", error=str(exc))
            return None

        if not cached:
            return None

        try:
            data = json.loads(cached)
        except json.JSONDecodeError:
            return None

        if "entries" not in data or "total_count" not in data:
            return None

        return data

    async def _write_cache(self, key: str, payload: dict, ttl: int) -> None:
        try:
            await self.redis.setex(key, ttl, json.dumps(payload))
        except Exception as exc:
            logger.warning("leaderboard_cache_write_failed", error=str(exc))
