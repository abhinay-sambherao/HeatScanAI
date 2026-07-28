"""EPREL crawler service: fetches product data from the EU EPREL public API.

The EPREL public API at https://eprel.ec.europa.eu/api/products/{group}
returns JSON without authentication when accessed with browser-like headers.
Data is open government (Open Data Directive 2019/1024).
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.product import Product
from app.models.manufacturer import Manufacturer
from app.models.category import Category
from app.models.crawler_log import CrawlerLog
from app.core.logging import get_logger

logger = get_logger("crawler")

EPREL_BASE = "https://eprel.ec.europa.eu/api"
PAGE_SIZE = 25
RATE_LIMIT_DELAY = 0.5

EPREL_PRODUCT_GROUPS = [
    {"name": "Space heaters (heat pumps, gas, oil, combination)", "slug": "spaceheaters"},
    {"name": "Local space heaters (stoves, fireplaces)", "slug": "localspaceheaters"},
    {"name": "Solid fuel boilers (biomass, pellet)", "slug": "solidfuelboilers"},
    {"name": "Water heaters", "slug": "waterheaters"},
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Referer": "https://eprel.ec.europa.eu/",
}

# Mapping from EPREL type/category fields to our category names
EPREL_TYPE_TO_CATEGORY: dict[str, str] = {
    "HEAT_PUMP": "Heat pumps",
    "GAS_BOILER": "Gas boilers",
    "OIL_BOILER": "Oil boilers",
    "BIOMASS_BOILER": "Biomass boilers",
    "SOLAR_HEATER": "Solar thermal collectors",
    "COMBINATION_HEATER": "Combination heaters",
    "ELECTRIC_BOILER": "Electric boilers",
    "WARM_AIR_HEATER": "Warm air heaters",
}

# Mapping from EPREL type to fuel type
EPREL_TYPE_TO_FUEL: dict[str, str] = {
    "HEAT_PUMP": "electricity",
    "GAS_BOILER": "gas",
    "OIL_BOILER": "oil",
    "BIOMASS_BOILER": "biomass",
    "SOLAR_HEATER": "solar",
    "COMBINATION_HEATER": "gas",
    "ELECTRIC_BOILER": "electricity",
    "WARM_AIR_HEATER": "gas",
}

# Group-level fallback fuel types when type field is missing
GROUP_FUEL_FALLBACK: dict[str, str] = {
    "localspaceheaters": "biomass",
    "solidfuelboilers": "biomass",
    "waterheaters": "electricity",
}

GROUP_CATEGORY_FALLBACK: dict[str, str] = {
    "localspaceheaters": "Local space heaters",
    "solidfuelboilers": "Biomass boilers",
    "waterheaters": "Water heaters",
}


def _map_energy_class(raw: str | None) -> str | None:
    """Normalize EPREL energy class codes to standard labels.

    EPREL uses 'APP' for A++, 'APPP' for A+++, 'AP' for A+, etc.
    """
    if not raw:
        return None
    mapping = {
        "APPP": "A+++",
        "APP": "A++",
        "AP": "A+",
    }
    return mapping.get(raw, raw)


def _map_fuel_type(eprel_type: str | None, group_slug: str) -> str | None:
    """Determine fuel type from EPREL type field or group fallback."""
    if eprel_type and eprel_type in EPREL_TYPE_TO_FUEL:
        return EPREL_TYPE_TO_FUEL[eprel_type]
    return GROUP_FUEL_FALLBACK.get(group_slug)


def _map_category(eprel_type: str | None, group_slug: str) -> str | None:
    """Determine category name from EPREL type field or group fallback."""
    if eprel_type and eprel_type in EPREL_TYPE_TO_CATEGORY:
        return EPREL_TYPE_TO_CATEGORY[eprel_type]
    return GROUP_CATEGORY_FALLBACK.get(group_slug)


def _extract_heat_output(hit: dict[str, Any]) -> str | None:
    """Extract heat output as a formatted string from the EPREL hit."""
    output = hit.get("ratedHeatOutput")
    if output is not None:
        return f"{output} kW"
    return None


def _extract_manufacturer_name(hit: dict[str, Any]) -> str:
    """Extract manufacturer name, preferring organisation title over trademark."""
    org = hit.get("organisation", {})
    title = org.get("organisationTitle") if org else None
    if title:
        return title.strip()
    trademark = hit.get("supplierOrTrademark")
    if trademark:
        return trademark.strip()
    return "Unknown"


async def _parse_product_hit(
    hit: dict,
    group_slug: str,
    manufacturer_cache: dict,
    category_cache: dict,
    db: AsyncSession,
) -> dict | None:
    """Parse a single EPREL API hit into a product dict ready for upsert.

    Returns None if the hit is missing critical fields.
    """
    eprel_id = hit.get("eprelRegistrationNumber")
    if not eprel_id:
        return None

    model = hit.get("modelIdentifier", "").strip()
    if not model:
        return None

    manufacturer_name = _extract_manufacturer_name(hit)
    energy_class = _map_energy_class(hit.get("energyClass"))
    heat_output = _extract_heat_output(hit)
    eprel_type = hit.get("type")
    fuel_type = _map_fuel_type(eprel_type, group_slug)
    category_name = _map_category(eprel_type, group_slug)

    # Resolve manufacturer
    mfr_key = manufacturer_name.lower()
    if mfr_key not in manufacturer_cache:
        stmt = select(Manufacturer).where(Manufacturer.name == manufacturer_name)
        existing = (await db.execute(stmt)).scalar_one_or_none()
        if existing:
            manufacturer_cache[mfr_key] = existing
        else:
            mfr = Manufacturer(id=uuid.uuid4(), name=manufacturer_name)
            db.add(mfr)
            await db.flush()
            manufacturer_cache[mfr_key] = mfr
    manufacturer = manufacturer_cache[mfr_key]

    # Resolve category
    category = None
    if category_name:
        cat_key = category_name.lower()
        if cat_key not in category_cache:
            stmt = select(Category).where(Category.name == category_name)
            existing = (await db.execute(stmt)).scalar_one_or_none()
            if existing:
                category_cache[cat_key] = existing
            else:
                cat = Category(id=uuid.uuid4(), name=category_name, eprel_category_id=group_slug)
                db.add(cat)
                await db.flush()
                category_cache[cat_key] = cat
        category = category_cache[cat_key]

    return {
        "eprel_id": str(eprel_id),
        "model": model,
        "manufacturer_id": manufacturer.id,
        "category_id": category.id if category else None,
        "supplier": hit.get("supplierOrTrademark", "").strip() or None,
        "energy_class": energy_class,
        "heat_output": heat_output,
        "fuel_type": fuel_type,
        "raw_json": hit,
    }


async def _fetch_page(client: httpx.AsyncClient, group_slug: str, page: int) -> dict:
    """Fetch a single page of products from the EPREL API."""
    url = f"/products/{group_slug}"
    params = {"page": page, "size": PAGE_SIZE}
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = await client.get(url, params=params, timeout=30.0)
            if response.status_code == 403:
                logger.warning("eprel_forbidden", group=group_slug, page=page)
                return {"size": 0, "hits": []}
            response.raise_for_status()
            return response.json()
        except (httpx.HTTPStatusError, httpx.RequestError) as exc:
            logger.warning(
                "fetch_failed",
                group=group_slug,
                page=page,
                attempt=attempt + 1,
                error=str(exc),
            )
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
            else:
                raise


async def run_crawler(db: AsyncSession, max_pages_per_group: int = 0) -> CrawlerLog:
    """Execute the EPREL crawler across all heating product groups.

    Fetches real product data from the EU EPREL public API, parses JSON
    responses, and upserts products into the database. Never duplicates
    products by eprel_id.

    Args:
        db: Async database session.
        max_pages_per_group: Max pages to fetch per group (0 = unlimited).
            Each page has 25 products. e.g. 40 pages = 1000 products/group.

    Returns:
        The completed CrawlerLog entry with record count and status.
    """
    log = CrawlerLog(
        id=uuid.uuid4(),
        started_at=datetime.now(timezone.utc),
        status="running",
    )
    db.add(log)
    await db.flush()

    total_records = 0
    total_skipped = 0
    errors: list[str] = []

    manufacturer_cache: dict[str, Manufacturer] = {}
    category_cache: dict[str, Category] = {}

    async with httpx.AsyncClient(headers=HEADERS, base_url=EPREL_BASE) as client:
        for group in EPREL_PRODUCT_GROUPS:
            group_slug = group["slug"]
            group_name = group["name"]
            try:
                first_page = await _fetch_page(client, group_slug, 0)
                total_in_group = first_page.get("size", 0)
                hits = first_page.get("hits", [])
                logger.info(
                    "group_started",
                    group=group_name,
                    total=total_in_group,
                )

                if total_in_group == 0 and not hits:
                    continue

                total_pages = (total_in_group + PAGE_SIZE - 1) // PAGE_SIZE
                pages_to_fetch = total_pages if max_pages_per_group == 0 else min(total_pages, max_pages_per_group)

                for page_num in range(pages_to_fetch):
                    if page_num > 0:
                        await asyncio.sleep(RATE_LIMIT_DELAY)
                        page_data = await _fetch_page(client, group_slug, page_num)
                        hits = page_data.get("hits", [])

                    if not hits:
                        break

                    for hit in hits:
                        product_data = await _parse_product_hit(
                            hit, group_slug, manufacturer_cache, category_cache, db
                        )
                        if product_data is None:
                            total_skipped += 1
                            continue

                        existing_stmt = select(Product).where(
                            Product.eprel_id == product_data["eprel_id"]
                        )
                        existing = (
                            await db.execute(existing_stmt)
                        ).scalar_one_or_none()

                        if existing:
                            existing.model = product_data["model"]
                            existing.supplier = product_data["supplier"]
                            existing.energy_class = product_data["energy_class"]
                            existing.heat_output = product_data["heat_output"]
                            existing.fuel_type = product_data["fuel_type"]
                            existing.category_id = product_data["category_id"]
                            existing.raw_json = product_data["raw_json"]
                        else:
                            product = Product(
                                id=uuid.uuid4(),
                                eprel_id=product_data["eprel_id"],
                                manufacturer_id=product_data["manufacturer_id"],
                                category_id=product_data["category_id"],
                                model=product_data["model"],
                                supplier=product_data["supplier"],
                                energy_class=product_data["energy_class"],
                                heat_output=product_data["heat_output"],
                                fuel_type=product_data["fuel_type"],
                                raw_json=product_data["raw_json"],
                            )
                            db.add(product)
                            total_records += 1

                    await db.flush()

                logger.info(
                    "group_complete",
                    group=group_name,
                    fetched=pages_to_fetch * PAGE_SIZE,
                    total_records=total_records,
                )
                await db.commit()

            except Exception as exc:
                logger.error(
                    "group_failed",
                    group=group_name,
                    error=str(exc),
                )
                errors.append(f"{group_name}: {exc}")

    log.finished_at = datetime.now(timezone.utc)
    log.records_count = total_records
    log.status = "success" if not errors else "partial"
    log.error_message = "; ".join(errors) if errors else None
    log.category = "all"

    await db.flush()
    logger.info(
        "crawler_complete",
        records=total_records,
        skipped=total_skipped,
        errors=len(errors),
    )
    return log
