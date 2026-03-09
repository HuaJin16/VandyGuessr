"""Seed demo mode data: images from disk + realistic leaderboard.

Requires seed_locations to have been run first (for location name resolution).

Run from apps/api/:
    python -m scripts.seed_demo
"""

import asyncio
import math
import os
import random
from datetime import UTC, datetime, timedelta
from pathlib import Path

from bson import ObjectId

from app.config import get_settings
from app.core.db.mongo import close_mongo_connection, connect_to_mongo, get_database
from app.shared.exif import extract_metadata
from app.shared.scoring import _CAMPUS_SIZE, _DECAY_CONSTANT, MAX_SCORE

DEMO_IMAGES_DIR = Path(__file__).resolve().parent.parent / "data" / "demo" / "images"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".heic", ".png"}
DEMO_IMAGE_PREFIX = "demo-"
DEMO_USER_PREFIX = "demo-seed-"

SEED_USER_COUNT = 30
ROUNDS_PER_GAME = 5

# Realistic Vanderbilt-style first/last names
FIRST_NAMES = [
    "Alex",
    "Jordan",
    "Taylor",
    "Morgan",
    "Casey",
    "Riley",
    "Avery",
    "Quinn",
    "Reese",
    "Parker",
    "Blake",
    "Drew",
    "Cameron",
    "Skyler",
    "Finley",
    "Harper",
    "Rowan",
    "Sawyer",
    "Emery",
    "Kendall",
    "Maya",
    "Ethan",
    "Sophia",
    "Liam",
    "Olivia",
    "Noah",
    "Ava",
    "Jackson",
    "Isabella",
    "Lucas",
]

LAST_NAMES = [
    "Chen",
    "Patel",
    "Kim",
    "Nguyen",
    "Williams",
    "Johnson",
    "Brown",
    "Garcia",
    "Martinez",
    "Davis",
    "Rodriguez",
    "Wilson",
    "Anderson",
    "Thomas",
    "Moore",
    "Jackson",
    "White",
    "Harris",
    "Clark",
    "Lewis",
    "Robinson",
    "Walker",
    "Young",
    "Hall",
    "Allen",
    "King",
    "Wright",
    "Scott",
    "Green",
    "Baker",
]


def _distance_from_score(score: int) -> float:
    """Inverse of the scoring formula: distance = -campus_size * ln(score / 5000) / 5."""
    if score >= MAX_SCORE:
        return 0.0
    if score <= 0:
        return _CAMPUS_SIZE
    return -_CAMPUS_SIZE * math.log(score / MAX_SCORE) / _DECAY_CONSTANT


def _offset_for_distance(distance_m: float, rng: random.Random) -> tuple[float, float]:
    """Generate a random lat/lng offset that produces approximately the given distance."""
    # ~111,320 meters per degree latitude at Vanderbilt's latitude
    meters_per_deg = 111_320
    offset_deg = distance_m / meters_per_deg
    angle = rng.uniform(0, 2 * math.pi)
    return offset_deg * math.sin(angle), offset_deg * math.cos(angle)


async def _resolve_location_name(
    locations_collection,
    lng: float,
    lat: float,
) -> str | None:
    """Replicate LocationRepository.find_by_coordinates pattern."""
    point = {"type": "Point", "coordinates": [lng, lat]}

    result = await locations_collection.find_one(
        {"geometry": {"$geoIntersects": {"$geometry": point}}}
    )
    if result:
        return result.get("name")

    result = await locations_collection.find_one(
        {"geometry": {"$near": {"$geometry": point, "$maxDistance": 15}}}
    )
    return result.get("name") if result else None


async def seed_images(db) -> list[dict]:
    """Read images from disk, extract EXIF, insert into MongoDB.

    Returns the list of inserted image documents.
    """
    settings = get_settings()
    base_url = f"http://localhost:{settings.backend_port}/demo/images"

    images_collection = db.images
    locations_collection = db.locations

    # Idempotent: remove previous demo images
    await images_collection.delete_many(
        {"original_filename": {"$regex": f"^{DEMO_IMAGE_PREFIX}"}}
    )

    image_files = sorted(
        p for p in DEMO_IMAGES_DIR.iterdir() if p.suffix.lower() in IMAGE_EXTENSIONS
    )

    if not image_files:
        print(f"No images found in {DEMO_IMAGES_DIR}")
        return []

    inserted = []
    for path in image_files:
        file_bytes = path.read_bytes()
        metadata = extract_metadata(file_bytes)

        if metadata["latitude"] is None or metadata["longitude"] is None:
            print(f"  Skipping {path.name}: no GPS coordinates in EXIF")
            continue

        location_name = await _resolve_location_name(
            locations_collection,
            metadata["longitude"],
            metadata["latitude"],
        )

        image_id = ObjectId()
        filename = f"{DEMO_IMAGE_PREFIX}{path.name}"

        doc = {
            "_id": image_id,
            "url": f"{base_url}/{path.name}",
            "latitude": metadata["latitude"],
            "longitude": metadata["longitude"],
            "altitude": metadata.get("altitude"),
            "width": metadata.get("width"),
            "height": metadata.get("height"),
            "format": metadata.get("format"),
            "environment": "outdoor",
            "original_filename": filename,
            "file_size": len(file_bytes),
            "location_name": location_name,
            "created_at": datetime.now(UTC),
        }

        await images_collection.insert_one(doc)
        inserted.append(doc)
        loc_label = location_name or "unknown location"
        print(f"  Inserted {path.name} ({loc_label})")

    print(f"Seeded {len(inserted)} demo images")
    return inserted


