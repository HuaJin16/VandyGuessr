"""Compression helpers for stored original panorama files."""

from __future__ import annotations

import io
from dataclasses import dataclass

from PIL import Image, ImageOps
from pillow_heif import register_heif_opener

from app.config import get_settings

register_heif_opener()


@dataclass(frozen=True, slots=True)
class CompressionResult:
    data: bytes
    content_type: str
    format: str
    quality: int
    source_size: int
    compressed_size: int
    savings_ratio: float
    compressed: bool


def extension_for_format(image_format: str) -> str:
    """Map an image format name to a file extension."""
    if image_format in {"jpeg", "jpg"}:
        return ".jpg"
    if image_format == "png":
        return ".png"
    if image_format in {"heic", "heif"}:
        return ".heic"
    return ".jpg"


def compress_original_image(
    file_bytes: bytes,
    content_type: str | None,
    *,
    fallback_content_type: str = "image/jpeg",
) -> CompressionResult:
    """Compress uploaded source bytes for stored fallback image.

    The function preserves EXIF metadata and only applies compression when
    resulting bytes meet the configured minimum savings ratio.
    """

    settings = get_settings()
    target_quality = settings.image_original_jpeg_quality
    min_savings_ratio = settings.image_original_min_savings_ratio
    source_size = len(file_bytes)

    with Image.open(io.BytesIO(file_bytes)) as raw_image:
        exif = raw_image.getexif()
        if exif.get(274):
            exif[274] = 1
        exif_bytes = exif.tobytes() if exif else None

        image = ImageOps.exif_transpose(raw_image).convert("RGB")

        buffer = io.BytesIO()
        save_kwargs = {
            "format": "JPEG",
            "quality": target_quality,
            "optimize": True,
            "progressive": True,
        }
        if exif_bytes:
            save_kwargs["exif"] = exif_bytes

        image.save(buffer, **save_kwargs)
        compressed_bytes = buffer.getvalue()

    compressed_size = len(compressed_bytes)
    savings_ratio = (
        max(0.0, (source_size - compressed_size) / source_size) if source_size else 0.0
    )

    if compressed_size >= source_size or savings_ratio < min_savings_ratio:
        return CompressionResult(
            data=file_bytes,
            content_type=content_type or fallback_content_type,
            format=(content_type or fallback_content_type).split("/")[-1].lower(),
            quality=target_quality,
            source_size=source_size,
            compressed_size=source_size,
            savings_ratio=0.0,
            compressed=False,
        )

    return CompressionResult(
        data=compressed_bytes,
        content_type="image/jpeg",
        format="jpeg",
        quality=target_quality,
        source_size=source_size,
        compressed_size=compressed_size,
        savings_ratio=savings_ratio,
        compressed=True,
    )
