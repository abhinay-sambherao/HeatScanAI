"""Crawler endpoints: trigger runs and view logs."""
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, async_session_factory
from app.schemas.crawler import CrawlerRunResponse, CrawlerLogOut, CrawlerLogList
from app.services.crawler_service import run_crawler
from app.models.crawler_log import CrawlerLog

router = APIRouter(prefix="/crawler", tags=["Crawler"])


async def _run_crawler_background() -> None:
    """Run crawler in background using a fresh database session."""
    async with async_session_factory() as db:
        try:
            await run_crawler(db)
            await db.commit()
        except Exception:
            await db.rollback()
            raise


@router.post("/run", response_model=CrawlerRunResponse)
async def trigger_crawler(
    db: AsyncSession = Depends(get_db),
) -> CrawlerRunResponse:
    """Trigger an EPREL crawl job. Runs asynchronously in the background."""
    log = CrawlerLog(
        id=uuid.uuid4(),
        started_at=datetime.now(timezone.utc),
        status="queued",
        category="all",
    )
    db.add(log)
    await db.flush()

    asyncio.create_task(_run_crawler_background())

    return CrawlerRunResponse(
        job_id=log.id,
        status="queued",
        message="Crawler job queued. Check /crawler/logs for status.",
    )


@router.get("/logs", response_model=CrawlerLogList)
async def get_crawler_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> CrawlerLogList:
    """Get paginated crawler run history."""
    count_stmt = select(func.count()).select_from(CrawlerLog)
    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = (
        select(CrawlerLog)
        .order_by(CrawlerLog.started_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    logs = list(result.scalars().all())

    return CrawlerLogList(
        items=[CrawlerLogOut.model_validate(log) for log in logs],
        total=total,
    )
