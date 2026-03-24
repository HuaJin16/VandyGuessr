"""Utilities for generating tiled panorama assets."""

from __future__ import annotations

import io
from dataclasses import dataclass

from PIL import Image, ImageFilter, ImageOps
from pillow_heif import register_heif_opener

from app.config import get_settings

register_heif_opener()

TILES_METADATA_VERSION = 2


@dataclass(frozen=True, slots=True)
class PanoramaGeometry:
    full_width: int
    full_height: int
    cropped_width: int
    cropped_height: int
    cropped_x: int
    cropped_y: int
    source_width: int
    source_height: int


@dataclass(frozen=True, slots=True)
class TileLevelSpec:
    level: int
    width: int
    height: int
    cols: int
    rows: int


@dataclass(frozen=True, slots=True)
class PanoramaTileMetadata:
    version: int
    original_width: int
    original_height: int
    aspect_ratio: float
    geometry: PanoramaGeometry
    levels: list[TileLevelSpec]


@dataclass(frozen=True, slots=True)
class PanoramaTileArtifacts:
    base_image: bytes
    tiles: dict[int, dict[tuple[int, int], bytes]]
    metadata: PanoramaTileMetadata


def _encode_jpeg(image: Image.Image, quality: int, exif_bytes: bytes | None) -> bytes:
    buffer = io.BytesIO()
    save_kwargs = {
        "format": "JPEG",
        "quality": quality,
        "optimize": True,
        "progressive": True,
    }
    if exif_bytes:
        save_kwargs["exif"] = exif_bytes
    image.save(buffer, **save_kwargs)
    return buffer.getvalue()


def _derive_geometry(source_width: int, source_height: int) -> PanoramaGeometry:
    full_width = max(source_width, source_height * 2)
    full_height = max(1, round(full_width / 2))
    cropped_x = max((full_width - source_width) // 2, 0)
    cropped_y = max((full_height - source_height) // 2, 0)

    return PanoramaGeometry(
        full_width=full_width,
        full_height=full_height,
        cropped_width=source_width,
        cropped_height=source_height,
        cropped_x=cropped_x,
        cropped_y=cropped_y,
        source_width=source_width,
        source_height=source_height,
    )


def _project_to_canvas(source: Image.Image, geometry: PanoramaGeometry) -> Image.Image:
    if (
        geometry.full_width == geometry.source_width
        and geometry.full_height == geometry.source_height
    ):
        return source

    canvas = Image.new("RGB", (geometry.full_width, geometry.full_height), (0, 0, 0))
    canvas.paste(source, (geometry.cropped_x, geometry.cropped_y))
    return canvas


def _power_of_two_floor(value: int, max_power: int) -> int:
    capped = max(1, min(value, max_power))
    power = 1
    while power * 2 <= capped:
        power *= 2
    return power


def _build_levels(
    geometry: PanoramaGeometry, *, base_max_width: int
) -> list[TileLevelSpec]:
    full_width = geometry.full_width
    full_height = geometry.full_height

    widths = []
    level0_width = min(base_max_width, full_width)
    widths.append(level0_width)

    level1_width = min(4096, full_width)
    if level1_width > level0_width:
        widths.append(level1_width)

    if full_width > level1_width:
        widths.append(full_width)

    levels: list[TileLevelSpec] = []
    for level_index, level_width in enumerate(widths):
        level_height = max(1, round(level_width * full_height / full_width))
        approx_tile_size = 768
        cols_target = max(1, round(level_width / approx_tile_size))
        rows_target = max(1, round(level_height / approx_tile_size))
        cols = _power_of_two_floor(cols_target, 64)
        rows = _power_of_two_floor(rows_target, 32)

        levels.append(
            TileLevelSpec(
                level=level_index,
                width=level_width,
                height=level_height,
                cols=cols,
                rows=rows,
            )
        )

    return levels


def generate_panorama_tiles(file_bytes: bytes) -> PanoramaTileArtifacts:
    settings = get_settings()

    with Image.open(io.BytesIO(file_bytes)) as raw_image:
        exif = raw_image.getexif()
        if exif.get(274):
            exif[274] = 1
        exif_bytes = exif.tobytes() if exif else None

        oriented = ImageOps.exif_transpose(raw_image).convert("RGB")
        source_width, source_height = oriented.size
        geometry = _derive_geometry(source_width, source_height)
        source = _project_to_canvas(oriented, geometry)

        levels = _build_levels(
            geometry,
            base_max_width=settings.panorama_base_max_width,
        )

        base_spec = levels[0]
        base_image = source.resize(
            (base_spec.width, base_spec.height),
            Image.Resampling.LANCZOS,
        ).filter(ImageFilter.GaussianBlur(radius=2))
        base_bytes = _encode_jpeg(
            base_image, settings.panorama_base_quality, exif_bytes
        )

        tile_payload: dict[int, dict[tuple[int, int], bytes]] = {}
        for spec in levels:
            if spec.width == source.width and spec.height == source.height:
                level_image = source
            else:
                level_image = source.resize(
                    (spec.width, spec.height),
                    Image.Resampling.LANCZOS,
                )

            tile_width = max(1, level_image.width // spec.cols)
            tile_height = max(1, level_image.height // spec.rows)
            level_tiles: dict[tuple[int, int], bytes] = {}

            for row in range(spec.rows):
                for col in range(spec.cols):
                    left = col * tile_width
                    upper = row * tile_height
                    right = (
                        level_image.width if col == spec.cols - 1 else left + tile_width
                    )
                    lower = (
                        level_image.height
                        if row == spec.rows - 1
                        else upper + tile_height
                    )
                    tile = level_image.crop((left, upper, right, lower))
                    level_tiles[(col, row)] = _encode_jpeg(
                        tile,
                        settings.panorama_tile_quality,
                        exif_bytes,
                    )

            tile_payload[spec.level] = level_tiles

    return PanoramaTileArtifacts(
        base_image=base_bytes,
        tiles=tile_payload,
        metadata=PanoramaTileMetadata(
            version=TILES_METADATA_VERSION,
            original_width=geometry.source_width,
            original_height=geometry.source_height,
            aspect_ratio=geometry.source_width / geometry.source_height,
            geometry=geometry,
            levels=levels,
        ),
    )
