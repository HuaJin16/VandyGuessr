"""Seed leaderboard users and completed games for local database.

Run from apps/api/:
    python -m scripts.seed_leaderboard
"""

import asyncio
import copy
import json
import random
from datetime import UTC, datetime
from pathlib import Path

from bson import ObjectId

from app.core.db.mongo import close_mongo_connection, connect_to_mongo, get_database
from app.domains.games.entities import GameEntity
from app.domains.users.entities import UserEntity

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "leaderboard_seed.json"
SEED_COUNT = 50
ROUNDS_PER_GAME = 5
SEED_IMAGES_PER_ENV = 3
SEED_IMAGE_PREFIX = "seed-image"
START_TOTAL_SCORE = 22000
TOTAL_SCORE_STEP = 200


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


def _build_round_scores(
    total_score: int,
    rounds: int,
    rng: random.Random,
) -> list[int]:
    total_score = max(0, min(total_score, rounds * 5000))
    remaining = total_score
    scores: list[int] = []

    for round_index in range(rounds):
        remaining_rounds = rounds - round_index - 1
        max_remaining = remaining_rounds * 5000
        min_score = max(0, remaining - max_remaining)
        max_score = min(5000, remaining)
        if remaining_rounds == 0:
            score = remaining
        else:
            score = rng.randint(min_score, max_score)
        scores.append(score)
        remaining -= score

    rng.shuffle(scores)
    return scores


def _build_seed_images(now: datetime) -> dict[str, list[dict]]:
    base_coords = {
        "indoor": (36.1462, -86.8041),
        "outdoor": (36.1447, -86.8027),
    }
    images: dict[str, list[dict]] = {"indoor": [], "outdoor": []}

    for environment in ("indoor", "outdoor"):
        base_lat, base_lng = base_coords[environment]
        for index in range(SEED_IMAGES_PER_ENV):
            image_id = ObjectId()
            offset = (index + 1) * 0.0002
            images[environment].append(
                {
                    "_id": image_id,
                    "url": f"https://example.com/{SEED_IMAGE_PREFIX}-{environment}-{index + 1:02d}.jpg",
                    "latitude": base_lat + offset,
                    "longitude": base_lng - offset,
                    "format": "jpg",
                    "environment": environment,
                    "original_filename": f"{SEED_IMAGE_PREFIX}-{environment}-{index + 1:02d}.jpg",
                    "file_size": 150000,
                    "location_name": f"Seed {environment.title()} {index + 1:02d}",
                    "created_at": now,
                }
            )

    return images


async def _seed_images(images_collection, now: datetime) -> dict[str, list[dict]]:
    await images_collection.delete_many(
        {"original_filename": {"$regex": f"^{SEED_IMAGE_PREFIX}-"}}
    )
    images_by_env = _build_seed_images(now)
    seed_docs = [doc for env_docs in images_by_env.values() for doc in env_docs]
    if seed_docs:
        await images_collection.insert_many(seed_docs)
    return images_by_env


def _build_rounds(
    images_by_env: dict[str, list[dict]],
    round_scores: list[int],
    rng: random.Random,
) -> list[dict]:
    environment_order = ["indoor", "indoor", "outdoor", "outdoor", "outdoor"]
    rng.shuffle(environment_order)
    rounds: list[dict] = []

    for round_id, (environment, score) in enumerate(
        zip(environment_order, round_scores, strict=True), start=1
    ):
        image_doc = rng.choice(images_by_env[environment])
        actual_lat = image_doc["latitude"]
        actual_lng = image_doc["longitude"]
        guess_lat = actual_lat + rng.uniform(-0.0003, 0.0003)
        guess_lng = actual_lng + rng.uniform(-0.0003, 0.0003)
        rounds.append(
            {
                "round_id": round_id,
                "image_id": str(image_doc["_id"]),
                "image_url": image_doc["url"],
                "actual_lat": actual_lat,
                "actual_lng": actual_lng,
                "guess": {"lat": guess_lat, "lng": guess_lng},
                "distance_meters": round(rng.uniform(10, 250), 2),
                "score": score,
                "location_name": image_doc["location_name"],
            }
        )

    return rounds


def _build_game(
    seed_game: dict,
    user_id: str,
    rounds: list[dict],
    now: datetime,
) -> GameEntity:
    total_score = sum(round_data["score"] for round_data in rounds)
    game_data = copy.deepcopy(seed_game)
    game_data.update(
        {
            "user_id": user_id,
            "rounds": rounds,
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
    images_collection = db.images

    now = datetime.now(UTC)
    images_by_env = await _seed_images(images_collection, now)
    rng = random.Random(42)

    for index in range(SEED_COUNT):
        total_score = START_TOTAL_SCORE - (index * TOTAL_SCORE_STEP)
        round_scores = _build_round_scores(total_score, ROUNDS_PER_GAME, rng)
        rounds = _build_rounds(images_by_env, round_scores, rng)

        user_entity, user_id = _build_user(seed_user, index)
        user_doc = user_entity.model_dump(by_alias=True, exclude={"id"})
        await users_collection.update_one(
            {"microsoft_oid": user_id},
            {"$set": user_doc},
            upsert=True,
        )

        await games_collection.delete_many({"user_id": user_id})
        game_entity = _build_game(seed_game, user_id, rounds, now)
        game_doc = game_entity.model_dump(by_alias=True, exclude={"id"})
        await games_collection.insert_one(game_doc)

    await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(seed())
