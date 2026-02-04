"""API v1 router configuration."""

from fastapi import APIRouter

from app.api.v1.images import router as images_router
from app.api.v1.users import router as users_router

router = APIRouter()

router.include_router(images_router)
router.include_router(users_router)
