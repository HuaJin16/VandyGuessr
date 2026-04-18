from unittest.mock import AsyncMock, Mock

import pytest

import app.domains.images.service as image_service_module
import app.domains.images.submission_job_service as submission_job_service_module
from app.domains.images.models import ImageUploadResult
from app.domains.images.router import _enqueue_uploaded_file, _enqueue_uploaded_files
from app.domains.images.service import ImageService, ImageUploadError
from app.domains.images.submission_job_models import SubmissionJobAcceptedResponse
from app.domains.images.submission_job_service import SubmissionJobService


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


def test_validate_file_accepts_windows_heic_fallback_mime() -> None:
    service = _service()

    assert (
        service._validate_file("photo.HEIC", "application/octet-stream", 1024)
        == "image/heic"
    )


def test_validate_file_accepts_heic_sequence_mime() -> None:
    service = _service()

    assert (
        service._validate_file("photo.heic", "image/heic-sequence", 1024)
        == "image/heic"
    )


def test_validate_file_rejects_generic_mime_for_jpeg() -> None:
    service = _service()

    with pytest.raises(ImageUploadError, match="Unsupported content type"):
        service._validate_file("photo.jpg", "application/octet-stream", 1024)


def test_extract_upload_metadata_wraps_decode_failures() -> None:
    service = _service()

    with pytest.raises(ImageUploadError, match="Could not read this file"):
        service.extract_upload_metadata(b"not-a-real-image")


@pytest.mark.asyncio
async def test_upload_image_does_not_persist_before_full_processing_succeeds() -> None:
    repository = AsyncMock()
    location_service = AsyncMock()
    service = ImageService(repository, location_service)

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(
        image_service_module,
        "extract_metadata",
        lambda _payload: {
            "latitude": 36.1,
            "longitude": -86.8,
            "altitude": None,
            "timestamp": None,
            "width": 16350,
            "height": 3905,
            "format": "JPEG",
        },
    )
    monkeypatch.setattr(
        image_service_module,
        "upload_panorama_tiles",
        AsyncMock(side_effect=RuntimeError("tile upload failed")),
    )

    try:
        result = await service.upload_image(
            file_bytes=b"image-bytes",
            filename="pano.jpg",
            content_type="image/jpeg",
            environment="outdoor",
            asset_id="asset-1",
        )
    finally:
        monkeypatch.undo()

    assert result == ImageUploadResult(
        success=False,
        filename="pano.jpg",
        error="An unexpected error occurred",
    )
    repository.create.assert_not_awaited()
    location_service.resolve_location_name.assert_not_awaited()


@pytest.mark.asyncio
async def test_enqueue_submission_normalizes_heic_fallback_content_type() -> None:
    service, image_service, repository, _redis = _submission_job_service()
    image_service._validate_file.return_value = "image/heic"
    image_service.extract_upload_metadata.return_value = {
        "width": 16350,
        "height": 3905,
        "latitude": 36.1,
        "longitude": -86.8,
    }

    upload_bytes = AsyncMock(return_value="https://example.com/temp.bin")
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(submission_job_service_module, "upload_bytes", upload_bytes)

    try:
        response = await service.enqueue_submission(
            file_bytes=b"heic-bytes",
            filename="photo.heic",
            content_type="application/octet-stream",
            environment="outdoor",
            moderation_status="pending",
            submitted_by_user_id="user-1",
        )
    finally:
        monkeypatch.undo()

    assert response.status == "queued"
    upload_bytes.assert_awaited_once()
    assert upload_bytes.await_args.args[2] == "image/heic"
    created_job = repository.create.await_args.args[0]
    assert created_job.content_type == "image/heic"


@pytest.mark.asyncio
async def test_enqueue_submission_stops_on_unreadable_file() -> None:
    service, image_service, repository, _redis = _submission_job_service()
    image_service._validate_file.return_value = "image/heic"
    image_service.extract_upload_metadata.side_effect = ImageUploadError(
        "Could not read this file"
    )

    with pytest.raises(ImageUploadError, match="Could not read this file"):
        await service.enqueue_submission(
            file_bytes=b"broken-heic",
            filename="photo.heic",
            content_type="application/octet-stream",
            environment="outdoor",
            moderation_status="pending",
            submitted_by_user_id="user-1",
        )

    repository.create.assert_not_awaited()


def _submission_job_service() -> tuple[
    SubmissionJobService, AsyncMock, AsyncMock, AsyncMock
]:
    image_service = AsyncMock()
    image_service._validate_file = Mock()
    image_service.extract_upload_metadata = Mock()
    image_service._validate_image_geometry = Mock()
    repository = AsyncMock()
    repository.create = AsyncMock(return_value="job-1")
    redis_client = AsyncMock()
    service = SubmissionJobService(image_service, repository, redis_client)
    return service, image_service, repository, redis_client


@pytest.mark.asyncio
async def test_claim_next_job_falls_back_to_queued_jobs() -> None:
    service, _image_service, repository, _redis = _submission_job_service()
    repository.claim_stale_processing = AsyncMock(return_value=None)
    repository.claim_next_queued = AsyncMock(
        return_value={"_id": "job-1", "attempts": 1}
    )

    claimed = await service.claim_next_job("worker-1")

    assert claimed == {"_id": "job-1", "attempts": 1}
    repository.claim_stale_processing.assert_awaited_once()
    repository.claim_next_queued.assert_awaited_once()


