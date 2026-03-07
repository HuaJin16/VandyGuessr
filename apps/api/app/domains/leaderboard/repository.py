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

    def _build_base_match(
        self,
        start: datetime | None,
        end: datetime | None,
    ) -> dict:
        match: dict = {"status": "completed"}
        if start and end:
            match["created_at"] = {"$gte": start, "$lt": end}
        elif start:
            match["created_at"] = {"$gte": start}
        elif end:
            match["created_at"] = {"$lt": end}
        return match

    @staticmethod
    def _unwind_and_filter_rounds() -> list[dict]:
        return [
            {"$unwind": "$rounds"},
            {
                "$match": {
                    "rounds.skipped": {"$ne": True},
                    "rounds.score": {"$ne": None},
                }
            },
        ]

    @staticmethod
    def _env_lookup_stages(mode: str) -> list[dict]:
        return [
            {
                "$lookup": {
                    "from": "images",
                    "let": {"image_id": "$rounds.image_id"},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {
                                    "$eq": ["$_id", {"$toObjectId": "$$image_id"}]
                                },
                                "environment": mode,
                            }
                        }
                    ],
                    "as": "image",
                }
            },
            {"$unwind": "$image"},
        ]

    @staticmethod
    def _round_group_stage() -> dict:
        return {
            "$group": {
                "_id": "$user_id",
                "total_points": {"$sum": "$rounds.score"},
                "avg_score": {"$avg": "$rounds.score"},
                "rounds_played": {"$sum": 1},
                "game_ids": {"$addToSet": "$_id"},
            }
        }

    @staticmethod
    def _games_played_stage() -> dict:
        return {"$addFields": {"games_played": {"$size": "$game_ids"}}}

    def _build_round_pipeline(
        self,
        mode: str,
        start: datetime | None,
        end: datetime | None,
    ) -> list[dict]:
        pipeline: list[dict] = [{"$match": self._build_base_match(start, end)}]
        pipeline.extend(self._unwind_and_filter_rounds())
        if mode != "all":
            pipeline.extend(self._env_lookup_stages(mode))
        pipeline.extend([self._round_group_stage(), self._games_played_stage()])
        return pipeline

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
                    "rounds_played": 1,
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
        pipeline = [
            *self._build_round_pipeline(mode, start, end),
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
        pipeline = [
            *self._build_round_pipeline(mode, start, end),
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
        pipeline = [
            *self._build_round_pipeline(mode, start, end),
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
            *self._build_round_pipeline(mode, start, end),
            {"$match": ahead_match},
            {"$count": "ahead"},
        ]

        results = await self.collection.aggregate(pipeline).to_list(length=1)
        return results[0]["ahead"] if results else 0
