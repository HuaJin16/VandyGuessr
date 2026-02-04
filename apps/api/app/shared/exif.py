"""EXIF extraction utilities for uploaded images."""

from __future__ import annotations

import io
from datetime import datetime
from typing import Any

from PIL import ExifTags, Image
from pillow_heif import register_heif_opener

register_heif_opener()


def _rational_to_float(value: Any) -> float:
    return (
        float(value[0]) / float(value[1]) if isinstance(value, tuple) else float(value)
    )


def _convert_to_degrees(value: Any) -> float:
    degrees = _rational_to_float(value[0])
    minutes = _rational_to_float(value[1])
    seconds = _rational_to_float(value[2])
    return degrees + (minutes / 60.0) + (seconds / 3600.0)


def _parse_timestamp(raw: str | None) -> str | None:
    if not raw:
        return None
    try:
        parsed = datetime.strptime(raw, "%Y:%m:%d %H:%M:%S")
    except ValueError:
        return None
    return parsed.isoformat()


def extract_metadata(file_bytes: bytes) -> dict[str, Any]:
    with Image.open(io.BytesIO(file_bytes)) as image:
        exif = image.getexif()
        if not exif:
            return {
                "latitude": None,
                "longitude": None,
                "altitude": None,
                "timestamp": None,
                "width": image.width,
                "height": image.height,
                "format": image.format,
            }

        exif_data = {ExifTags.TAGS.get(tag, tag): value for tag, value in exif.items()}

        # GPS data is in a sub-IFD, access it properly via get_ifd()
        # Using exif_data.get("GPSInfo") returns an IFD pointer (int), not the data
        gps_ifd = exif.get_ifd(ExifTags.IFD.GPSInfo)
        gps_data: dict[str | int, Any] = {}
        if gps_ifd:
            gps_data = {
                ExifTags.GPSTAGS.get(tag, tag): value for tag, value in gps_ifd.items()
            }

        latitude = None
        longitude = None
        if gps_data.get("GPSLatitude") and gps_data.get("GPSLatitudeRef"):
            latitude = _convert_to_degrees(gps_data["GPSLatitude"])
            if gps_data["GPSLatitudeRef"].upper() == "S":
                latitude = -latitude

        if gps_data.get("GPSLongitude") and gps_data.get("GPSLongitudeRef"):
            longitude = _convert_to_degrees(gps_data["GPSLongitude"])
            if gps_data["GPSLongitudeRef"].upper() == "W":
                longitude = -longitude

        altitude = None
        if gps_data.get("GPSAltitude") is not None:
            altitude = float(gps_data["GPSAltitude"])
            if gps_data.get("GPSAltitudeRef") in (1, "1"):
                altitude = -altitude

        timestamp = _parse_timestamp(exif_data.get("DateTimeOriginal"))
        if not timestamp:
            timestamp = _parse_timestamp(exif_data.get("DateTime"))

        return {
            "latitude": latitude,
            "longitude": longitude,
            "altitude": altitude,
            "timestamp": timestamp,
            "width": image.width,
            "height": image.height,
            "format": image.format,
        }
