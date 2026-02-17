"""Seed leaderboard users and completed games.

Run from apps/api/:
    python -m scripts.seed_leaderboard
"""

import asyncio
import copy
import json
from datetime import UTC, datetime
from pathlib import Path

from app.core.db.mongo import close_mongo_connection, connect_to_mongo, get_database
from app.domains.games.entities import GameEntity
from app.domains.users.entities import UserEntity

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "leaderboard_seed.json"
SEED_COUNT = 50
START_SCORE = 5000


def _load_seed_data() -> dict:
    with DATA_PATH.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    if "user" not in data or "game" not in data:
        raise ValueError("Seed file must include 'user' and 'game' templates.")

    return data


def _build_user(seed_user: dict, index: int) -> tuple[UserEntity, str]:
    user_number = index + 1
    user_id = f"leaderboard-seed-{user_number:03d}"
    user_data = {
        **seed_user,
        "microsoft_oid": user_id,
        "email": f"seed{user_number:03d}@vanderbilt.edu",
        "username": f"seed{user_number:03d}",
        "name": f"Seed User {user_number:03d}",
    }

    return UserEntity(**user_data), user_id


def _build_game(
    seed_game: dict,
    user_id: str,
    total_score: int,
    now: datetime,
) -> GameEntity:
    game_data = copy.deepcopy(seed_game)
    game_data.update(
        {
            "user_id": user_id,
            "total_score": total_score,
            "status": "completed",
            "created_at": now,
            "last_activity_at": now,
        }
    )

    return GameEntity(**game_data)


async def seed() -> None:
    seed_data = _load_seed_data()
    seed_user = seed_data["user"]
    seed_game = seed_data["game"]

    await connect_to_mongo()
    db = get_database()
    users_collection = db.users
    games_collection = db.games

    for index in range(SEED_COUNT):
        score = START_SCORE - index
        now = datetime.now(UTC)

        user_entity, user_id = _build_user(seed_user, index)
        user_doc = user_entity.model_dump(by_alias=True, exclude={"id"})
        await users_collection.update_one(
            {"microsoft_oid": user_id},
            {"$set": user_doc},
            upsert=True,
        )

        await games_collection.delete_many({"user_id": user_id})
        game_entity = _build_game(seed_game, user_id, score, now)
        game_doc = game_entity.model_dump(by_alias=True, exclude={"id"})
        await games_collection.insert_one(game_doc)

    await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(seed())
