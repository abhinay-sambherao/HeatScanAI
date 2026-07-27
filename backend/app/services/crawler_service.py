from __future__ import annotations

"""EPREL crawler service: async HTTP client for fetching product data
from the European Product Register for Energy Labelling."""

import asyncio
import uuid
from datetime import datetime, timezone

import httpx
from bs4 import BeautifulSoup
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.product import Product
from app.models.manufacturer import Manufacturer
from app.models.category import Category
from app.models.crawler_log import CrawlerLog
from app.core.logging import get_logger

logger = get_logger("crawler")

EPREL_CATEGORIES = [
    {"name": "Gas boilers", "eprel_id": "491"},
    {"name": "Oil boilers", "eprel_id": "492"},
    {"name": "Heat pumps", "eprel_id": "494"},
    {"name": "Combination heaters", "eprel_id": "495"},
]

RATE_LIMIT_DELAY = 1.0  # seconds between requests


async def _fetch_page(client: httpx.AsyncClient, url: str) -> str:
    """Fetch a single page with retry logic for transient failures."""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = await client.get(url, timeout=30.0)
            response.raise_for_status()
            return response.text
        except (httpx.HTTPStatusError, httpx.RequestError) as exc:
            logger.warning("fetch_failed", url=url, attempt=attempt + 1, error=str(exc))
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
            else:
                raise


def _parse_products(html: str, manufacturer_id: uuid.UUID, category_id: uuid.UUID) -> list[dict]:
    """Parse EPREL product listing HTML into structured product dicts."""
    soup = BeautifulSoup(html, "html.parser")
    products = []

    rows = soup.select("table tbody tr, .product-item, .result-item")

    for row in rows:
        try:
            eprel_id_el = row.select_one("[data-eprel-id], .eprel-id, td:first-child")
            model_el = row.select_one(".model, td:nth-child(2)")
            energy_el = row.select_one(".energy-class, td:nth-child(3)")
            supplier_el = row.select_one(".supplier, td:nth-child(4)")

            eprel_id = eprel_id_el.get_text(strip=True) if eprel_id_el else None
            if not eprel_id:
                continue

            products.append({
                "eprel_id": eprel_id,
                "manufacturer_id": manufacturer_id,
                "category_id": category_id,
                "model": model_el.get_text(strip=True) if model_el else "Unknown",
                "energy_class": energy_el.get_text(strip=True) if energy_el else None,
                "supplier": supplier_el.get_text(strip=True) if supplier_el else None,
                "raw_html": str(row),
            })
        except Exception as exc:
            logger.warning("parse_row_error", error=str(exc))
            continue

    return products


async def _get_or_create_manufacturer(
    db: AsyncSession, name: str
) -> Manufacturer:
    """Get an existing manufacturer or create a new one."""
    stmt = select(Manufacturer).where(Manufacturer.name == name)
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()
    if existing:
        return existing

    mfr = Manufacturer(id=uuid.uuid4(), name=name)
    db.add(mfr)
    await db.flush()
    return mfr


async def _get_or_create_category(
    db: AsyncSession, name: str, eprel_id: str | None = None
) -> Category:
    """Get an existing category or create a new one."""
    stmt = select(Category).where(Category.name == name)
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()
    if existing:
        return existing

    cat = Category(id=uuid.uuid4(), name=name, eprel_category_id=eprel_id)
    db.add(cat)
    await db.flush()
    return cat


async def run_crawler(db: AsyncSession) -> CrawlerLog:
    """Execute the EPREL crawler across all configured categories.

    Steps:
        1. Create a CrawlerLog entry (status=running)
        2. For each category, fetch product listings with pagination
        3. Parse and upsert products (never duplicate by eprel_id)
        4. Update CrawlerLog with final status and record count

    Returns:
        The completed CrawlerLog entry.
    """
    log = CrawlerLog(
        id=uuid.uuid4(),
        started_at=datetime.now(timezone.utc),
        status="running",
    )
    db.add(log)
    await db.flush()

    total_records = 0
    errors = []

    async with httpx.AsyncClient(
        base_url=settings.EPREL_BASE_URL,
        headers={"User-Agent": "EVH-Heatscan-Crawler/1.0"},
    ) as client:
        for cat_config in EPREL_CATEGORIES:
            try:
                category = await _get_or_create_category(
                    db, cat_config["name"], cat_config["eprel_id"]
                )

                page = 1
                has_more = True

                while has_more:
                    url = f"/api/products?page={page}&category={cat_config['eprel_id']}"
                    html = await _fetch_page(client, url)
                    products = _parse_products(html, uuid.uuid4(), category.id)

                    if not products:
                        has_more = False
                        break

                    for prod_data in products:
                        existing_stmt = select(Product).where(
                            Product.eprel_id == prod_data["eprel_id"]
                        )
                        existing = (await db.execute(existing_stmt)).scalar_one_or_none()

                        if existing:
                            existing.model = prod_data["model"]
                            existing.energy_class = prod_data["energy_class"]
                            existing.supplier = prod_data["supplier"]
                            existing.raw_json = {"raw_html": prod_data["raw_html"]}
                        else:
                            product = Product(
                                id=uuid.uuid4(),
                                eprel_id=prod_data["eprel_id"],
                                manufacturer_id=prod_data["manufacturer_id"],
                                category_id=prod_data["category_id"],
                                model=prod_data["model"],
                                energy_class=prod_data["energy_class"],
                                supplier=prod_data["supplier"],
                                raw_json={"raw_html": prod_data["raw_html"]},
                            )
                            db.add(product)
                            total_records += 1

                    await db.flush()
                    page += 1
                    await asyncio.sleep(RATE_LIMIT_DELAY)

                    if page > 50:
                        has_more = False

            except Exception as exc:
                logger.error(
                    "category_crawl_failed",
                    category=cat_config["name"],
                    error=str(exc),
                )
                errors.append(f"{cat_config['name']}: {exc}")

    log.finished_at = datetime.now(timezone.utc)
    log.records_count = total_records
    log.status = "success" if not errors else "partial"
    log.error_message = "; ".join(errors) if errors else None
    log.category = "all"

    await db.flush()
    logger.info("crawler_complete", records=total_records, errors=len(errors))
    return log
