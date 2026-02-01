"""API v1 router configuration."""

from fastapi import APIRouter

from app.api.v1.images import router as images_router

router = APIRouter()

router.include_router(images_router)


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "0.1.0"}
