"""EVH Heating OCR & EPREL Intelligence Platform — FastAPI Application."""

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.config import settings
from app.core.logging import setup_logging, get_logger
from app.database import init_db
from app.scheduler import DailyCrawlerScheduler
from app.api import ocr, products, manufacturers, categories, crawler, health, admin

FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events."""
    setup_logging()
    logger = get_logger("startup")
    logger.info("starting_service", version="1.0.0")
    await init_db()
    logger.info("database_ready")
    scheduler = DailyCrawlerScheduler(
        settings.CRAWL_SCHEDULE_ENABLED,
        hour=settings.CRAWL_SCHEDULE_HOUR,
        minute=settings.CRAWL_SCHEDULE_MINUTE,
    )
    scheduler.start()
    yield
    await scheduler.stop()
    logger.info("shutting_down")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="EVH HeatScan AI Platform",
        description="OCR-powered heating system identification and EPREL product matching",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_origin_regex=settings.ALLOWED_ORIGINS_REGEX,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(ocr.router)
    app.include_router(products.router)
    app.include_router(manufacturers.router)
    app.include_router(categories.router)
    app.include_router(crawler.router)
    app.include_router(admin.router)

    @app.get("/")
    @app.get("/app")
    async def serve_frontend():
        """Serve the frontend SPA."""
        return FileResponse(str(FRONTEND_DIR / "index.html"))

    # Serve the rest of the static frontend (js/, css/, images/, index.html for
    # sub-paths) from the same FRONTEND_DIR. Any remaining path (e.g. /js/app.js,
    # /css/style.css) falls through to these files. Registered after all API
    # routers so the API endpoints always take precedence.
    app.mount(
        "/",
        StaticFiles(directory=str(FRONTEND_DIR), html=True),
        name="frontend",
    )

    return app


app = create_app()
