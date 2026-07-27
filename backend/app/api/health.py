"""Health and metrics endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.product import Product
from app.models.manufacturer import Manufacturer
from app.models.ocr_result import OCRResult
from app.models.crawler_log import CrawlerLog

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check() -> dict:
    """Simple health check endpoint."""
    return {"status": "healthy", "service": "evh-heatscan"}


@router.get("/metrics")
async def metrics(db: AsyncSession = Depends(get_db)) -> dict:
    """System metrics: product count, manufacturer count, scan count, etc."""
    product_count = (await db.execute(select(func.count()).select_from(Product))).scalar() or 0
    manufacturer_count = (await db.execute(select(func.count()).select_from(Manufacturer))).scalar() or 0
    scan_count = (await db.execute(select(func.count()).select_from(OCRResult))).scalar() or 0
    crawler_runs = (await db.execute(select(func.count()).select_from(CrawlerLog))).scalar() or 0

    last_scan_stmt = select(OCRResult.created_at).order_by(OCRResult.created_at.desc()).limit(1)
    last_scan_result = await db.execute(last_scan_stmt)
    last_scan = last_scan_result.scalar()

    return {
        "products": product_count,
        "manufacturers": manufacturer_count,
        "total_scans": scan_count,
        "crawler_runs": crawler_runs,
        "last_scan": last_scan.isoformat() if last_scan else None,
    }
