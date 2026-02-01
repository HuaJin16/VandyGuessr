"""Image upload endpoints."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status

from app.config import get_settings
from app.services.exif import extract_metadata
from app.services.s3 import upload_bytes

router = APIRouter(prefix="/images", tags=["images"])

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".heic"}
ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/heic",
    "image/heif",
}


def _require_code(code: str | None) -> None:
    settings = get_settings()
    if not settings.upload_secret_code:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Upload secret code is not configured",
        )
    if not code or code != settings.upload_secret_code:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid upload code",
        )


def _validate_file(file: UploadFile) -> None:
    filename = file.filename or ""
    extension = f".{filename.rsplit('.', 1)[-1].lower()}" if "." in filename else ""
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file extension",
        )
    if file.content_type and file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported content type",
        )


@router.post("/upload")
async def upload_image(
    file: UploadFile = File(...),
    code: str | None = Query(default=None),
) -> dict[str, Any]:
    _require_code(code)
    _validate_file(file)

    settings = get_settings()
    file_bytes = await file.read()
    if len(file_bytes) > settings.upload_max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File exceeds maximum size",
        )

    metadata = extract_metadata(file_bytes)
    if metadata.get("latitude") is None or metadata.get("longitude") is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image is missing GPS EXIF data",
        )

    file_extension = (
        "." + file.filename.rsplit(".", 1)[-1].lower()
        if file.filename and "." in file.filename
        else ""
    )
    key = f"images/{uuid.uuid4()}{file_extension}"

    url = await upload_bytes(key, file_bytes, file.content_type)

    return {
        "success": True,
        "url": url,
        "metadata": {
            "latitude": metadata.get("latitude"),
            "longitude": metadata.get("longitude"),
            "altitude": metadata.get("altitude"),
            "timestamp": metadata.get("timestamp"),
            "width": metadata.get("width"),
            "height": metadata.get("height"),
            "format": metadata.get("format"),
            "original_filename": file.filename,
            "file_size": len(file_bytes),
        },
    }
