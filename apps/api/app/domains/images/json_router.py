"""JSON API for authenticated crowd uploads and moderation."""

from typing import Literal

from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status

from app.container import deps
from app.core.auth import CurrentUser
from app.core.auth.reviewer import ReviewerUser
from app.domains.images.models import (
    CrowdSubmissionResponse,
    PendingSubmissionItem,
    PendingSubmissionsResponse,
)
from app.domains.images.moderation_service import ImageModerationService
from app.domains.images.service import ImageService

router = APIRouter(prefix="/images", tags=["images"])


@router.post(
    "/submissions",
    response_model=CrowdSubmissionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit_crowd_image(
    current_user: CurrentUser,
    environment: Literal["indoor", "outdoor"] = Query(...),
    file: UploadFile = File(...),
    image_service: ImageService = deps(ImageService),
) -> CrowdSubmissionResponse:
    file_bytes = await file.read()
    result = await image_service.upload_image(
        file_bytes=file_bytes,
        filename=file.filename,
        content_type=file.content_type,
        environment=environment,
        moderation_status="pending",
        submitted_by_user_id=current_user["oid"],
    )
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.error or "Upload failed",
        )
    return CrowdSubmissionResponse(
        id=result.id or "",
        url=result.url or "",
        latitude=result.latitude or 0.0,
        longitude=result.longitude or 0.0,
        environment=environment,
    )


@router.get("/moderation/pending", response_model=PendingSubmissionsResponse)
async def list_pending_submissions(
    _reviewer: ReviewerUser,
    limit: int = Query(default=50, ge=1, le=100),
    skip: int = Query(default=0, ge=0),
    moderation_service: ImageModerationService = deps(ImageModerationService),
) -> PendingSubmissionsResponse:
    docs = await moderation_service.list_pending(limit, skip)
    items = [
        PendingSubmissionItem(
            id=doc["_id"],
            url=doc["url"],
            latitude=doc["latitude"],
            longitude=doc["longitude"],
            environment=doc["environment"],
            location_name=doc.get("location_name"),
            original_filename=doc.get("original_filename"),
            created_at=doc["created_at"],
            submitter_name=doc.get("submitter_name"),
            submitter_email=doc.get("submitter_email"),
        )
        for doc in docs
    ]
    return PendingSubmissionsResponse(items=items)


@router.post("/moderation/{image_id}/approve", status_code=status.HTTP_204_NO_CONTENT)
async def approve_submission(
    image_id: str,
    reviewer: ReviewerUser,
    moderation_service: ImageModerationService = deps(ImageModerationService),
) -> None:
    ok = await moderation_service.approve(image_id, reviewer["oid"])
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pending submission not found",
        )


@router.post("/moderation/{image_id}/reject", status_code=status.HTTP_204_NO_CONTENT)
async def reject_submission(
    image_id: str,
    reviewer: ReviewerUser,
    moderation_service: ImageModerationService = deps(ImageModerationService),
) -> None:
    ok = await moderation_service.reject(image_id, reviewer["oid"])
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pending submission not found",
        )
