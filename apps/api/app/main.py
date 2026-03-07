"""FastAPI application entry point."""

import os
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import get_settings
from app.core.db import (
    close_mongo_connection,
    close_redis_connection,
    connect_to_mongo,
    connect_to_redis,
)
from app.domains.games.router import router as games_router
from app.domains.images.router import router as images_router
from app.domains.leaderboard.router import router as leaderboard_router
from app.domains.users.router import router as users_router

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Manage application lifespan events."""
    # Startup
    await connect_to_mongo()
    await connect_to_redis()

    settings = get_settings()
    if settings.feature_multiplayer:
        from app.container import container
        from app.domains.multiplayer.connection_manager import ConnectionManager
        from app.domains.multiplayer.repository import IMultiplayerGameRepository

        cm = container.resolve(ConnectionManager)
        await cm.start()

        repo = container.resolve(IMultiplayerGameRepository)
        await repo.ensure_indexes()

        logger.info("multiplayer_enabled")

    yield

    # Shutdown
    if settings.feature_multiplayer:
        from app.container import container
        from app.domains.multiplayer.connection_manager import ConnectionManager

        cm = container.resolve(ConnectionManager)
        await cm.stop()

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

    # Include domain routers under /v1 prefix
    app.include_router(games_router, prefix="/v1")
    app.include_router(images_router, prefix="/v1")
    app.include_router(leaderboard_router, prefix="/v1")
    app.include_router(users_router, prefix="/v1")

    # Conditionally register multiplayer router
    if settings.feature_multiplayer:
        from app.domains.multiplayer.router import router as multiplayer_router

        app.include_router(multiplayer_router, prefix="/v1")

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request,  # noqa: ARG001
        exc: StarletteHTTPException,
    ) -> Response | JSONResponse:
        """Handle HTTP exceptions with empty response for 404s."""
        if exc.status_code == 404:
            return Response(status_code=404)
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.get("/health")
    async def health_check() -> dict[str, str]:
        """Health check endpoint with version info."""
        return {
            "status": "healthy",
            "version": os.getenv("VERSION", "0.1.0"),
            "git_sha": os.getenv("GIT_SHA", "unknown"),
            "git_branch": os.getenv("GIT_BRANCH", "unknown"),
        }

    return app


# Configure structlog for JSON output
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

app = create_app()
