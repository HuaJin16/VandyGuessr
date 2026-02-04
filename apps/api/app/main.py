"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as api_v1_router
from app.config import get_settings
from app.core import not_found
from app.core.database import close_mongo_connection, connect_to_mongo
from app.core.redis import close_redis_connection, connect_to_redis


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Manage application lifespan events."""
    # Startup
    await connect_to_mongo()
    await connect_to_redis()

    yield

    # Shutdown
    await close_mongo_connection()
    await close_redis_connection()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        description="A GeoGuessr-style game for Vanderbilt University's campus",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(api_v1_router, prefix="/api/v1")

    @app.get("/", response_class=Response)
    async def root() -> Response:
        """Root endpoint - returns 404 as this is not a valid API endpoint."""
        return not_found()

    return app


app = create_app()
