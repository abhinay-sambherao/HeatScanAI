"""Normalize manufacturer attribution using the brand normalizer.

Consolidates EPREL's inconsistent manufacturer names (legal entities,
registrants, case variants) into canonical brand names for all existing
products. This is the DB migration counterpart to the crawl-time
normalization in `app/services/parser.py` via brand_normalizer.

Example normalization:
    "Viessmann Climate Solutions SE"  -> "Viessmann"  (2111 products)
    "Viessmann Werke GmbH & Co. KG"   -> "Viessmann"  (1165 products)
    "Viessmann"                        -> "Viessmann"  (15 products)
    "KWB - Kraft und Wärme aus Biomasse GmbH" -> "KWB" (104 products)
    "MIDEA"                            -> "Midea" (506 products)

It also:
  - Removes the "Web-" scraper products that create false matches
  - Removes products with garbled / trivial model strings
  - Deletes orphaned manufacturer rows

Usage (run from backend/):
    python -m scripts.normalize_brands             # dry run (report only)
    python -m scripts.normalize_brands --apply     # apply changes
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import uuid

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import async_session_factory
from app.models.manufacturer import Manufacturer
from app.models.product import Product
from app.models.match import Match
from app.services.brand_normalizer import (
    normalize_brand,
    is_valid_brand,
    extract_brand_from_raw,
)
from app.services.crawler_service import _is_plausible_model


async def _delete_product(db, product: Product) -> None:
    """Delete a product and its associated match rows.

    `matches.product_id` has a NOT NULL constraint, so SQLAlchemy cannot
    silently null out the FK when a matched product is deleted. Delete the
    match rows first.
    """
    for m in list(product.matches):
        await db.delete(m)
    await db.delete(product)


async def normalize(apply: bool = False) -> None:
    async with async_session_factory() as db:
        products = (await db.execute(
            select(Product).options(
                selectinload(Product.manufacturer),
                selectinload(Product.matches),
            )
        )).scalars().all()

        manufacturers = (await db.execute(select(Manufacturer))).scalars().all()
        mfr_by_name: dict[str, Manufacturer] = {m.name.lower(): m for m in manufacturers}

        # Track obsolete manufacturer rows to delete at the end
        obsolete: dict[int, Manufacturer] = {}

        fixes = 0
        no_raw = 0
        skipped_brand = 0
        skipped_model = 0
        web_removed = 0
        junk_removed = 0
        newly_created: set[str] = set()

        for product in products:
            # Remove WEB- scraped pseudo-products (synthetic, non-EPREL)
            if product.eprel_id.startswith("WEB-"):
                if apply:
                    await _delete_product(db, product)
                web_removed += 1
                continue

            # Remove garbled / trivial model strings
            if not _is_plausible_model(product.model or ""):
                if apply:
                    await _delete_product(db, product)
                junk_removed += 1
                continue

            # Normalize the brand from raw_json
            raw = product.raw_json
            brand = None
            if isinstance(raw, dict):
                brand = extract_brand_from_raw(raw)
            if not brand:
                # Fall back to normalizing the current stored manufacturer name
                current = product.manufacturer.name if product.manufacturer else None
                if current:
                    brand = normalize_brand(current)
            if not brand:
                no_raw += 1
                continue

            if not is_valid_brand(brand):
                skipped_brand += 1
                continue

            current_name = product.manufacturer.name if product.manufacturer else "Unknown"
            if current_name.lower() == brand.lower():
                continue

            # Find or create the target manufacturer
            target = mfr_by_name.get(brand.lower())
            if target is None:
                if not apply and brand.lower() not in newly_created:
                    newly_created.add(brand.lower())
                    print(f"NEW manufacturer '{brand}'")
                if apply:
                    target = Manufacturer(id=uuid.uuid4(), name=brand)
                    db.add(target)
                    await db.flush()
                    mfr_by_name[brand.lower()] = target

            if not apply:
                print(f"  {current_name:<60} -> {brand:<40} "
                      f"(product {product.eprel_id} '{product.model}')")
                fixes += 1
            else:
                if target is not None:
                    product.manufacturer_id = target.id
                    # Keep registrant as supplier if available
                    if isinstance(raw, dict):
                        org = raw.get("organisation") or {}
                        registrant = org.get("organisationTitle") if isinstance(org, dict) else None
                        if registrant and str(registrant).strip() != product.supplier:
                            product.supplier = str(registrant).strip()
                fixes += 1

        # Reassign products that now point to a brand that is a parent of another
        # (after normalization, some manufacturer rows may become duplicates).
        if apply:
            # Refresh the map to reflect renames
            mfr_by_name = {m.name.lower(): m for m in
                           (await db.execute(select(Manufacturer))).scalars().all()}

        # Delete now-empty / obsolete manufacturer rows (those with 0 products)
        if apply:
            for mfr in (await db.execute(select(Manufacturer))).scalars().all():
                count = (await db.execute(
                    select(Product.id).where(Product.manufacturer_id == mfr.id)
                )).scalars().first()
                if count is None and mfr.name not in {"Unknown"}:
                    await db.delete(mfr)

            await db.commit()
            print(f"\nApplied: {fixes} reassignments, {web_removed} WEB- products "
                  f"removed, {junk_removed} garbled-model products removed, "
                  f"{no_raw} without brand skipped, {skipped_brand} invalid-skip.")
        else:
            print(f"\nWould change: {fixes} reassignments, {web_removed} WEB- "
                  f"products removed, {junk_removed} garbled-model products removed, "
                  f"{no_raw} without brand skipped, {skipped_brand} invalid-skip.")
            print("Re-run with --apply to write changes.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Normalize manufacturer attribution")
    parser.add_argument("--apply", action="store_true",
                        help="Write changes to the database (default: dry run)")
    args = parser.parse_args()
    sys.exit(asyncio.run(normalize(apply=args.apply)))
