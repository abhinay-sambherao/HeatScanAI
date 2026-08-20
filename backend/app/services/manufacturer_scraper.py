"""Manufacturer website scraper: searches known brand sites for product specs.

When a product isn't found in the local DB or EPREL API, this module
tries to find it on the manufacturer's own website using brand-specific
search URL patterns, then extracts specifications from the product page.
"""

from __future__ import annotations

import re
import uuid
from typing import Any

import httpx
from bs4 import BeautifulSoup
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.models.manufacturer import Manufacturer
from app.models.category import Category
from app.ocr.parser import extract_fields
from app.config import settings
from app.core.logging import get_logger

logger = get_logger("scraper")

# Brand-specific search URL patterns
# Key is the canonical manufacturer name (lowercase), value is a dict with:
#   - search_url: URL template for search (use {model} placeholder)
#   - base_url: the base domain for resolving relative links
#   - selectors: CSS selectors for finding product links on search results
MANUFACTURER_SITES: dict[str, dict[str, Any]] = {
    "viessmann": {
        "search_url": "https://www.viessmann.de/de/suche.html?q={model}",
        "base_url": "https://www.viessmann.de",
        "product_link_selector": "a[href*='/produkte/'], a[href*='/product/']",
        "name_selector": "h1, .product-title, .product-name",
    },
    "vaillant": {
        "search_url": "https://www.vaillant.de/produkte/?q={model}",
        "base_url": "https://www.vaillant.de",
        "product_link_selector": "a[href*='/produkte/'], a[href*='/product/']",
        "name_selector": "h1, .product-title",
    },
    "bosch": {
        "search_url": "https://www.bosch-thermotechnology.com/de/search/?q={model}",
        "base_url": "https://www.bosch-thermotechnology.com",
        "product_link_selector": "a[href*='/product/'], a[href*='/produkt/']",
        "name_selector": "h1, .product-headline",
    },
    "wolf": {
        "search_url": "https://www.wolf.eu/de-de/suche?q={model}",
        "base_url": "https://www.wolf.eu",
        "product_link_selector": "a[href*='/produkte/']",
        "name_selector": "h1, .product-title",
    },
    "daikin": {
        "search_url": "https://www.daikin.de/de_de/produkte.html?q={model}",
        "base_url": "https://www.daikin.de",
        "product_link_selector": "a[href*='/produkte/'], a[href*='/product/']",
        "name_selector": "h1, .product-title",
    },
    "mitsubishi": {
        "search_url": "https://www.mitsubishi-les.com/de/produkte/?q={model}",
        "base_url": "https://www.mitsubishi-les.com",
        "product_link_selector": "a[href*='/produkte/']",
        "name_selector": "h1, .product-title, .product-name",
    },
    "worcester": {
        "search_url": "https://www.worcester-bosch.co.uk/search?q={model}",
        "base_url": "https://www.worcester-bosch.co.uk",
        "product_link_selector": "a[href*='/products/'], a[href*='/product/']",
        "name_selector": "h1, .product-title",
    },
    "stiebel eltron": {
        "search_url": "https://www.stiebel-eltron.de/de/produkte/?q={model}",
        "base_url": "https://www.stiebel-eltron.de",
        "product_link_selector": "a[href*='/produkte/']",
        "name_selector": "h1, .product-title",
    },
    "panasonic": {
        "search_url": "https://www.panasonic.com/de/consumer/haushalt-heizung/suche.html?q={model}",
        "base_url": "https://www.panasonic.com",
        "product_link_selector": "a[href*='/heizung/']",
        "name_selector": "h1, .product-title, .pane-title",
    },
    "weishaupt": {
        "search_url": "https://www.weishaupt.de/produkte?q={model}",
        "base_url": "https://www.weishaupt.de",
        "product_link_selector": "a[href*='/produkte/'], a[href*='/product/']",
        "name_selector": "h1, .product-title",
    },
    "ferroli": {
        "search_url": "https://www.ferroli.com/en/produkte?q={model}",
        "base_url": "https://www.ferroli.com",
        "product_link_selector": "a[href*='/produkte/'], a[href*='/product/']",
        "name_selector": "h1, .product-title",
    },
    "ariston": {
        "search_url": "https://www.ariston.com/de/produkte/?q={model}",
        "base_url": "https://www.ariston.com",
        "product_link_selector": "a[href*='/produkte/']",
        "name_selector": "h1, .product-title",
    },
    "baxi": {
        "search_url": "https://www.baxi.de/produkte/?q={model}",
        "base_url": "https://www.baxi.de",
        "product_link_selector": "a[href*='/produkte/']",
        "name_selector": "h1, .product-title",
    },
    "glow-worm": {
        "search_url": "https://www.glow-worm.co.uk/products?q={model}",
        "base_url": "https://www.glow-worm.co.uk",
        "product_link_selector": "a[href*='/products/']",
        "name_selector": "h1, .product-title",
    },
    "ideal": {
        "search_url": "https://www.idealheating.com/search?q={model}",
        "base_url": "https://www.idealheating.com",
        "product_link_selector": "a[href*='/products/']",
        "name_selector": "h1, .product-title",
    },
    "remeha": {
        "search_url": "https://www.remeha.de/produkte/?q={model}",
        "base_url": "https://www.remeha.de",
        "product_link_selector": "a[href*='/produkte/']",
        "name_selector": "h1, .product-title",
    },
    "intergas": {
        "search_url": "https://www.intergasheating.co.uk/search?q={model}",
        "base_url": "https://www.intergasheating.co.uk",
        "product_link_selector": "a[href*='/products/'], a[href*='/producten/']",
        "name_selector": "h1, .product-title",
    },
    "atag": {
        "search_url": "https://www.atagverwarming.nl/producten/?q={model}",
        "base_url": "https://www.atagverwarming.nl",
        "product_link_selector": "a[href*='/producten/']",
        "name_selector": "h1, .product-title",
    },
    "junkers": {
        "search_url": "https://www.junkers.de/search?q={model}",
        "base_url": "https://www.junkers.de",
        "product_link_selector": "a[href*='/produkte/'], a[href*='/product/']",
        "name_selector": "h1, .product-title",
    },
    "samsung": {
        "search_url": "https://www.samsung.com/de/search/?q={model}",
        "base_url": "https://www.samsung.com",
        "product_link_selector": "a[href*='/heating/'], a[href*='/klima/']",
        "name_selector": "h1, .product-title",
    },
    "lg": {
        "search_url": "https://www.lg.com/de/search?q={model}",
        "base_url": "https://www.lg.com",
        "product_link_selector": "a[href*='/heizung/'], a[href*='/product/']",
        "name_selector": "h1, .product-title",
    },
    "beretta": {
        "search_url": "https://www.beretta.com/de-de/produkte/?q={model}",
        "base_url": "https://www.beretta.com",
        "product_link_selector": "a[href*='/produkte/'], a[href*='/product/']",
        "name_selector": "h1, .product-title",
    },
    "biasi": {
        "search_url": "https://www.biasi.com/de/produkte/?q={model}",
        "base_url": "https://www.biasi.com",
        "product_link_selector": "a[href*='/produkte/'], a[href*='/product/']",
        "name_selector": "h1, .product-title",
    },
    "nefit": {
        "search_url": "https://www.nefit.nl/zoeken/?q={model}",
        "base_url": "https://www.nefit.nl",
        "product_link_selector": "a[href*='/producten/'], a[href*='/product/']",
        "name_selector": "h1, .product-title",
    },
    "awb": {
        "search_url": "https://www.awb.nl/producten?q={model}",
        "base_url": "https://www.awb.nl",
        "product_link_selector": "a[href*='/producten/'], a[href*='/product/']",
        "name_selector": "h1, .product-title",
    },
    "brotje": {
        "search_url": "https://www.brotje.de/produkte/?q={model}",
        "base_url": "https://www.brotje.de",
        "product_link_selector": "a[href*='/produkte/'], a[href*='/product/']",
        "name_selector": "h1, .product-title",
    },
    "brötje": {
        "search_url": "https://www.brotje.de/produkte/?q={model}",
        "base_url": "https://www.brotje.de",
        "product_link_selector": "a[href*='/produkte/'], a[href*='/product/']",
        "name_selector": "h1, .product-title",
    },
    "viadrus": {
        "search_url": "https://www.viadrus.cz/?s={model}",
        "base_url": "https://www.viadrus.cz",
        "product_link_selector": "a[href*='/vyrobky/'], a[href*='/product/']",
        "name_selector": "h1, .product-title",
    },
    "de dietrich": {
        "search_url": "https://www.dedietrich-thermique.com/de/search?q={model}",
        "base_url": "https://www.dedietrich-thermique.com",
        "product_link_selector": "a[href*='/produkte/'], a[href*='/product/']",
        "name_selector": "h1, .product-title",
    },
    "saunier duval": {
        "search_url": "https://www.saunierduval.com/search/?q={model}",
        "base_url": "https://www.saunierduval.com",
        "product_link_selector": "a[href*='/produkte/'], a[href*='/product/']",
        "name_selector": "h1, .product-title",
    },
    "atmos": {
        "search_url": "https://www.atmos.eu/?s={model}",
        "base_url": "https://www.atmos.eu",
        "product_link_selector": "a[href*='/vyrobky/'], a[href*='/product/']",
        "name_selector": "h1, .product-title",
    },
    "thermia": {
        "search_url": "https://www.thermia.com/de/search?q={model}",
        "base_url": "https://www.thermia.com",
        "product_link_selector": "a[href*='/produkte/'], a[href*='/product/']",
        "name_selector": "h1, .product-title",
    },
    "clage": {
        "search_url": "https://www.clage.com/de/produkte?q={model}",
        "base_url": "https://www.clage.com",
        "product_link_selector": "a[href*='/produkte/'], a[href*='/product/']",
        "name_selector": "h1, .product-title",
    },
    "truma": {
        "search_url": "https://www.truma.com/de/produkte?q={model}",
        "base_url": "https://www.truma.com",
        "product_link_selector": "a[href*='/produkte/'], a[href*='/product/']",
        "name_selector": "h1, .product-title",
    },
    "ökofen": {
        "search_url": "https://www.oekofen.com/de-de/pelletheizung",
        "base_url": "https://www.oekofen.com",
        "product_link_selector": "a[href*='/de-de/'], a[href*='/produkte/']",
        "name_selector": "h1, .product-title",
    },
    "ochsner": {
        "search_url": "https://www.ochsner.com/de-de",
        "base_url": "https://www.ochsner.com",
        "product_link_selector": "a[href*='/de-de/'], a[href*='/produkt/']",
        "name_selector": "h1, .product-title",
    },
    "elco": {
        "search_url": "https://www.elco.net/de/produkte.html",
        "base_url": "https://www.elco.net",
        "product_link_selector": "a[href*='/produkte/'], a[href*='/product/']",
        "name_selector": "h1, .product-title",
    },
}

