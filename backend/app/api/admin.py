"""Admin dashboard endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.ocr_result import OCRResult
from app.models.crawler_log import CrawlerLog
from app.models.product import Product
from app.models.manufacturer import Manufacturer

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/dashboard")
async def admin_dashboard(db: AsyncSession = Depends(get_db)) -> dict:
    """Summary statistics for the admin dashboard."""
    product_count = (await db.execute(select(func.count()).select_from(Product))).scalar() or 0
    manufacturer_count = (await db.execute(select(func.count()).select_from(Manufacturer))).scalar() or 0
    scan_count = (await db.execute(select(func.count()).select_from(OCRResult))).scalar() or 0

    avg_conf_stmt = select(func.avg(OCRResult.confidence))
    avg_confidence = (await db.execute(avg_conf_stmt)).scalar() or 0.0

    last_crawl_stmt = (
        select(CrawlerLog)
        .order_by(CrawlerLog.started_at.desc())
        .limit(1)
    )
    last_crawl = (await db.execute(last_crawl_stmt)).scalar_one_or_none()

    failed_jobs_stmt = select(func.count()).select_from(CrawlerLog).where(
        CrawlerLog.status.in_(["failed", "partial"])
    )
    failed_jobs = (await db.execute(failed_jobs_stmt)).scalar() or 0

    return {
        "total_products": product_count,
        "total_manufacturers": manufacturer_count,
        "total_scans": scan_count,
        "average_confidence": round(float(avg_confidence), 2),
        "last_crawl": {
            "status": last_crawl.status if last_crawl else None,
            "records": last_crawl.records_count if last_crawl else 0,
            "finished_at": last_crawl.finished_at.isoformat() if last_crawl and last_crawl.finished_at else None,
        },
        "failed_crawler_jobs": failed_jobs,
    }


@router.get("/ocr-history")
async def ocr_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Paginated OCR scan history."""
    count_stmt = select(func.count()).select_from(OCRResult)
    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = (
        select(OCRResult)
        .order_by(OCRResult.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    scans = result.scalars().all()

    return {
        "items": [
            {
                "id": str(s.id),
                "filename": s.filename,
                "confidence": s.confidence,
                "latitude": s.latitude,
                "longitude": s.longitude,
                "address": s.address,
                "city": s.city,
                "installation_year": s.installation_year,
                "created_at": s.created_at.isoformat(),
            }
            for s in scans
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/failed-jobs")
async def failed_jobs(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List failed or partial crawler jobs."""
    stmt = (
        select(CrawlerLog)
        .where(CrawlerLog.status.in_(["failed", "partial"]))
        .order_by(CrawlerLog.started_at.desc())
        .limit(50)
    )
    result = await db.execute(stmt)
    jobs = result.scalars().all()

    return {
        "items": [
            {
                "id": str(j.id),
                "started_at": j.started_at.isoformat(),
                "finished_at": j.finished_at.isoformat() if j.finished_at else None,
                "records_count": j.records_count,
                "status": j.status,
                "error_message": j.error_message,
                "category": j.category,
            }
            for j in jobs
        ]
    }
