"""Thumbnail helpers for lightweight image previews."""

from __future__ import annotations

import io

from PIL import Image, ImageOps

from app.config import get_settings


def generate_thumbnail_image(file_bytes: bytes) -> bytes:
    """Generate a small JPEG thumbnail for list and detail previews."""

    settings = get_settings()
    target_size = (
        settings.image_thumbnail_max_width,
        settings.image_thumbnail_max_height,
    )

    with Image.open(io.BytesIO(file_bytes)) as raw_image:
        image = ImageOps.exif_transpose(raw_image).convert("RGB")
        thumbnail = ImageOps.fit(
            image,
            target_size,
            method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.45),
        )

        buffer = io.BytesIO()
        thumbnail.save(
            buffer,
            format="JPEG",
            quality=settings.image_thumbnail_jpeg_quality,
            optimize=True,
            progressive=True,
        )
        return buffer.getvalue()
