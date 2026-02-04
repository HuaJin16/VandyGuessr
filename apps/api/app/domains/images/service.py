"""Image service for business logic."""

import contextlib
import uuid
from datetime import datetime
from typing import Literal

import structlog

from app.config import get_settings
from app.domains.images.entities import ImageEntity
from app.domains.images.models import ImageUploadResult
from app.domains.images.repository import IImageRepository
from app.shared.exif import extract_metadata
from app.shared.s3 import upload_bytes

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

    def __init__(self, image_repository: IImageRepository) -> None:
        self.image_repository = image_repository

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

            # Generate S3 key
            file_extension = (
                "." + filename.rsplit(".", 1)[-1].lower()
                if filename and "." in filename
                else ""
            )
            key = f"images/{uuid.uuid4()}{file_extension}"

            # Upload to S3
            url = await upload_bytes(key, file_bytes, content_type)

            # Parse timestamp if present
            timestamp = None
            if metadata.get("timestamp"):
                with contextlib.suppress(ValueError, TypeError):
                    timestamp = datetime.fromisoformat(metadata["timestamp"])

            # Create entity
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
                created_at=datetime.utcnow(),
            )

            # Persist to MongoDB
            image_id = await self.image_repository.create(image)

            logger.info(
                "image_uploaded",
                image_id=image_id,
                key=key,
                latitude=latitude,
                longitude=longitude,
                environment=environment,
                file_size=len(file_bytes),
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
