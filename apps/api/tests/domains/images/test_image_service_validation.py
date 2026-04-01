from unittest.mock import AsyncMock

import pytest

from app.domains.images.service import ImageService, ImageUploadError


def _service() -> ImageService:
    return ImageService(AsyncMock(), AsyncMock())


def test_validate_image_geometry_rejects_non_positive_dimensions() -> None:
    service = _service()

    with pytest.raises(ImageUploadError, match="Unable to determine image dimensions"):
        service._validate_image_geometry(0, 2000)


def test_validate_image_geometry_rejects_too_many_pixels() -> None:
    service = _service()

    with pytest.raises(ImageUploadError, match="Image resolution exceeds"):
        service._validate_image_geometry(10000, 7001)


def test_validate_image_geometry_rejects_large_projected_width() -> None:
    service = _service()

    with pytest.raises(ImageUploadError, match="Panorama projection exceeds"):
        service._validate_image_geometry(8000, 8501)


def test_validate_image_geometry_accepts_reasonable_dimensions() -> None:
    service = _service()

    service._validate_image_geometry(6000, 3000)
