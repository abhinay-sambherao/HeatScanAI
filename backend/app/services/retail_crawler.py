"""Crawler for retail listings from heizungsdiscount24.de.

Retail enrichment source: downloads the shop's product sitemaps, fetches each
heating-category product page, extracts the JSON-LD ``Product`` block, and
stores brand/model/name + reseller URL/price in ``retail_products``.

Scope guard: only heating-relevant categories are crawled and ``klimaanlagen``
(air conditioning) is excluded, keeping the platform heating-systems-only.
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import AsyncIterator, Dict, List, Optional

import httpx

from app.database import async_session_factory
from app.models.retail_product import RetailProduct
from app.services.brand_normalizer import normalize_brand
from app.ocr.parser import _extract_product_designation

logger = logging.getLogger(__name__)

SITEMAP_INDEX = "https://www.heizungsdiscount24.de/sitemap.xml"
PRODUCT_SITEMAPS = [
    "https://www.heizungsdiscount24.de/sitemaps/sitemap_products1.xml",
    "https://www.heizungsdiscount24.de/sitemaps/sitemap_products2.xml",
    "https://www.heizungsdiscount24.de/sitemaps/sitemap_products3.xml",
]
SOURCE = "heizungsdiscount24"

# First URL path segment => heating-relevant category (inclusive allow-list).
HEATING_CATEGORY_PATHS = {
    "gas-heizung",
    "waermepumpen",
    "oel-heizung",
    "holz-heizung",
    "luftheizer",
    "speichertechnik",
    "durchlauferhitzer",
    "wohnungsstationen",
    "regelungstechnik",
    "solartechnik",
    "solarrohr",
    "solarfluessigkeit",
    "fussbodenheizung",
}
# Pure air-conditioning => explicitly excluded (heating-only scope).
EXCLUDED_CATEGORY_PATHS = {"klimaanlagen"}

_CRAWL_DELAY = 0.25  # ~4 requests/sec, respectful of robots.txt (no crawl-delay set)
_TIMEOUT = httpx.Timeout(20.0)
_HEADERS = {
    "User-Agent": "HeatScanAI-crawler/1.0 (+contact: evh@example.com)",
    "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
}

JSONLD_RE = re.compile(r'<script type="application/ld\+json"[^>]*>(.*?)</script>', re.S)


def _is_heating_url(url: str) -> bool:
    """True if the product URL belongs to a heating-relevant category."""
    m = re.search(r"heizungsdiscount24\.de/([a-z0-9-]+)/", url)
    if not m:
        return False
    slug = m.group(1)
    if slug in EXCLUDED_CATEGORY_PATHS:
        return False
    return slug in HEATING_CATEGORY_PATHS


def parse_product_jsonld(html: str) -> Optional[Dict]:
    """Extract the JSON-LD ``Product`` block from a product page's HTML."""
    for block in JSONLD_RE.findall(html):
        try:
            data = json.loads(block)
        except json.JSONDecodeError:
            continue
        if not isinstance(data, dict):
            continue
        if data.get("@type") == "Product" or "Product" in (data.get("@type") or []):
            return data
    return None


def _extract_model(name: str, brand: Optional[str], mpn: Optional[str]) -> Optional[str]:
    """Derive a searchable model from the retail product name / mpn."""
    designation = _extract_product_designation(name) if name else None
    if designation:
        return designation
    # Fallback: strip the brand prefix and take the leading descriptor token(s),
    # e.g. "Stiebel Eltron WPL 18 A Wärmepumpe" -> "WPL 18 A".
    if name:
        rest = name.strip()
        if brand:
            if brand.lower() in rest.lower():
                rest = re.sub(re.escape(brand), "", rest, flags=re.I).strip()
        # Prefer an explicit model code (letters+digits with / - . e.g. "GB172i-24",
        # or space-separated uppercase marker + number e.g. "WPL 18").
        code = re.search(
            r"\b([A-Z]{1,8}[\s/\.\-]*\d[\w/\.\-]{0,14}|[A-Za-z]{1,10}[\d/\.\-][A-Za-z0-9/\.\-]{0,14})\b",
            rest,
        )
        if code:
            return code.group(1).strip()
        m = re.match(r"([A-Za-z0-9][A-Za-z0-9/\-\. ]*?)", rest)
        tok = m.group(1).strip() if m else ""
        cut = re.split(r"\s+(?:Brennwert|Kompakt|Wart|Wärmepumpe|Warmwasser|Gas|Öl|Heiz|Solar|Luft|Wasser|Speicher|Regel|Set|System|Kombi|Gerät)\b", tok, maxsplit=1)[0]
        if len(cut) >= 2:
            return cut.strip()
    return mpn or None


