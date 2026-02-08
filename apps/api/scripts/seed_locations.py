"""Seed the locations collection from OpenStreetMap GeoJSON data.

Run from apps/api/:
    python -m scripts.seed_locations
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path

from motor.motor_asyncio import AsyncIOMotorClient

from app.config import get_settings

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "campus_buildings.geojson"


def _extract_building_type(properties: dict) -> str | None:
    for key in ("building", "leisure", "amenity"):
        if value := properties.get(key):
            return value if value != "yes" else None
    return None


async def seed() -> None:
    settings = get_settings()
    client: AsyncIOMotorClient = AsyncIOMotorClient(settings.mongodb_url)
    db = client[settings.mongodb_database]
    collection = db.locations

    # Ensure indexes
    await collection.create_index([("geometry", "2dsphere")])
    await collection.create_index("osm_id", unique=True)

    # Load GeoJSON
    with open(DATA_PATH) as f:
        geojson = json.load(f)

    features = [f for f in geojson["features"] if f["properties"].get("name")]
    print(f"Found {len(features)} named features in GeoJSON")

    seeded = 0
    for feature in features:
        props = feature["properties"]
        doc = {
            "name": props["name"],
            "osm_id": props["@id"],
            "building_type": _extract_building_type(props),
            "geometry": feature["geometry"],
        }
        await collection.update_one(
            {"osm_id": doc["osm_id"]},
            {
                "$set": doc,
                "$setOnInsert": {"created_at": datetime.utcnow()},
            },
            upsert=True,
        )
        seeded += 1

    print(f"Seeded {seeded} locations")

    # Backfill existing images missing location_name
    images_collection = db.images
    cursor = images_collection.find(
        {"$or": [{"location_name": None}, {"location_name": {"$exists": False}}]}
    )
    backfilled = 0
    async for image in cursor:
        lat = image.get("latitude")
        lng = image.get("longitude")
        if lat is None or lng is None:
            continue

        point = {"type": "Point", "coordinates": [lng, lat]}
        location = await collection.find_one(
            {"geometry": {"$geoIntersects": {"$geometry": point}}}
        )
        if not location:
            location = await collection.find_one(
                {"geometry": {"$near": {"$geometry": point, "$maxDistance": 15}}}
            )
        if location:
            await images_collection.update_one(
                {"_id": image["_id"]},
                {"$set": {"location_name": location["name"]}},
            )
            backfilled += 1

    print(f"Backfilled {backfilled} images with location names")

    client.close()


if __name__ == "__main__":
    asyncio.run(seed())
