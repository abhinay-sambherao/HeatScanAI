from __future__ import annotations

import os
import sys
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from app.config import settings

DB_URL = settings.DATABASE_URL or os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./heatscan.db")

# Under pytest each anyio test runs on its own event loop. The default
# AsyncAdaptedQueuePool reuses asyncpg connections across loops, which fails
# on the next test's checkout ("attached to a different loop"). NullPool
# opens a fresh connection per session, so no pooled connection survives
# across loops. Production (uvicorn) never has "pytest" in sys.modules.
_running_tests = "pytest" in sys.modules

engine = create_async_engine(
    DB_URL,
    echo=False,
    pool_pre_ping=not _running_tests,
    poolclass=NullPool if _running_tests else None,
)

async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


async def init_db() -> None:
    """Create all tables if they don't exist."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that yields a database session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