def extract_retail_product(html: str, url: str) -> Optional[Dict]:
    """Turn a product page (HTML) + URL into a retail product record dict."""
    data = parse_product_jsonld(html)
    if not data:
        return None

    brand_raw = ""
    brand_obj = data.get("brand")
    if isinstance(brand_obj, dict):
        brand_raw = str(brand_obj.get("name") or "")
    elif isinstance(brand_obj, str):
        brand_raw = brand_obj

    brand = normalize_brand(brand_raw) or (brand_raw.strip() or None)
    name = (data.get("name") or "").strip() or None
    mpn = (data.get("mpn") or "").strip() or None
    sku = (data.get("sku") or "").strip() or None
    model = _extract_model(name, brand, mpn)

    price = None
    currency = None
    offers = data.get("offers")
    if isinstance(offers, dict):
        price = offers.get("price")
        currency = offers.get("priceCurrency")
    elif isinstance(offers, list) and offers:
        price = offers[0].get("price")
        currency = offers[0].get("priceCurrency")

    if price is not None:
        try:
            price = float(price)
        except (TypeError, ValueError):
            price = None

    return {
        "source": SOURCE,
        "brand": brand,
        "model": model,
        "name": name,
        "url": url,
        "mpn": mpn,
        "sku": sku,
        "price": price,
        "currency": currency,
    }


async def _iter_product_urls(client: httpx.AsyncClient) -> AsyncIterator[str]:
    """Yield product URLs from the product sitemaps, filtered to heating categories."""
    loc_re = re.compile(r"<loc>(.*?)</loc>", re.S)
    for sm in PRODUCT_SITEMAPS:
        try:
            resp = await client.get(sm)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            logger.warning("sitemap fetch failed %s: %s", sm, exc)
            continue
        for m in loc_re.findall(resp.text):
            url = m.strip()
            if _is_heating_url(url):
                yield url


async def _upsert(session, rec: Dict) -> bool:
    """Insert or refresh a retail product keyed on URL. Returns True if new."""
    existing = await session.execute(
        RetailProduct.__table__.select().where(RetailProduct.url == rec["url"])
    )
    row = existing.scalar_one_or_none()
    if row is None:
        session.add(RetailProduct(**rec))
        return True
    for k, v in rec.items():
        if v is not None:
            setattr(row, k, v)
    return False


async def run_retail_crawler(limit: int = 0) -> Dict[str, int]:
    """Crawl heizungsdiscount24 heating products into ``retail_products``.

    ``limit`` caps the number of product pages fetched (0 = no cap), useful
    for smoke tests.
    """
    stats = {"seen": 0, "parsed": 0, "new": 0, "updated": 0, "skipped": 0}
    fetched = 0

    async with httpx.AsyncClient(headers=_HEADERS, timeout=_TIMEOUT, follow_redirects=True) as client:
        async with async_session_factory() as session:
            async for url in _iter_product_urls(client):
                stats["seen"] += 1
                if limit and fetched >= limit:
                    break
                try:
                    resp = await client.get(url)
                    resp.raise_for_status()
                    html = resp.content.decode("iso-8859-1", errors="replace")
                except httpx.HTTPError as exc:
                    logger.warning("page fetch failed %s: %s", url, exc)
                    stats["skipped"] += 1
                    continue

                fetched += 1
                record = extract_retail_product(html, url)
                if not record or not record["model"]:
                    stats["skipped"] += 1
                    continue
                stats["parsed"] += 1
                if await _upsert(session, record):
                    stats["new"] += 1
                else:
                    stats["updated"] += 1
                await session.commit()
                await asyncio.sleep(_CRAWL_DELAY)

    logger.info("retail crawl done: %s", stats)
    return stats


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(asyncio.run(run_retail_crawler(limit=20)))
