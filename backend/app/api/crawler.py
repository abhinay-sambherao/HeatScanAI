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
from app.services.retail_crawler import run_retail_crawler
from app.models.crawler_log import CrawlerLog

router = APIRouter(prefix="/crawler", tags=["Crawler"])


async def _run_crawler_background(
    log_id: uuid.UUID, max_pages: int, include_extras: bool, groups: list[str] | None
) -> None:
    """Run crawler in background using a fresh database session."""
    async with async_session_factory() as db:
        try:
            # Update the existing log entry to running
            stmt = select(CrawlerLog).where(CrawlerLog.id == log_id)
            log = (await db.execute(stmt)).scalar_one_or_none()
            if log:
                log.status = "running"
                await db.flush()

            result = await run_crawler(
                db,
                max_pages_per_group=max_pages,
                include_extras=include_extras,
                only_groups=groups,
            )

            # Merge the results into the original log
            log.status = result.status
            log.records_count = result.records_count
            log.finished_at = result.finished_at
            log.error_message = result.error_message
            await db.commit()
        except Exception as exc:
            if log:
                log.status = "failed"
                log.error_message = str(exc)
                log.finished_at = datetime.now(timezone.utc)
                await db.commit()
            else:
                await db.rollback()


@router.post("/run", response_model=CrawlerRunResponse)
async def trigger_crawler(
    max_pages: int = Query(40, ge=0, le=10000, description="Max pages per group (0=unlimited, 40=1000 products)"),
    include_extras: bool = Query(False, description="Include control/solar groups (off by default)"),
    groups: str = Query(None, description="Comma-separated group slugs to crawl (e.g. spaceheaters,waterheaters). Overrides include_extras."),
    db: AsyncSession = Depends(get_db),
) -> CrawlerRunResponse:
    """Trigger an EPREL crawl job. Runs asynchronously in the background."""
    group_list = [g.strip() for g in groups.split(",") if g.strip()] if groups else None
    log = CrawlerLog(
        id=uuid.uuid4(),
        started_at=datetime.now(timezone.utc),
        status="queued",
        category="all",
    )
    db.add(log)
    await db.flush()

    asyncio.create_task(_run_crawler_background(log.id, max_pages, include_extras, group_list))

    return CrawlerRunResponse(
        job_id=log.id,
        status="queued",
        message=f"Crawler job queued (max_pages={max_pages}/group). Check /crawler/logs for status.",
    )


@router.post("/retail")
async def trigger_retail_crawler(
    limit: int = Query(0, ge=0, description="Max product pages to fetch (0=unlimited, full crawl)"),
    db: AsyncSession = Depends(get_db),
) -> CrawlerRunResponse:
    """Trigger a retail crawl (heizungsdiscount24) into retail_products.

    Enriches scan results with purchasable reseller listings (URL + price).
    Runs asynchronously; check /crawler/logs for status (category=retail).
    """
    log = CrawlerLog(
        id=uuid.uuid4(),
        started_at=datetime.now(timezone.utc),
        status="queued",
        category="retail",
    )
    db.add(log)
    await db.flush()
    asyncio.create_task(_run_retail_background(log.id, limit))
    return CrawlerRunResponse(
        job_id=log.id,
        status="queued",
        message=f"Retail crawler job queued (limit={limit or 'full'}). Check /crawler/logs for status.",
    )


async def _run_retail_background(log_id: uuid.UUID, limit: int) -> None:
    """Run the retail crawl in the background, updating the shared log row."""
    async with async_session_factory() as db:
        stmt = select(CrawlerLog).where(CrawlerLog.id == log_id)
        log = (await db.execute(stmt)).scalar_one_or_none()
        try:
            if log:
                log.status = "running"
                await db.flush()
            stats = await run_retail_crawler(limit=limit)
            if log:
                log.status = "finished"
                log.records_count = stats.get("new", 0)
                log.finished_at = datetime.now(timezone.utc)
                await db.commit()
        except Exception as exc:
            if log:
                log.status = "failed"
                log.error_message = str(exc)
                log.finished_at = datetime.now(timezone.utc)
                await db.commit()
            else:
                await db.rollback()


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
