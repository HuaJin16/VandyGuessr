"""Leaderboard repository for aggregation queries."""

from datetime import datetime
from typing import Protocol

from motor.motor_asyncio import AsyncIOMotorDatabase


class ILeaderboardRepository(Protocol):
    async def get_leaderboard_page(
        self,
        mode: str,
        start: datetime | None,
        end: datetime | None,
        limit: int,
        offset: int,
    ) -> tuple[list[dict], int]: ...

    async def get_user_entry(
        self,
        user_id: str,
        mode: str,
        start: datetime | None,
        end: datetime | None,
    ) -> dict | None: ...

    async def count_users_ahead(
        self,
        user_id: str,
        avg_score: float,
        total_points: int,
        games_played: int,
        mode: str,
        start: datetime | None,
        end: datetime | None,
    ) -> int: ...

    async def get_entries_by_offset(
        self,
        mode: str,
        start: datetime | None,
        end: datetime | None,
        offset: int,
        limit: int,
    ) -> list[dict]: ...


class LeaderboardRepository:
    """MongoDB implementation for leaderboard aggregation."""

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.collection = db.games

    def _build_match(
        self,
        mode: str,
        start: datetime | None,
        end: datetime | None,
    ) -> dict:
        match: dict = {"status": "completed"}
        if mode != "all":
            match["mode.environment"] = mode
        if start and end:
            match["created_at"] = {"$gte": start, "$lt": end}
        elif start:
            match["created_at"] = {"$gte": start}
        elif end:
            match["created_at"] = {"$lt": end}
        return match

    @staticmethod
    def _group_stage() -> dict:
        return {
            "$group": {
                "_id": "$user_id",
                "total_points": {"$sum": "$total_score"},
                "avg_score": {"$avg": "$total_score"},
                "games_played": {"$sum": 1},
            }
        }

    @staticmethod
    def _sort_stage() -> dict:
        return {
            "$sort": {
                "avg_score": -1,
                "total_points": -1,
                "games_played": -1,
                "_id": 1,
            }
        }

    @staticmethod
    def _lookup_user_stage() -> list[dict]:
        return [
            {
                "$lookup": {
                    "from": "users",
                    "localField": "_id",
                    "foreignField": "microsoft_oid",
                    "as": "user",
                }
            },
            {"$unwind": "$user"},
            {
                "$project": {
                    "_id": 0,
                    "user_oid": "$_id",
                    "user_doc_id": "$user._id",
                    "name": "$user.name",
                    "username": "$user.username",
                    "total_points": 1,
                    "avg_score": 1,
                    "games_played": 1,
                }
            },
        ]

    async def get_leaderboard_page(
        self,
        mode: str,
        start: datetime | None,
        end: datetime | None,
        limit: int,
        offset: int,
    ) -> tuple[list[dict], int]:
        match = self._build_match(mode, start, end)
        pipeline = [
            {"$match": match},
            self._group_stage(),
            self._sort_stage(),
            {
                "$facet": {
                    "entries": [
                        {"$skip": offset},
                        {"$limit": limit},
                        *self._lookup_user_stage(),
                    ],
                    "totalCount": [{"$count": "count"}],
                }
            },
        ]

        results = await self.collection.aggregate(pipeline).to_list(length=1)
        if not results:
            return [], 0

        doc = results[0]
        entries = doc.get("entries", [])
        total_count = doc.get("totalCount", [])
        count_value = total_count[0]["count"] if total_count else 0
        return entries, count_value

    async def get_entries_by_offset(
        self,
        mode: str,
        start: datetime | None,
        end: datetime | None,
        offset: int,
        limit: int,
    ) -> list[dict]:
        match = self._build_match(mode, start, end)
        pipeline = [
            {"$match": match},
            self._group_stage(),
            self._sort_stage(),
            {"$skip": offset},
            {"$limit": limit},
            *self._lookup_user_stage(),
        ]

        return await self.collection.aggregate(pipeline).to_list(length=limit)

    async def get_user_entry(
        self,
        user_id: str,
        mode: str,
        start: datetime | None,
        end: datetime | None,
    ) -> dict | None:
        match = self._build_match(mode, start, end)
        pipeline = [
            {"$match": match},
            self._group_stage(),
            {"$match": {"_id": user_id}},
            *self._lookup_user_stage(),
        ]

        results = await self.collection.aggregate(pipeline).to_list(length=1)
        return results[0] if results else None

    async def count_users_ahead(
        self,
        user_id: str,
        avg_score: float,
        total_points: int,
        games_played: int,
        mode: str,
        start: datetime | None,
        end: datetime | None,
    ) -> int:
        match = self._build_match(mode, start, end)
        ahead_match = {
            "$or": [
                {"avg_score": {"$gt": avg_score}},
                {
                    "avg_score": avg_score,
                    "total_points": {"$gt": total_points},
                },
                {
                    "avg_score": avg_score,
                    "total_points": total_points,
                    "games_played": {"$gt": games_played},
                },
                {
                    "avg_score": avg_score,
                    "total_points": total_points,
                    "games_played": games_played,
                    "_id": {"$lt": user_id},
                },
            ]
        }
        pipeline = [
            {"$match": match},
            self._group_stage(),
            {"$match": ahead_match},
            {"$count": "ahead"},
        ]

        results = await self.collection.aggregate(pipeline).to_list(length=1)
        return results[0]["ahead"] if results else 0
