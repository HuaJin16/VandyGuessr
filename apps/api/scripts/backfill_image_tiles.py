"""Backfill tiled panorama metadata for existing images.

Run from apps/api/:
    python -m scripts.backfill_image_tiles --dry-run
"""

from __future__ import annotations

import argparse
import asyncio
from dataclasses import dataclass
from urllib.parse import urlparse

import httpx

from app.core.db.mongo import close_mongo_connection, connect_to_mongo, get_database
from app.shared.exif import extract_metadata
from app.shared.panorama_tiling import generate_panorama_tiles
from app.shared.tile_upload import upload_tile_artifacts


@dataclass(slots=True)
class BackfillStats:
    scanned: int = 0
    updated: int = 0
    failed: int = 0


def _asset_id_from_url(url: str, fallback: str) -> str:
    path = urlparse(url).path
    name = path.rsplit("/", 1)[-1] if path else ""
    if not name:
        return fallback
    return name.rsplit(".", 1)[0] or fallback


async def _process_image(
    image_doc: dict,
    client: httpx.AsyncClient,
    dry_run: bool,
) -> tuple[bool, str]:
    image_id = str(image_doc["_id"])
    image_url = image_doc.get("url")
    if not isinstance(image_url, str) or not image_url:
        return False, f"{image_id}: missing url"

    try:
        response = await client.get(image_url)
        response.raise_for_status()
        source_bytes = response.content

        artifacts = await asyncio.to_thread(generate_panorama_tiles, source_bytes)
        tile_gps = extract_metadata(artifacts.base_image)
        if tile_gps.get("latitude") is None or tile_gps.get("longitude") is None:
            return False, f"{image_id}: generated base missing GPS EXIF"

        if dry_run:
            return (
                True,
                f"{image_id}: would backfill {len(artifacts.metadata.levels)} levels",
            )

        asset_id = _asset_id_from_url(image_url, image_id)
        tile_metadata = await upload_tile_artifacts(asset_id, artifacts)
        await get_database().images.update_one(
            {"_id": image_doc["_id"]},
            {"$set": {"tiles": tile_metadata.model_dump()}},
        )
        return True, f"{image_id}: backfilled"
    except Exception as exc:
        return False, f"{image_id}: {exc}"


async def run_backfill(
    *,
    dry_run: bool,
    limit: int | None,
    batch_size: int,
    concurrency: int,
    environment: str | None,
) -> None:
    await connect_to_mongo()
    try:
        db = get_database()

        query: dict = {
            "$or": [
                {"tiles": {"$exists": False}},
                {"tiles": None},
                {"tiles.levels": {"$exists": False}},
                {"tiles.base_url": {"$exists": False}},
                {"tiles.version": {"$exists": False}},
                {"tiles.version": {"$lt": 2}},
                {"tiles.base_pano_data": {"$exists": False}},
            ]
        }
        if environment:
            query["environment"] = environment

        total_candidates = await db.images.count_documents(query)
        target_count = (
            min(total_candidates, limit) if limit is not None else total_candidates
        )
        print(f"Found {target_count} image(s) to process")

        cursor = db.images.find(query, {"url": 1, "environment": 1}).sort("_id", 1)

        semaphore = asyncio.Semaphore(concurrency)
        stats = BackfillStats()
        remaining = limit

        async with httpx.AsyncClient(timeout=45, follow_redirects=True) as client:
            while True:
                if remaining is not None and remaining <= 0:
                    break

                batch_limit = (
                    min(batch_size, remaining) if remaining is not None else batch_size
                )
                batch = await cursor.to_list(length=batch_limit)
                if not batch:
                    break

                async def run_one(image_doc: dict) -> tuple[bool, str]:
                    async with semaphore:
                        return await _process_image(image_doc, client, dry_run)

                results = await asyncio.gather(*(run_one(doc) for doc in batch))
                for ok, message in results:
                    stats.scanned += 1
                    if ok:
                        stats.updated += 1
                        print(f"OK  {message}")
                    else:
                        stats.failed += 1
                        print(f"ERR {message}")

                print(
                    f"Progress: scanned={stats.scanned} updated={stats.updated} failed={stats.failed}"
                )

                if remaining is not None:
                    remaining -= len(batch)

        print("Backfill complete")
        print(f"Scanned: {stats.scanned}")
        print(f"Updated: {stats.updated}")
        print(f"Failed:  {stats.failed}")
    finally:
        await close_mongo_connection()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Backfill panorama tiles for existing images"
    )
    parser.add_argument("--dry-run", action="store_true", help="Do not upload or write")
    parser.add_argument("--limit", type=int, default=None, help="Max images to process")
    parser.add_argument(
        "--batch-size",
        type=int,
        default=25,
        help="Images processed per batch",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=3,
        help="Concurrent image jobs",
    )
    parser.add_argument(
        "--environment",
        choices=["indoor", "outdoor"],
        default=None,
        help="Optional environment filter",
    )
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    await run_backfill(
        dry_run=args.dry_run,
        limit=args.limit,
        batch_size=max(1, args.batch_size),
        concurrency=max(1, args.concurrency),
        environment=args.environment,
    )


if __name__ == "__main__":
    asyncio.run(main())
