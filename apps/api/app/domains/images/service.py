"""Image service for business logic."""

import asyncio
import contextlib
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Literal

import structlog

from app.config import get_settings
from app.domains.images.entities import (
    ImageCompressionEntity,
    ImageEntity,
)
from app.domains.images.models import ImageUploadResult
from app.domains.images.repository import IImageRepository
from app.domains.locations.service import LocationService
from app.shared.exif import extract_metadata
from app.shared.image_compression import compress_original_image, extension_for_format
from app.shared.image_thumbnails import generate_thumbnail_image
from app.shared.s3 import upload_bytes
from app.shared.tile_upload import upload_panorama_tiles

logger = structlog.get_logger()


class ImageUploadError(Exception):
    """Exception raised when image upload fails."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class ImageService:
    """Service for image-related business logic."""

    ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".heic"}
    ALLOWED_CONTENT_TYPES = {
        "image/jpeg",
        "image/png",
        "image/heic",
        "image/heif",
    }
    HEIC_CONTENT_TYPES = {
        "image/heic",
        "image/heif",
        "image/heic-sequence",
        "image/heif-sequence",
    }
    HEIC_FALLBACK_CONTENT_TYPES = {"application/octet-stream"}

    def __init__(
        self,
        image_repository: IImageRepository,
        location_service: LocationService,
    ) -> None:
        self.image_repository = image_repository
        self.location_service = location_service

    @classmethod
    def _file_extension(cls, filename: str | None) -> str:
        filename = filename or ""
        if "." not in filename:
            return ""
        return f".{filename.rsplit('.', 1)[-1].lower()}"

    @staticmethod
    def _normalize_content_type(content_type: str | None) -> str | None:
        if not content_type:
            return None
        normalized = content_type.split(";", 1)[0].strip().lower()
        return normalized or None

    def _validate_file(
        self, filename: str | None, content_type: str | None, file_size: int
    ) -> str | None:
        """Validate file extension, content type, and size."""
        settings = get_settings()

        # Validate extension
        extension = self._file_extension(filename)
        if extension not in self.ALLOWED_EXTENSIONS:
            raise ImageUploadError("Unsupported file extension")

        # Validate content type
        normalized_content_type = self._normalize_content_type(content_type)
        if extension == ".heic":
            if (
                normalized_content_type in self.HEIC_CONTENT_TYPES
                or normalized_content_type in self.HEIC_FALLBACK_CONTENT_TYPES
                or normalized_content_type is None
            ):
                effective_content_type = "image/heic"
            else:
                raise ImageUploadError("Unsupported content type")
        else:
            if (
                normalized_content_type
                and normalized_content_type not in self.ALLOWED_CONTENT_TYPES
            ):
                raise ImageUploadError("Unsupported content type")
            effective_content_type = normalized_content_type

        # Validate size
        if file_size > settings.upload_max_bytes:
            raise ImageUploadError("File exceeds maximum size")

        return effective_content_type

    def extract_upload_metadata(self, file_bytes: bytes) -> dict[str, object]:
        try:
            return extract_metadata(file_bytes)
        except Exception as exc:
            raise ImageUploadError("Could not read this file") from exc

    def _validate_image_geometry(self, width: int | None, height: int | None) -> None:
        """Validate image dimensions before expensive processing."""
        settings = get_settings()
        if not isinstance(width, int) or width <= 0:
            raise ImageUploadError("Unable to determine image dimensions")
        if not isinstance(height, int) or height <= 0:
            raise ImageUploadError("Unable to determine image dimensions")

        if max(width, height) > settings.upload_max_dimension:
            raise ImageUploadError("Image dimensions exceed maximum allowed")

        if width * height > settings.upload_max_pixels:
            raise ImageUploadError("Image resolution exceeds maximum allowed")

        projected_full_width = max(width, height * 2)
        if projected_full_width > settings.upload_max_projected_full_width:
            raise ImageUploadError("Panorama projection exceeds maximum allowed")

    async def upload_image(
        self,
        file_bytes: bytes,
        filename: str | None,
        content_type: str | None,
        environment: Literal["indoor", "outdoor"],
        *,
        moderation_status: Literal["approved", "pending"] = "approved",
        submitted_by_user_id: str | None = None,
        asset_id: str,
        progress_callback: Callable[[str], Awaitable[None]] | None = None,
    ) -> ImageUploadResult:
        """Upload a single image to S3 and persist metadata to MongoDB.

        Args:
            file_bytes: The image file bytes
            filename: Original filename
            content_type: MIME type
            environment: "indoor" or "outdoor"

        Returns:
            ImageUploadResult with success/failure info
        """

        async def report_progress(stage: str) -> None:
            if progress_callback is None:
                return
            with contextlib.suppress(Exception):
                await progress_callback(stage)

        try:
            await report_progress("validating_image")

            # Validate file
            effective_content_type = self._validate_file(
                filename, content_type, len(file_bytes)
            )

            # Extract EXIF metadata
            metadata = self.extract_upload_metadata(file_bytes)
            self._validate_image_geometry(metadata.get("width"), metadata.get("height"))
            latitude = metadata.get("latitude")
            longitude = metadata.get("longitude")

            if latitude is None or longitude is None:
                raise ImageUploadError("Image is missing GPS EXIF data")

            await report_progress("generating_tiles")
            tiles = await upload_panorama_tiles(asset_id, file_bytes)

            await report_progress("generating_thumbnail")
            thumbnail_bytes = await asyncio.to_thread(
                generate_thumbnail_image,
                file_bytes,
            )
            thumbnail_url = await upload_bytes(
                f"images/{asset_id}/thumbnail.jpg",
                thumbnail_bytes,
                "image/jpeg",
            )

            await report_progress("compressing_original")
            compression_result = await asyncio.to_thread(
                compress_original_image,
                file_bytes,
                effective_content_type,
            )
            compression_gps = self.extract_upload_metadata(compression_result.data)
            if (
                compression_gps.get("latitude") is None
                or compression_gps.get("longitude") is None
            ):
                raise ImageUploadError("Compressed panorama is missing GPS EXIF data")

            # Generate S3 key
            original_extension = (
                "." + filename.rsplit(".", 1)[-1].lower()
                if filename and "." in filename
                else ""
            )
            if compression_result.compressed:
                file_extension = extension_for_format(compression_result.format)
                upload_bytes_payload = compression_result.data
                upload_content_type = compression_result.content_type
            else:
                file_extension = original_extension or extension_for_format(
                    (metadata.get("format") or "").lower()
                )
                upload_bytes_payload = file_bytes
                upload_content_type = effective_content_type

            key = f"images/{asset_id}{file_extension}"

            # Upload to S3
            await report_progress("uploading_original")
            url = await upload_bytes(
                key,
                upload_bytes_payload,
                upload_content_type,
            )

            # Parse timestamp if present
            timestamp = None
            if metadata.get("timestamp"):
                with contextlib.suppress(ValueError, TypeError):
                    timestamp = datetime.fromisoformat(metadata["timestamp"])

            # Resolve campus location from coordinates
            await report_progress("resolving_location")
            location_name = await self.location_service.resolve_location_name(
                latitude, longitude
            )

            now = datetime.now(UTC)
            image = ImageEntity(
                url=url,
                latitude=latitude,
                longitude=longitude,
                altitude=metadata.get("altitude"),
                timestamp=timestamp,
                width=metadata.get("width"),
                height=metadata.get("height"),
                format=metadata.get("format"),
                environment=environment,
                original_filename=filename,
                file_size=len(file_bytes),
                location_name=location_name,
                thumbnail_url=thumbnail_url,
                thumbnail_version=2,
                tiles=tiles,
                compression=ImageCompressionEntity(
                    version=1,
                    source_size_bytes=compression_result.source_size,
                    stored_size_bytes=compression_result.compressed_size,
                    savings_ratio=compression_result.savings_ratio,
                    quality=compression_result.quality,
                    format=compression_result.format,
                    compressed=compression_result.compressed,
                ),
                created_at=now,
                moderation_status=moderation_status,
                submitted_by_user_id=submitted_by_user_id,
                submitted_at=now if moderation_status == "pending" else None,
            )

            # Persist to MongoDB
            await report_progress("persisting_image")
            image_id = await self.image_repository.create(image)

            if moderation_status == "pending":
                logger.info(
                    "submission_created",
                    image_id=image_id,
                    submitted_by=submitted_by_user_id,
                    environment=environment,
                    tile_levels=tiles.level_count,
                    original_file_size=compression_result.source_size,
                    stored_file_size=compression_result.compressed_size,
                    compression_applied=compression_result.compressed,
                    compression_savings_ratio=compression_result.savings_ratio,
                )
            else:
                logger.info(
                    "image_uploaded",
                    image_id=image_id,
                    key=key,
                    latitude=latitude,
                    longitude=longitude,
                    environment=environment,
                    location_name=location_name,
                    tile_levels=tiles.level_count,
                    original_file_size=compression_result.source_size,
                    stored_file_size=compression_result.compressed_size,
                    compression_applied=compression_result.compressed,
                    compression_savings_ratio=compression_result.savings_ratio,
                )

            return ImageUploadResult(
                success=True,
                filename=filename,
                id=image_id,
                url=url,
                latitude=latitude,
                longitude=longitude,
            )

        except ImageUploadError as e:
            logger.warning(
                "image_upload_failed",
                filename=filename,
                error=e.message,
            )
            return ImageUploadResult(
                success=False,
                filename=filename,
                error=e.message,
            )
        except Exception as e:
            logger.error(
                "image_upload_error",
                filename=filename,
                error=str(e),
            )
            return ImageUploadResult(
                success=False,
                filename=filename,
                error="An unexpected error occurred",
            )
