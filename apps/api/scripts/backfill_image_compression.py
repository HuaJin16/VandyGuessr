"""Backfill compression metadata for stored original images.

Run from apps/api/:
    python -m scripts.backfill_image_compression --dry-run
"""

from __future__ import annotations

import argparse
import asyncio
from dataclasses import dataclass
from urllib.parse import urlparse

import httpx

from app.config import get_settings
from app.core.db.mongo import close_mongo_connection, connect_to_mongo, get_database
from app.domains.images.entities import ImageCompressionEntity
from app.shared.exif import extract_metadata
from app.shared.image_compression import (
    CompressionResult,
    compress_original_image,
    extension_for_format,
)
from app.shared.s3 import build_public_url, upload_bytes


@dataclass(slots=True)
class BackfillStats:
    scanned: int = 0
    updated: int = 0
    failed: int = 0


def _extract_key(url: str) -> str | None:
    parsed = urlparse(url)
    path = parsed.path.lstrip("/")
    if not path:
        return None

    settings = get_settings()
    bucket = settings.spaces_bucket
    host = parsed.netloc.split(":", 1)[0].lower()

    if bucket and host.startswith(f"{bucket.lower()}."):
        return path

    if bucket and path.startswith(f"{bucket}/"):
        return path[len(bucket) + 1 :]

    return path


def _derive_destination_key(current_key: str, result: CompressionResult) -> str:
    if not result.compressed:
        return current_key
    stem = current_key.rsplit(".", 1)[0] if "." in current_key else current_key
    return f"{stem}{extension_for_format(result.format)}"


async def _process_image(
    image_doc: dict,
    client: httpx.AsyncClient,
    dry_run: bool,
) -> tuple[bool, str]:
    image_id = str(image_doc["_id"])
    image_url = image_doc.get("url")
    if not isinstance(image_url, str) or not image_url:
        return False, f"{image_id}: missing url"

    source_key = _extract_key(image_url)
    if not source_key:
        return False, f"{image_id}: unable to parse key from url"

    try:
        response = await client.get(image_url)
        response.raise_for_status()
        source_bytes = response.content
        source_content_type = response.headers.get("content-type", "")

        result = await asyncio.to_thread(
            compress_original_image,
            source_bytes,
            source_content_type,
        )

        exif = extract_metadata(result.data)
        if exif.get("latitude") is None or exif.get("longitude") is None:
            return False, f"{image_id}: compressed bytes missing GPS EXIF"

        destination_key = _derive_destination_key(source_key, result)
        destination_url = build_public_url(destination_key)

        if dry_run:
            return (
                True,
                f"{image_id}: would set compression (compressed={result.compressed}, savings={result.savings_ratio:.3f})",
            )

        if result.compressed:
            await upload_bytes(destination_key, result.data, result.content_type)

        update_doc: dict = {
            "compression": ImageCompressionEntity(
                version=1,
                source_size_bytes=result.source_size,
                stored_size_bytes=result.compressed_size,
                savings_ratio=result.savings_ratio,
                quality=result.quality,
                format=result.format,
                compressed=result.compressed,
            ).model_dump()
        }

        if destination_url != image_url:
            update_doc["url"] = destination_url

        await get_database().images.update_one(
            {"_id": image_doc["_id"]},
            {"$set": update_doc},
        )
        return (
            True,
            f"{image_id}: compressed={result.compressed} savings={result.savings_ratio:.3f}",
        )
    except Exception as exc:
        return False, f"{image_id}: {exc}"


async def run_backfill(
    *,
    dry_run: bool,
    limit: int | None,
    batch_size: int,
    concurrency: int,
    environment: str | None,
    force: bool,
) -> None:
    await connect_to_mongo()
    try:
        db = get_database()

        query: dict = {}
        if not force:
            query = {
                "$or": [
                    {"compression": {"$exists": False}},
                    {"compression": None},
                    {"compression.version": {"$exists": False}},
                    {"compression.version": {"$lt": 1}},
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
        description="Backfill compression metadata for existing images"
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
    parser.add_argument(
        "--force",
        action="store_true",
        help="Reprocess even if compression metadata already exists",
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
        force=args.force,
    )


if __name__ == "__main__":
    asyncio.run(main())