@pytest.mark.asyncio
async def test_process_claimed_job_requeues_failed_attempt() -> None:
    service, image_service, repository, redis_client = _submission_job_service()
    repository.renew_lease = AsyncMock(return_value=True)
    repository.mark_queued = AsyncMock(return_value=True)
    repository.mark_failed = AsyncMock(return_value=True)
    repository.mark_completed = AsyncMock(return_value=True)
    image_service.upload_image = AsyncMock(
        return_value=ImageUploadResult(success=False, error="Upload failed")
    )

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(
        submission_job_service_module,
        "download_bytes",
        AsyncMock(return_value=b"image-bytes"),
    )
    monkeypatch.setattr(
        submission_job_service_module,
        "delete_object",
        AsyncMock(),
    )

    try:
        processed = await service.process_claimed_job(
            {
                "_id": "job-1",
                "attempts": 1,
                "asset_id": "asset-1",
                "temp_key": "images/uploads-temp/asset-1.bin",
                "filename": "pano.jpg",
                "content_type": "image/jpeg",
                "environment": "outdoor",
                "moderation_status": "approved",
                "submitted_by_user_id": None,
            },
            worker_id="worker-1",
        )
    finally:
        monkeypatch.undo()

    assert processed is False
    repository.mark_queued.assert_awaited_once_with("job-1", "Upload failed")
    repository.mark_failed.assert_not_awaited()
    repository.mark_completed.assert_not_awaited()
    redis_client.rpush.assert_awaited()


@pytest.mark.asyncio
async def test_process_claimed_job_marks_completed_and_cleans_temp_object() -> None:
    service, image_service, repository, _redis_client = _submission_job_service()
    repository.renew_lease = AsyncMock(return_value=True)
    repository.mark_queued = AsyncMock(return_value=True)
    repository.mark_failed = AsyncMock(return_value=True)
    repository.mark_completed = AsyncMock(return_value=True)
    image_service.upload_image = AsyncMock(
        return_value=ImageUploadResult(
            success=True,
            id="image-1",
            url="https://example.com/images/asset-1.jpg",
        )
    )

    delete_object = AsyncMock()
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(
        submission_job_service_module,
        "download_bytes",
        AsyncMock(return_value=b"image-bytes"),
    )
    monkeypatch.setattr(submission_job_service_module, "delete_object", delete_object)

    try:
        processed = await service.process_claimed_job(
            {
                "_id": "job-1",
                "attempts": 1,
                "asset_id": "asset-1",
                "temp_key": "images/uploads-temp/asset-1.bin",
                "filename": "pano.jpg",
                "content_type": "image/jpeg",
                "environment": "outdoor",
                "moderation_status": "approved",
                "submitted_by_user_id": None,
            },
            worker_id="worker-1",
        )
    finally:
        monkeypatch.undo()

    assert processed is True
    repository.mark_completed.assert_awaited_once_with(
        "job-1",
        worker_id="worker-1",
        image_id="image-1",
        image_url="https://example.com/images/asset-1.jpg",
    )
    repository.mark_failed.assert_not_awaited()
    repository.mark_queued.assert_not_awaited()
    delete_object.assert_awaited_once_with("images/uploads-temp/asset-1.bin")


def _mock_upload_file(filename: str, content_type: str, payload: bytes) -> AsyncMock:
    upload = AsyncMock()
    upload.filename = filename
    upload.content_type = content_type
    upload.read = AsyncMock(return_value=payload)
    return upload


@pytest.mark.asyncio
async def test_enqueue_uploaded_file_queues_operator_submission() -> None:
    service = AsyncMock()
    service.enqueue_submission = AsyncMock(
        return_value=SubmissionJobAcceptedResponse(jobId="job-123", status="queued")
    )
    file = _mock_upload_file("pano.jpg", "image/jpeg", b"image-bytes")

    result = await _enqueue_uploaded_file(service, file, "outdoor")

    assert result.jobId == "job-123"
    service.enqueue_submission.assert_awaited_once_with(
        file_bytes=b"image-bytes",
        filename="pano.jpg",
        content_type="image/jpeg",
        environment="outdoor",
        moderation_status="approved",
        submitted_by_user_id=None,
    )


@pytest.mark.asyncio
async def test_enqueue_uploaded_files_collects_queue_and_failure_results() -> None:
    service = AsyncMock()
    service.enqueue_submission = AsyncMock(
        side_effect=[
            SubmissionJobAcceptedResponse(jobId="job-1", status="queued"),
            ImageUploadError("Image is missing GPS EXIF data"),
            RuntimeError("boom"),
        ]
    )
    files = [
        _mock_upload_file("queued.jpg", "image/jpeg", b"queued"),
        _mock_upload_file("bad.jpg", "image/jpeg", b"bad"),
        _mock_upload_file("error.jpg", "image/jpeg", b"error"),
    ]

    queued_items, failed_items = await _enqueue_uploaded_files(service, files, "indoor")

    assert queued_items == [{"filename": "queued.jpg", "job_id": "job-1"}]
    assert failed_items == [
        {"filename": "bad.jpg", "error": "Image is missing GPS EXIF data"},
        {"filename": "error.jpg", "error": "An unexpected error occurred"},
    ]
