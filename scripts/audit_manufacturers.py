"""Audit and fix manufacturer attribution for existing EPREL products.

EPREL products carry two entity names:
  - supplierOrTrademark  -> the brand on the nameplate (e.g. "Wertec")
  - organisation         -> the registrant, often an importer/distributor
                            (e.g. "TECNILIMA - EQUIPAMENTOS E SERVICOS LDA")

The crawler used to store the registrant as the manufacturer. This script
re-points products to their brand and stores the registrant in `supplier`.

Usage (run from backend/):
    python -m scripts.audit_manufacturers            # dry run (report only)
    python -m scripts.audit_manufacturers --apply    # apply fixes
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import uuid

from rapidfuzz import fuzz

from app.database import async_session_factory
from app.models.manufacturer import Manufacturer
from app.models.product import Product
from sqlalchemy import select
from sqlalchemy.orm import selectinload


def _brand_of(product: Product) -> str | None:
    """Extract the nameplate brand from the stored EPREL raw_json."""
    raw = product.raw_json
    if not isinstance(raw, dict):
        return None
    brand = raw.get("supplierOrTrademark")
    if brand and str(brand).strip():
        return str(brand).strip()
    owner = raw.get("trademarkOwner")
    if owner and str(owner).strip():
        return str(owner).strip()
    org = raw.get("organisation") or {}
    title = org.get("organisationTitle")
    if title and str(title).strip():
        return str(title).strip()
    return None


def _registrant_of(product: Product) -> str | None:
    """Extract the registrant (organisation) from the stored EPREL raw_json."""
    raw = product.raw_json
    if not isinstance(raw, dict):
        return None
    org = raw.get("organisation") or {}
    title = org.get("organisationTitle")
    if title and str(title).strip():
        return str(title).strip()
    return None


def _is_valid_brand(brand: str) -> bool:
    """Reject package-description strings that EPREL stores as brand.

    Space-heater *package* registrations put the full composition in
    supplierOrTrademark (e.g. "Wolf Sonnenpaket Ölbrennwert COB-15 ; 3x
    Kollektor F3-1, 1 MK, SEM-2-400"). Those are not usable brand names.
    """
    if len(brand) > 60:
        return False
    lowered = brand.lower()
    if ";" in brand:
        return False
    if "paket" in lowered or "sonnenpaket" in lowered:
        return False
    return True


async def audit(apply: bool = False) -> None:
    async with async_session_factory() as db:
        products = (await db.execute(
            select(Product).options(selectinload(Product.manufacturer))
        )).scalars().all()

        manufacturers = (await db.execute(select(Manufacturer))).scalars().all()
        mfr_by_name = {m.name.lower(): m for m in manufacturers}

        fixes = 0
        no_raw = 0
        skipped_brand = 0
        created_displayed: set[str] = set()
        for product in products:
            brand = _brand_of(product)
            if brand is None:
                no_raw += 1
                continue

            current = product.manufacturer.name if product.manufacturer else None
            if current and current.lower() == brand.lower():
                continue

            if not _is_valid_brand(brand):
                skipped_brand += 1
                if not apply:
                    print(
                        f"SKIP  {current or 'Unknown':<60} -> {brand[:40]:<40} "
                        f"(product {product.eprel_id} '{product.model}')"
                    )
                continue

            registrant = _registrant_of(product)
            similarity = fuzz.token_sort_ratio(
                (current or "").lower(), brand.lower()
            ) if current else 0

            # Pick the manufacturer row to point the product at.
            target = mfr_by_name.get(brand.lower())
            if target is None and similarity > 85 and current:
                # Same entity, different spelling (e.g. "Waterkotte GmbH" vs
                # "WATERKOTTE") -> rename the existing row instead of
                # creating a duplicate.
                target = mfr_by_name[current.lower()]
                if not apply:
                    print(f"RENAME manufacturer '{current}' -> '{brand}'")
                else:
                    target.name = brand
                    mfr_by_name.pop(current.lower())
                    mfr_by_name[brand.lower()] = target
            if target is None:
                if not apply and brand.lower() not in created_displayed:
                    print(f"NEW manufacturer '{brand}'")
                    created_displayed.add(brand.lower())
                if apply:
                    target = Manufacturer(id=uuid.uuid4(), name=brand)
                    db.add(target)
                    await db.flush()
                    mfr_by_name[brand.lower()] = target

            if not apply:
                print(
                    f"  {current or 'Unknown':<60} -> {brand:<40} "
                    f"(product {product.eprel_id} '{product.model}')"
                )
            else:
                product.manufacturer_id = target.id
                if registrant and registrant != product.supplier:
                    product.supplier = registrant
            fixes += 1

        if apply:
            await db.commit()
            print(f"\nApplied {fixes} fixes to {len(products)} products "
                  f"({no_raw} without raw_json skipped, "
                  f"{skipped_brand} package products skipped).")
        else:
            print(f"\n{fixes} product(s) would change across {len(products)} "
                  f"products ({no_raw} without raw_json skipped, "
                  f"{skipped_brand} package products skipped). "
                  "Re-run with --apply to write changes.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Audit manufacturer attribution")
    parser.add_argument("--apply", action="store_true",
                        help="Write changes to the database (default: dry run)")
    args = parser.parse_args()
    sys.exit(asyncio.run(audit(apply=args.apply)))
