"""S3-compatible storage helpers for image uploads."""

from __future__ import annotations

import asyncio
from functools import lru_cache
from urllib.parse import urlparse

import boto3
from botocore.config import Config

from app.config import get_settings


@lru_cache
def get_s3_client():
    settings = get_settings()
    return boto3.client(
        "s3",
        region_name=settings.spaces_region or None,
        endpoint_url=settings.spaces_endpoint or None,
        aws_access_key_id=settings.spaces_access_key or None,
        aws_secret_access_key=settings.spaces_secret_key or None,
        config=Config(s3={"addressing_style": "virtual"}),
    )


def build_public_url(key: str) -> str:
    settings = get_settings()
    endpoint = settings.spaces_endpoint
    bucket = settings.spaces_bucket
    if not endpoint or not bucket:
        raise ValueError("Spaces endpoint and bucket are required")

    parsed = urlparse(endpoint)
    host = parsed.netloc or parsed.path
    scheme = parsed.scheme or "https"
    return f"{scheme}://{bucket}.{host}/{key}"


async def upload_bytes(
    key: str,
    data: bytes,
    content_type: str | None,
    *,
    public: bool = True,
) -> str:
    settings = get_settings()
    if not settings.spaces_bucket:
        raise ValueError("Spaces bucket is required")

    client = get_s3_client()
    put_kwargs: dict[str, str | bytes] = {
        "Bucket": settings.spaces_bucket,
        "Key": key,
        "Body": data,
        "ContentType": content_type or "application/octet-stream",
    }
    if public:
        put_kwargs["ACL"] = "public-read"

    await asyncio.to_thread(client.put_object, **put_kwargs)
    return build_public_url(key)


async def download_bytes(key: str) -> bytes:
    settings = get_settings()
    if not settings.spaces_bucket:
        raise ValueError("Spaces bucket is required")

    client = get_s3_client()
    response = await asyncio.to_thread(
        client.get_object,
        Bucket=settings.spaces_bucket,
        Key=key,
    )
    body = response["Body"]
    return await asyncio.to_thread(body.read)


async def delete_object(key: str) -> None:
    settings = get_settings()
    if not settings.spaces_bucket:
        raise ValueError("Spaces bucket is required")

    client = get_s3_client()
    await asyncio.to_thread(
        client.delete_object,
        Bucket=settings.spaces_bucket,
        Key=key,
    )