def _build_round_scores(
    total_score: int,
    rounds: int,
    rng: random.Random,
) -> list[int]:
    """Distribute total_score across rounds with natural variance."""
    total_score = max(0, min(total_score, rounds * MAX_SCORE))
    remaining = total_score
    scores: list[int] = []

    for round_index in range(rounds):
        remaining_rounds = rounds - round_index - 1
        max_remaining = remaining_rounds * MAX_SCORE
        min_score = max(0, remaining - max_remaining)
        max_score = min(MAX_SCORE, remaining)
        if remaining_rounds == 0:
            score = remaining
        else:
            score = rng.randint(min_score, max_score)
        scores.append(score)
        remaining -= score

    rng.shuffle(scores)
    return scores


def _build_rounds(
    images: list[dict],
    round_scores: list[int],
    game_time: datetime,
    rng: random.Random,
) -> list[dict]:
    """Build round data using actual demo images and consistent distances."""
    rounds = []
    for round_id, score in enumerate(round_scores, start=1):
        image = rng.choice(images)
        actual_lat = image["latitude"]
        actual_lng = image["longitude"]

        distance = _distance_from_score(score)
        lat_off, lng_off = _offset_for_distance(distance, rng)
        guess_lat = actual_lat + lat_off
        guess_lng = actual_lng + lng_off

        round_time = game_time + timedelta(seconds=round_id * rng.randint(15, 45))

        rounds.append(
            {
                "round_id": round_id,
                "image_id": str(image["_id"]),
                "image_url": image["url"],
                "actual_lat": actual_lat,
                "actual_lng": actual_lng,
                "guess": {"lat": guess_lat, "lng": guess_lng},
                "distance_meters": round(distance, 2),
                "score": score,
                "started_at": round_time,
                "guessed_at": round_time + timedelta(seconds=rng.randint(5, 30)),
                "skipped": False,
                "location_name": image.get("location_name"),
            }
        )

    return rounds


async def seed_leaderboard(db, images: list[dict]) -> None:
    """Seed realistic users and completed games."""
    if not images:
        print("No demo images available — skipping leaderboard seeding")
        return

    users_collection = db.users
    games_collection = db.games
    rng = random.Random(42)

    # Idempotent: remove previous demo seed users and their games
    await users_collection.delete_many(
        {"microsoft_oid": {"$regex": f"^{DEMO_USER_PREFIX}"}}
    )
    await games_collection.delete_many({"user_id": {"$regex": f"^{DEMO_USER_PREFIX}"}})

    now = datetime.now(UTC)

    for index in range(SEED_USER_COUNT):
        first = FIRST_NAMES[index % len(FIRST_NAMES)]
        last = LAST_NAMES[index % len(LAST_NAMES)]
        name = f"{first} {last}"
        username = f"{first.lower()}{last.lower()}"
        email = f"{first.lower()}.{last.lower()}@vanderbilt.edu"
        user_id = f"{DEMO_USER_PREFIX}{index + 1:03d}"

        user_doc = {
            "microsoft_oid": user_id,
            "email": email,
            "username": username,
            "name": name,
            "avatar_url": None,
            "created_at": now - timedelta(days=rng.randint(7, 30)),
        }

        await users_collection.update_one(
            {"microsoft_oid": user_id},
            {"$set": user_doc},
            upsert=True,
        )

        # 1-4 games per user
        num_games = rng.randint(1, 4)
        for _game_idx in range(num_games):
            # Normal distribution centered at 3500 avg per round, std 600
            mean_round_score = max(500, min(4800, int(rng.gauss(3500, 600))))
            total_score = mean_round_score * ROUNDS_PER_GAME
            # Add per-game jitter
            total_score = max(
                0,
                min(
                    ROUNDS_PER_GAME * MAX_SCORE,
                    total_score + rng.randint(-500, 500),
                ),
            )

            round_scores = _build_round_scores(total_score, ROUNDS_PER_GAME, rng)

            # Spread games across last 7 days
            game_time = now - timedelta(
                days=rng.uniform(0, 7),
                hours=rng.randint(0, 23),
                minutes=rng.randint(0, 59),
            )

            rounds = _build_rounds(images, round_scores, game_time, rng)
            actual_total = sum(r["score"] for r in rounds)

            game_doc = {
                "user_id": user_id,
                "mode": {
                    "timed": rng.choice([True, False]),
                    "environment": "any",
                    "daily": False,
                },
                "status": "completed",
                "rounds": rounds,
                "total_score": actual_total,
                "created_at": game_time,
                "last_activity_at": game_time + timedelta(minutes=rng.randint(3, 10)),
            }

            await games_collection.insert_one(game_doc)

    print(f"Seeded {SEED_USER_COUNT} users with games")


async def seed() -> None:
    os.environ.setdefault("DEMO_MODE", "true")
    await connect_to_mongo()
    db = get_database()

    print("Seeding demo images...")
    images = await seed_images(db)

    print("Seeding demo leaderboard...")
    await seed_leaderboard(db, images)

    await close_mongo_connection()

    print("Done.")


if __name__ == "__main__":
    asyncio.run(seed())
