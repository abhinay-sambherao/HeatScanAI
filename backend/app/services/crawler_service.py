"""EPREL crawler service: fetches product data from the EU EPREL Public API.

Uses the authenticated EPREL API at https://eprel.ec.europa.eu/api/products/{group}
with an API key sent in the X-API-KEY header. The key is used only on list
endpoints (returning >1 model). Cached aggressively to stay under the 5 req/s limit.
"""

from __future__ import annotations

import asyncio
import io
import json
import re
import uuid
import zipfile
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
from app.services.brand_normalizer import (
    normalize_brand,
    is_valid_brand,
    extract_brand_from_raw,
)
from rapidfuzz import fuzz as fuzz_engine

logger = get_logger("crawler")

EPREL_BASE = "https://eprel.ec.europa.eu/api"
PAGE_SIZE = 25
# 4 req/s stays safely under EPREL's 5 req/s rate limit
RATE_LIMIT_DELAY = 0.25

EPREL_PRODUCT_GROUPS = [
    {"name": "Space heaters (heat pumps, gas, oil, combination)", "slug": "spaceheaters"},
    {"name": "Local space heaters (stoves, fireplaces)", "slug": "localspaceheaters"},
    {"name": "Solid fuel boilers (biomass, pellet)", "slug": "solidfuelboilers"},
    {"name": "Water heaters", "slug": "waterheaters"},
    {"name": "Hot water storage tanks", "slug": "hotwaterstoragetanks"},
]

# Additional real single-product groups: temperature controls and solar
# devices. The remaining EPREL extra groups (solidfuelboilerpackages,
# spaceheaterpackages, waterheaterpackages) are *package registrations* that
# store the full composition string in supplierOrTrademark ("Wolf Sonnenpaket
# Ölbrennwert COB-15 ; 3x Kollektor F3-1 ..."). Those are not nameplate-
# matchable single units and are excluded from the crawl entirely — they would
# only add junk brands and cost a large pointless download.
EPREL_EXTRA_GROUPS = [
    {"name": "Space heater temperature controls", "slug": "spaceheatertemperaturecontrol"},
    {"name": "Space heater solar devices", "slug": "spaceheatersolardevice"},
    {"name": "Water heater solar devices", "slug": "waterheatersolardevices"},
]

# Every group this app may crawl. HeizungScan is a heating-systems lead-gen
# tool, so the catalogue is deliberately restricted to *heating* appliances
# (boilers, heat pumps, water heaters, storage, plus controls/solar) and to
# reversible units that also heat (EPREL registers these under "space
# heaters"). Standalone air-conditioning / cooling-only units live in EPREL's
# separate `airconditioners` family and are NEVER crawled. This allow-list is
# enforced as a guard so a caller cannot accidentally pull in a non-heating
# group via the `groups`/`only_groups` params.
HEATING_ONLY_GROUP_SLUGS: frozenset[str] = frozenset(
    {g["slug"] for g in EPREL_PRODUCT_GROUPS + EPREL_EXTRA_GROUPS}
)

# Full pagination walks every offset. The old offset-sampling approach only
# touched a handful of offsets per group and was heavily lossy.

HEADERS = {
    "User-Agent": "FastAPI-HeatScanAI/1.0 (EPREL integration; contact via EVH GmbH)",
    "Accept": "application/json",
}

# Conditionally add API key — used only when set in .env
if settings.EPREL_API_KEY:
    HEADERS["X-API-KEY"] = settings.EPREL_API_KEY

