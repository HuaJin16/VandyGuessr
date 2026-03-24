"""Upload tiled panorama artifacts to S3 and build metadata entity."""

import asyncio

from app.domains.images.entities import (
    ImagePanoDataEntity,
    ImageTileLevelEntity,
    ImageTilesEntity,
)
from app.shared.panorama_tiling import PanoramaTileArtifacts
from app.shared.s3 import build_public_url, upload_bytes


async def upload_tile_artifacts(
    asset_id: str,
    artifacts: PanoramaTileArtifacts,
) -> ImageTilesEntity:
    base_key = f"images/{asset_id}/base.jpg"
    await upload_bytes(base_key, artifacts.base_image, "image/jpeg")

    semaphore = asyncio.Semaphore(12)

    async def _upload_one(level: int, col: int, row: int, data: bytes) -> None:
        key = f"images/{asset_id}/l{level}/{col}_{row}.jpg"
        async with semaphore:
            await upload_bytes(key, data, "image/jpeg")

    tasks = [
        _upload_one(level, col, row, tile_bytes)
        for level, tiles in artifacts.tiles.items()
        for (col, row), tile_bytes in tiles.items()
    ]
    if tasks:
        await asyncio.gather(*tasks)

    levels = [
        ImageTileLevelEntity(
            level=spec.level,
            width=spec.width,
            height=spec.height,
            cols=spec.cols,
            rows=spec.rows,
        )
        for spec in artifacts.metadata.levels
    ]

    geometry = artifacts.metadata.geometry

    return ImageTilesEntity(
        version=artifacts.metadata.version,
        base_url=build_public_url(base_key),
        tile_url_template=build_public_url(
            f"images/{asset_id}/l{{level}}/{{col}}_{{row}}.jpg"
        ),
        level_count=len(levels),
        original_width=artifacts.metadata.original_width,
        original_height=artifacts.metadata.original_height,
        aspect_ratio=artifacts.metadata.aspect_ratio,
        base_pano_data=ImagePanoDataEntity(
            full_width=geometry.full_width,
            full_height=geometry.full_height,
            cropped_width=geometry.cropped_width,
            cropped_height=geometry.cropped_height,
            cropped_x=geometry.cropped_x,
            cropped_y=geometry.cropped_y,
        ),
        levels=levels,
    )
