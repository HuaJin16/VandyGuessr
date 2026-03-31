"""Daily challenge persistence and deterministic image selection."""

import hashlib
import random
from datetime import UTC, datetime
from typing import Protocol
from zoneinfo import ZoneInfo

from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field

DAILY_SALT = "vandyguessr-daily-2025"
ROUNDS_PER_GAME = 5
CHICAGO_TZ = ZoneInfo("America/Chicago")


class DailyChallengeEntity(BaseModel):
    """A cached set of image IDs for a single calendar day (CST)."""

    id: str | None = Field(default=None, alias="_id")
    date: str  # YYYY-MM-DD in CST
    image_ids: list[str]
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    model_config = {"populate_by_name": True}


class IDailyChallengeRepository(Protocol):
    async def find_by_date(self, date_str: str) -> dict | None: ...

    async def create(self, challenge: DailyChallengeEntity) -> str: ...


class DailyChallengeRepository:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.collection = db.daily_challenges

    async def ensure_indexes(self) -> None:
        await self.collection.create_index("date", unique=True)

    async def find_by_date(self, date_str: str) -> dict | None:
        return await self.collection.find_one({"date": date_str})

    async def create(self, challenge: DailyChallengeEntity) -> str:
        result = await self.collection.insert_one(
            challenge.model_dump(by_alias=True, exclude={"id"})
        )
        return str(result.inserted_id)


def pick_daily_images(date_str: str, all_image_ids: list[str]) -> list[str]:
    """Deterministically pick ROUNDS_PER_GAME images for a given date.

    Uses a seeded RNG so every caller gets the same result for the same day.
    """
    seed = hashlib.sha256(f"{DAILY_SALT}:{date_str}".encode()).hexdigest()
    rng = random.Random(seed)
    pool = list(all_image_ids)
    rng.shuffle(pool)
    return pool[:ROUNDS_PER_GAME]


def today_cst() -> str:
    """Return today's date string in America/Chicago."""
    return datetime.now(tz=CHICAGO_TZ).strftime("%Y-%m-%d")