# Mapping from EPREL type/category fields to our category names
EPREL_TYPE_TO_CATEGORY: dict[str, str] = {
    "HEAT_PUMP": "Heat pumps",
    "LOW_TEMPERATURE_HEAT_PUMP": "Heat pumps",
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
    "spaceheatertemperaturecontrol": "Temperature controls",
    "spaceheatersolardevice": "Solar thermal collectors",
    "waterheatersolardevices": "Solar thermal collectors",
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


def _is_plausible_model(model: str) -> bool:
    """Return True if the model string is a plausible product model.

    Rejects:
    - Pure numeric / trivial short codes ("10", "AC", "A", "2C")
    - Composition strings containing ';' or "Paket"/"module"
    - Model strings that are clearly gas/flue codes or postal codes
    """
    if not model or not model.strip():
        return False
    model = model.strip()
    # Trivial 1-2 char codes
    if len(model) < 3:
        return False
    # Pure numerics of any length < 6 (e.g. "10", "2024", "900")
    if re.match(r"^\d{1,5}$", model):
        return False
    # Composition strings
    if any(m in model.lower() for m in ["paket", "sonnenpaket", "module kit"]):
        return False
    if ";" in model:
        return False
    return True


def _extract_kw(value: Any) -> float | None:
    """Parse a heat-output value (number or "17.2 kW" string) into kW."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        m = re.search(r"(\d+(?:[.,]\d+)?)", value.replace(",", "."))
        if m:
            return float(m.group(1))
    return None


def _kw_in_range(detected_kw: float, hit_kw: float) -> bool:
    """True if the EPREL heat output plausibly matches the nameplate value.

    Tolerance is the larger of 25% relative or 2 kW absolute, so small units
    (e.g. 2 kW heat pumps) are not dropped by a percentage band alone.
    """
    band = max(2.0, 0.25 * detected_kw)
    return abs(hit_kw - detected_kw) <= band


def _extract_manufacturer_name(hit: dict[str, Any]) -> str:
    """Extract the brand/manufacturer name shown on a nameplate.

    Uses the brand normalizer to map EPREL's inconsistent names (legal
    entities, registrants, case variants) to canonical brand names.

    EPREL's `organisation` is the entity that *registered* the product — often
    an importer or distributor. The brand on the nameplate is
    `supplierOrTrademark`, but EPREL sometimes stores the legal entity there
    too (e.g. "Viessmann Climate Solutions SE" instead of "Viessmann").
    """
    brand = extract_brand_from_raw(hit)
    if brand:
        return brand
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

    model = (hit.get("modelIdentifier") or "").strip()
    if not model:
        return None

    # Reject garbled / composition model strings that would pollute matching:
    # trivial 1-2 char codes ("A", "AC", "10"), composition strings with ';'
    # or "Paket", and pure-numeric strings that are really gas/flue codes.
    if not _is_plausible_model(model):
        return None

    manufacturer_name = _extract_manufacturer_name(hit)
    energy_class = _map_energy_class(hit.get("energyClass"))
    heat_output = _extract_heat_output(hit)
    eprel_type = hit.get("type")
    fuel_type = _map_fuel_type(eprel_type, group_slug)
    category_name = _map_category(eprel_type, group_slug)
    registrant = (hit.get("organisation") or {}).get("organisationTitle")
    registrant = registrant.strip() if registrant else None

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
        "supplier": registrant,
        "energy_class": energy_class,
        "heat_output": heat_output,
        "fuel_type": fuel_type,
        "raw_json": hit,
    }


async def _fetch_page(
    client: httpx.AsyncClient, group_slug: str, page: int = 1, limit: int = PAGE_SIZE
) -> dict:
    """Fetch one page of products from the EPREL list endpoint.

    The list endpoint paginates via the `_page`/`_limit` query params (1-based
    page, max 100 per page). The old `offset`/`size` params are ignored by the
    API and always return the same first page.
    """
    url = f"/products/{group_slug}"
    params = {"_page": max(int(page), 1), "_limit": limit}
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


async def _fetch_group_export(client: httpx.AsyncClient, group_slug: str) -> list[dict]:
    """Download the daily full export ZIP for a product group.

    EPREL publishes one ZIP per group at /api/exportProducts/{group} (redirects
    to /EprelPublicData/{group}.zip) containing a single JSON list with every
    registered model — old and current. This is the only reliable way to get the
    complete model-name list; the list endpoint only returns one page at a time.
    """
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = await client.get(
                f"/exportProducts/{group_slug}",
                timeout=180.0,
                follow_redirects=True,
            )
            response.raise_for_status()
            content = response.content
            if not content.startswith(b"PK"):
                raise httpx.HTTPStatusError(
                    f"Expected ZIP for {group_slug}, got {response.headers.get('content-type')}",
                    request=response.request,
                    response=response,
                )
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                member = archive.namelist()[0]
                with archive.open(member) as fh:
                    records = json.load(fh)
            logger.info(
                "export_loaded",
                group=group_slug,
                records=len(records),
                member=member,
            )
            return records
        except (httpx.HTTPStatusError, httpx.RequestError, zipfile.BadZipFile, json.JSONDecodeError) as exc:
            logger.warning(
                "export_failed",
                group=group_slug,
                attempt=attempt + 1,
                error=str(exc),
            )
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
            else:
                raise


async def run_crawler(
    db: AsyncSession,
    max_pages_per_group: int = 0,
    include_extras: bool = False,
    only_groups: list[str] | None = None,
) -> CrawlerLog:
    """Execute the EPREL crawler across all heating product groups.

    Downloads the daily full export ZIP for each group
    (GET /api/exportProducts/{group}) so the local product table becomes a
    complete model-name list. Never duplicates products by eprel_id.

    Args:
        db: Async database session.
        max_pages_per_group: Backward-compatible cap in "pages" (25 records
            each); e.g. 12 = max 300 records per group. 0 = fetch the entire
            group export.
        include_extras: Also crawl the control/solar groups. Package/control
            package registrations are excluded entirely (see EPREL_EXTRA_GROUPS).
        only_groups: If given, crawl only these group slugs. Lets an
            incremental run fetch just the missing groups instead of
            re-downloading every export ZIP. Takes precedence over
            include_extras.

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
        if only_groups:
            pool = {g["slug"]: g for g in EPREL_PRODUCT_GROUPS + EPREL_EXTRA_GROUPS}
            # Heating-only guard: ignore any requested non-heating group slug
            # (e.g. EPREL's airconditioners) rather than crawling it.
            heating_groups = [g for g in only_groups if g in HEATING_ONLY_GROUP_SLUGS]
            all_groups = [pool[slug] for slug in heating_groups if slug in pool]
        else:
            all_groups = EPREL_PRODUCT_GROUPS
            if include_extras:
                all_groups = all_groups + EPREL_EXTRA_GROUPS

        for group in all_groups:
            group_slug = group["slug"]
            group_name = group["name"]
            try:
                records = await _fetch_group_export(client, group_slug)
                logger.info(
                    "group_started",
                    group=group_name,
                    total=len(records),
                )
                if not records:
                    continue

                # Preload the set of eprel ids once per group so the common
                # all-new case avoids one SELECT per record.
                existing_ids = set(
                    (await db.execute(select(Product.eprel_id))).scalars().all()
                )

                # Backward-compatible cap: max_pages_per_group x 25 records.
                cap = max_pages_per_group * PAGE_SIZE if max_pages_per_group else 0
                processed = 0
                for hit in records:
                    if cap and processed >= cap:
                        break
                    product_data = await _parse_product_hit(
                        hit, group_slug, manufacturer_cache, category_cache, db
                    )
                    if product_data is None:
                        total_skipped += 1
                        continue
                    processed += 1

                    if product_data["eprel_id"] in existing_ids:
                        existing = (
                            await db.execute(
                                select(Product).where(
                                    Product.eprel_id == product_data["eprel_id"]
                                )
                            )
                        ).scalar_one_or_none()
                        if existing is None:
                            # Id was preloaded but row vanished (concurrent wipe).
                            db.add(
                                Product(
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
                            )
                            total_records += 1
                            continue
                        existing.manufacturer_id = product_data["manufacturer_id"]
                        existing.model = product_data["model"]
                        existing.supplier = product_data["supplier"]
                        existing.energy_class = product_data["energy_class"]
                        existing.heat_output = product_data["heat_output"]
                        existing.fuel_type = product_data["fuel_type"]
                        existing.category_id = product_data["category_id"]
                        existing.raw_json = product_data["raw_json"]
                    else:
                        db.add(
                            Product(
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
                        )
                        total_records += 1
                        existing_ids.add(product_data["eprel_id"])

                    if processed % 500 == 0:
                        # Commit in batches so long crawls stay visible/bounded.
                        await db.commit()
                        logger.info(
                            "group_progress",
                            group=group_name,
                            processed=processed,
                            records=total_records,
                        )

                await db.commit()
                logger.info(
                    "group_complete",
                    group=group_name,
                    records_in_group=total_records,
                )

            except Exception as exc:
                logger.error(
                    "group_failed",
                    group=group_name,
                    error=str(exc),
                )
                await db.rollback()
                # Flushed-but-uncommitted Manufacturer/Category rows are gone
                # from the DB after the rollback; drop cached references so a
                # later group never reuses a rolled-back id (FK violation).
                manufacturer_cache.clear()
                category_cache.clear()
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

async def search_and_add_product(
    db: AsyncSession,
    manufacturer: str | None,
    model: str | None,
    fuel_type: str | None = None,
    heat_output: str | None = None,
) -> list[dict]:
    """Search EPREL API for a product matching detected manufacturer/model.

    Called by the OCR service when no good local match is found. Searches
    EPREL product groups (restricted to the groups relevant for the detected
    fuel type, when known), fuzzy-matches against manufacturer and model, and
    adds new products to the database on-the-fly.

    Args:
        db: Database session.
        manufacturer: OCR-detected manufacturer name (or None).
        model: OCR-detected model number (or None).
        fuel_type: OCR-detected fuel type (gas/oil/electricity/biomass/solar).
            When known, only the EPREL groups that hold that fuel type are
            queried, avoiding up to 8x unnecessary API requests per scan.
        heat_output: OCR-detected heat output (e.g. "17.2 kW"). When known,
            EPREL hits whose rated heat output is far outside the detected
            value are skipped, so a generic model match (e.g. "Vitodens 200")
            is not polluted by entries with a different output rating.

    Returns:
        List of newly added product data dicts (same format as find_matches).
        Empty list if nothing was found or added.
    """
    if not manufacturer and not model:
        return []

    detected_kw = _extract_kw(heat_output)

    added: list[dict] = []
    manufacturer_cache: dict[str, Manufacturer] = {}
    category_cache: dict[str, Category] = {}

    # Pre-populate caches with existing data
    existing_mfrs = (await db.execute(select(Manufacturer))).scalars().all()
    for m in existing_mfrs:
        manufacturer_cache[m.name.lower()] = m
    existing_cats = (await db.execute(select(Category))).scalars().all()
    for c in existing_cats:
        category_cache[c.name.lower()] = c

    # Restrict the searched groups to those relevant for the detected fuel
    # type. When the fuel type is unknown, search all groups (backwards
    # compatible).
    fuel_to_groups: dict[str, list[str]] = {
        "gas": ["spaceheaters"],
        "oil": ["spaceheaters"],
        "electricity": ["spaceheaters", "waterheaters"],
        "biomass": ["solidfuelboilers", "localspaceheaters"],
        "solar": ["waterheaters"],
    }
    all_groups = EPREL_PRODUCT_GROUPS + EPREL_EXTRA_GROUPS
    if fuel_type in fuel_to_groups:
        wanted = set(fuel_to_groups[fuel_type])
        all_groups = [g for g in all_groups if g["slug"] in wanted]

    # Only search first few pages for speed (real-time OCR response)
    search_pages = [1, 2, 3]

    async with httpx.AsyncClient(headers=HEADERS, base_url=EPREL_BASE) as client:
        for group in all_groups:
            group_slug = group["slug"]
            for page in search_pages:
                try:
                    data = await _fetch_page(client, group_slug, page)
                    hits = data.get("hits", [])
                    if not hits:
                        continue

                    for hit in hits:
                        hit_model = hit.get("modelIdentifier", "")
                        hit_mfr = _extract_manufacturer_name(hit)
                        eprel_id = hit.get("eprelRegistrationNumber")
                        if not eprel_id or not hit_model:
                            continue

                        # Check if already in DB
                        existing = (await db.execute(
                            select(Product).where(Product.eprel_id == str(eprel_id))
                        )).scalar_one_or_none()
                        if existing:
                            continue

                        # Skip hits whose rated heat output clearly disagrees
                        # with the nameplate value (correctness over breadth).
                        hit_kw = _extract_kw(hit.get("ratedHeatOutput"))
                        if detected_kw is not None and hit_kw is not None:
                            if not _kw_in_range(detected_kw, hit_kw):
                                continue

                        # Fuzzy match against detected manufacturer/model
                        mfr_match = 0.0
                        if manufacturer:
                            mfr_match = fuzz_engine.token_sort_ratio(
                                manufacturer.lower(), hit_mfr.lower()
                            )
                        model_match = 0.0
                        if model:
                            model_match = fuzz_engine.token_sort_ratio(
                                model.lower(), hit_model.lower()
                            )

                        # Only add if strongly matching both fields
                        if mfr_match > 75 and model_match > 70:
                            product_data = await _parse_product_hit(
                                hit, group_slug, manufacturer_cache, category_cache, db
                            )
                            if product_data is None:
                                continue
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
                                source="EPREL API",
                                raw_json=product_data["raw_json"],
                            )
                            db.add(product)
                            await db.flush()
                            added.append({
                                "product_id": product.id,
                                "manufacturer": hit_mfr,
                                "model": hit_model,
                                "energy_class": product_data["energy_class"],
                                "fuel_type": product_data["fuel_type"],
                                "heat_output": product_data["heat_output"],
                                "score": 100.0,
                                "matched_attributes": {"eprel_search": {"score": 100.0, "target": hit_model}},
                                "reason": f"Found on EPREL: {hit_mfr} {hit_model}",
                            })
                            logger.info("added_on_demand", eprel_id=eprel_id, model=hit_model, manufacturer=hit_mfr)

                except Exception:
                    continue  # skip failed pages silently

    if added:
        await db.commit()

    return added
