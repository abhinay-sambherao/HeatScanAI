from __future__ import annotations

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://evh:evh_secret@localhost:5432/evh_heatscan",
        description="Async PostgreSQL connection string",
    )
    DATABASE_URL_SYNC: str = Field(
        default="postgresql://evh:evh_secret@localhost:5432/evh_heatscan",
        description="Sync PostgreSQL connection string for Alembic",
    )
    JWT_SECRET_KEY: str = Field(
        default="change-me-in-production-use-a-real-secret",
        description="Secret key for JWT token signing",
    )
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT signing algorithm")
    JWT_EXPIRE_MINUTES: int = Field(
        default=1440, description="JWT token expiry in minutes (24h)"
    )
    ALLOWED_ORIGINS: str = Field(
        default="http://localhost:3000,http://localhost:8000,http://127.0.0.1:8000,null",
        description="Comma-separated allowed CORS origins",
    )
    ALLOWED_ORIGINS_REGEX: str = Field(
        default=r"https://(.*\.)?netlify\.app|https://(.*\.)?abhiinayy\.in|https://.*\.lhr\.life|https://.*\.trycloudflare\.com",
        description="Regex of additional allowed CORS origins (e.g. Netlify preview/tunnel hosts)",
    )
    EPREL_BASE_URL: str = Field(
        default="https://eprel.ec.europa.eu",
        description="EPREL API base URL",
    )
    EPREL_API_KEY: str = Field(
        default="",
        description="EPREL Public API key. Used only for list endpoints that return >1 model. Add to .env as EPREL_API_KEY=your-key",
    )
    MAX_UPLOAD_SIZE_MB: int = Field(default=20, description="Max file upload size in MB")
    OCR_CONFIDENCE_THRESHOLD: float = Field(
        default=0.5, description="Minimum OCR confidence to accept"
    )
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    CRAWL_SCHEDULE_ENABLED: bool = Field(
        default=False,
        description="Enable the daily EPREL re-crawl scheduler (default off)",
    )
    CRAWL_SCHEDULE_HOUR: int = Field(
        default=3, ge=0, le=23, description="Daily crawl hour (UTC)"
    )
    CRAWL_SCHEDULE_MINUTE: int = Field(
        default=0, ge=0, le=59, description="Daily crawl minute (UTC)"
    )

    @property
    def allowed_origins_list(self) -> list[str]:
        """Parse comma-separated origins into a list."""
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
