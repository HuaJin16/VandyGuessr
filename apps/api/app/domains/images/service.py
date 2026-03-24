"""Image service for business logic."""

import asyncio
import contextlib
import uuid
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
from app.shared.panorama_tiling import generate_panorama_tiles
from app.shared.s3 import upload_bytes
from app.shared.tile_upload import upload_tile_artifacts

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

    def __init__(
        self,
        image_repository: IImageRepository,
        location_service: LocationService,
    ) -> None:
        self.image_repository = image_repository
        self.location_service = location_service

    def _validate_file(
        self, filename: str | None, content_type: str | None, file_size: int
    ) -> None:
        """Validate file extension, content type, and size."""
        settings = get_settings()

        # Validate extension
        filename = filename or ""
        extension = f".{filename.rsplit('.', 1)[-1].lower()}" if "." in filename else ""
        if extension not in self.ALLOWED_EXTENSIONS:
            raise ImageUploadError("Unsupported file extension")

        # Validate content type
        if content_type and content_type not in self.ALLOWED_CONTENT_TYPES:
            raise ImageUploadError("Unsupported content type")

        # Validate size
        if file_size > settings.upload_max_bytes:
            raise ImageUploadError("File exceeds maximum size")

    async def upload_image(
        self,
        file_bytes: bytes,
        filename: str | None,
        content_type: str | None,
        environment: Literal["indoor", "outdoor"],
        *,
        moderation_status: Literal["approved", "pending"] = "approved",
        submitted_by_user_id: str | None = None,
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
        try:
            # Validate file
            self._validate_file(filename, content_type, len(file_bytes))

            # Extract EXIF metadata
            metadata = extract_metadata(file_bytes)
            latitude = metadata.get("latitude")
            longitude = metadata.get("longitude")

            if latitude is None or longitude is None:
                raise ImageUploadError("Image is missing GPS EXIF data")

            asset_id = str(uuid.uuid4())

            tile_artifacts = await asyncio.to_thread(
                generate_panorama_tiles, file_bytes
            )
            tile_gps = extract_metadata(tile_artifacts.base_image)
            if tile_gps.get("latitude") is None or tile_gps.get("longitude") is None:
                raise ImageUploadError(
                    "Generated base panorama is missing GPS EXIF data"
                )

            tiles = await upload_tile_artifacts(asset_id, tile_artifacts)

            compression_result = await asyncio.to_thread(
                compress_original_image,
                file_bytes,
                content_type,
            )
            compression_gps = extract_metadata(compression_result.data)
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
                upload_content_type = content_type

            key = f"images/{asset_id}{file_extension}"

            # Upload to S3
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