# Manufacturers not in the specific list — try a generic search pattern
GENERIC_SEARCH_URL = "https://www.{domain}/search?q={model}"


def _find_manufacturer_site(manufacturer_name: str) -> dict[str, Any] | None:
    """Find the manufacturer site config by name, or return a generic config."""
    name_lower = manufacturer_name.lower().strip()
    if name_lower in MANUFACTURER_SITES:
        return MANUFACTURER_SITES[name_lower]
    # Try partial match
    for key, config in MANUFACTURER_SITES.items():
        if key in name_lower or name_lower in key:
            return config
    # Try generic: construct domain from manufacturer name
    slug = name_lower.replace(" ", "").replace("-", "").replace("'", "").replace(".", "")
    return {
        "search_url": f"https://www.{slug}.com/search?q={{model}}",
        "base_url": f"https://www.{slug}.com",
        "product_link_selector": "a[href*='/product'], a[href*='/produkt']",
        "name_selector": "h1",
    }


def _extract_page_text(soup: BeautifulSoup) -> str:
    """Extract visible text from a product page."""
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()
    text = soup.get_text(separator=" ", strip=True)
    return re.sub(r"\s+", " ", text)


async def _fetch_page(client: httpx.AsyncClient, url: str) -> str | None:
    """Fetch a page with browser-like headers and retry."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
    }
    for attempt in range(2):
        try:
            resp = await client.get(url, headers=headers, timeout=15.0, follow_redirects=True)
            if resp.status_code == 200:
                return resp.text
        except Exception:
            if attempt == 0:
                continue
    return None


async def search_product_on_manufacturer_site(
    manufacturer: str,
    model: str,
) -> dict[str, Any] | None:
    """Search a manufacturer's website for a product and extract specs.

    Steps:
        1. Look up manufacturer site config
        2. Search the site for the model
        3. Follow the first product link
        4. Extract specs from the product page using the OCR parser

    Returns:
        Dict with model, manufacturer, energy_class, heat_output, fuel_type
        or None if nothing found.
    """
    site_config = _find_manufacturer_site(manufacturer)
    if not site_config:
        return None

    search_url = site_config["search_url"].format(model=model)
    base_url = site_config["base_url"]

    async with httpx.AsyncClient() as client:
        html = await _fetch_page(client, search_url)
        if not html:
            return None

        soup = BeautifulSoup(html, "html.parser")
        selector = site_config.get("product_link_selector", "a[href]")
        links = soup.select(selector)

        if not links:
            return None

        # Find the link whose text most closely matches the model
        best_link = None
        best_score = 0
        from rapidfuzz import fuzz

        for link in links[:20]:
            href = link.get("href", "")
            text = link.get_text(strip=True)
            if not href or not text:
                continue
            score = fuzz.partial_ratio(model.lower(), text.lower())
            if score > best_score:
                best_score = score
                best_link = href

        # Fallback: if no good link found via selector, try ALL page links
        if best_score < 50:
            all_links = soup.find_all("a", href=True)
            for link in all_links[:50]:
                href = link["href"]
                text = link.get_text(strip=True)
                score = fuzz.partial_ratio(model.lower(), text.lower())
                if score > best_score:
                    best_score = score
                    best_link = href

        if not best_link or best_score < 40:
            return None

        # Resolve relative URL
        if best_link.startswith("/"):
            product_url = base_url + best_link
        elif best_link.startswith("http"):
            product_url = best_link
        else:
            product_url = base_url + "/" + best_link

        # Fetch product page
        product_html = await _fetch_page(client, product_url)
        if not product_html:
            return None

        product_soup = BeautifulSoup(product_html, "html.parser")
        page_text = _extract_page_text(product_soup)

        # Use the OCR parser to extract specs from the page text
        fields = extract_fields(page_text)

        # Get product name from heading
        name_selector = site_config.get("name_selector", "h1")
        name_tag = product_soup.select_one(name_selector)
        product_name = name_tag.get_text(strip=True) if name_tag else model

        result = {
            "model": model,
            "product_name": product_name,
            "manufacturer": manufacturer,
            "energy_class": fields.get("energy_class"),
            "heat_output": fields.get("heat_output"),
            "fuel_type": fields.get("fuel_type"),
            "source_url": product_url,
        }
        logger.info("scraped_from_manufacturer", manufacturer=manufacturer, model=model, url=product_url)
        return result


async def search_and_add_from_manufacturer(
    db: AsyncSession,
    manufacturer: str | None,
    model: str | None,
) -> list[dict]:
    """Search manufacturer website for a product, add to DB if found.

    Called after EPREL API fallback fails. Returns match data in the same
    format as find_matches() and search_and_add_product().

    Args:
        db: Database session.
        manufacturer: OCR-detected manufacturer name.
        model: OCR-detected model number.

    Returns:
        List of match dicts (empty if nothing found/added).
    """
    if not manufacturer or not model:
        return []

    result = await search_product_on_manufacturer_site(manufacturer, model)
    if not result:
        return []

    # Check if we already have this in DB (by model + manufacturer)
    existing_stmt = select(Product).join(
        Manufacturer, Product.manufacturer_id == Manufacturer.id
    ).where(
        Manufacturer.name.ilike(f"%{manufacturer}%"),
        Product.model.ilike(f"%{model}%"),
    )
    existing = (await db.execute(existing_stmt)).scalar_one_or_none()
    if existing:
        return []

    # Resolve manufacturer
    mfr_stmt = select(Manufacturer).where(Manufacturer.name.ilike(f"%{manufacturer}%"))
    mfr = (await db.execute(mfr_stmt)).scalar_one_or_none()
    if not mfr:
        mfr = Manufacturer(id=uuid.uuid4(), name=manufacturer)
        db.add(mfr)
        await db.flush()

    # Resolve category from OCR parser
    cat = None
    category_name = result.get("fuel_type")
    if category_name:
        fuel_to_cat = {
            "gas": "Gas boilers",
            "oil": "Oil boilers",
            "electricity": "Heat pumps",
            "biomass": "Biomass boilers",
            "solar": "Solar thermal collectors",
        }
        cat_name = fuel_to_cat.get(category_name)
        if cat_name:
            cat_stmt = select(Category).where(Category.name == cat_name)
            cat = (await db.execute(cat_stmt)).scalar_one_or_none()
            if not cat:
                cat = Category(id=uuid.uuid4(), name=cat_name, eprel_category_id="web_scrape")
                db.add(cat)
                await db.flush()

    # Create product
    eprel_id = f"WEB-{manufacturer.upper()[:4]}-{model[:20]}"
    product = Product(
        id=uuid.uuid4(),
        eprel_id=eprel_id,
        manufacturer_id=mfr.id,
        category_id=cat.id if cat else None,
        model=model,
        supplier=manufacturer,
        energy_class=result.get("energy_class"),
        heat_output=result.get("heat_output"),
        fuel_type=result.get("fuel_type"),
        raw_json={"source": "manufacturer_website", "url": result.get("source_url")},
    )
    db.add(product)
    await db.flush()
    await db.commit()

    logger.info("added_from_manufacturer_site", manufacturer=manufacturer, model=model)

    return [{
        "product_id": product.id,
        "manufacturer": manufacturer,
        "model": model,
        "energy_class": result.get("energy_class"),
        "fuel_type": result.get("fuel_type"),
        "heat_output": result.get("heat_output"),
        "score": 100.0,
        "matched_attributes": {"manufacturer_site": {"score": 100.0, "target": model}},
        "reason": f"Found on {manufacturer} website: {result.get('source_url', '')}",
    }]
