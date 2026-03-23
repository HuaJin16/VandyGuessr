"""Crowd submission moderation (list / approve / reject)."""

import structlog

from app.domains.images.repository import IImageRepository
from app.domains.users.repository import IUserRepository

logger = structlog.get_logger()


class ImageModerationService:
    def __init__(
        self,
        image_repository: IImageRepository,
        user_repository: IUserRepository,
    ) -> None:
        self._images = image_repository
        self._users = user_repository

    async def list_pending(self, limit: int, skip: int) -> list[dict]:
        docs = await self._images.find_pending_moderation(limit, skip)
        results: list[dict] = []
        for doc in docs:
            oid = doc.get("submitted_by_user_id")
            submitter_name: str | None = None
            submitter_email: str | None = None
            if oid:
                user_doc = await self._users.find_by_microsoft_oid(oid)
                if user_doc:
                    submitter_name = user_doc.get("name")
                    submitter_email = user_doc.get("email")
            doc["_id"] = str(doc["_id"])
            doc["submitter_name"] = submitter_name
            doc["submitter_email"] = submitter_email
            results.append(doc)
        return results

    async def approve(self, image_id: str, reviewer_oid: str) -> bool:
        ok = await self._images.update_moderation(
            image_id,
            moderation_status="approved",
            reviewed_by_user_id=reviewer_oid,
        )
        if ok:
            logger.info(
                "submission_approved",
                image_id=image_id,
                reviewer_oid=reviewer_oid,
            )
        return ok

    async def reject(self, image_id: str, reviewer_oid: str) -> bool:
        ok = await self._images.update_moderation(
            image_id,
            moderation_status="rejected",
            reviewed_by_user_id=reviewer_oid,
        )
        if ok:
            logger.info(
                "submission_rejected",
                image_id=image_id,
                reviewer_oid=reviewer_oid,
            )
        return ok
