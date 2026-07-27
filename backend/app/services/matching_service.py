from __future__ import annotations

"""Matching engine using RapidFuzz to find the best product matches
for OCR-extracted fields."""

from rapidfuzz import fuzz

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.product import Product

# Base weights for composite scoring
WEIGHT_MANUFACTURER = 0.35
WEIGHT_MODEL = 0.35
WEIGHT_ENERGY_CLASS = 0.10
WEIGHT_FUEL_TYPE = 0.10
WEIGHT_HEAT_OUTPUT = 0.10


def _fuzzy_score(query, target) -> float:
    """Compute fuzzy match ratio between two strings. Returns 0 if either is None."""
    if not query or not target:
        return 0.0
    return fuzz.token_sort_ratio(query.lower(), target.lower())


def _compute_composite(mfr_score, model_score, energy_score, fuel_score, output_score, mfr_val, model_val):
    """Compute weighted composite score, redistributing weight from missing fields."""
    available = {}
    if mfr_val is not None:
        available["mfr"] = (mfr_score, WEIGHT_MANUFACTURER)
    if model_val is not None:
        available["model"] = (model_score, WEIGHT_MODEL)
    available["energy"] = (energy_score, WEIGHT_ENERGY_CLASS)
    available["fuel"] = (fuel_score, WEIGHT_FUEL_TYPE)
    available["output"] = (output_score, WEIGHT_HEAT_OUTPUT)

    total_weight = sum(w for _, w in available.values())
    if total_weight == 0:
        return 0.0

    return sum(s * (w / total_weight) for s, w in available.values())


async def find_matches(
    db: AsyncSession,
    manufacturer,
    model,
    energy_class=None,
    fuel_type=None,
    heat_output=None,
    raw_text=None,
    limit: int = 5,
):
    """Find the top matching products using RapidFuzz fuzzy scoring.

    When manufacturer/model are None (OCR didn't detect them), weights are
    redistributed to the remaining fields. Also performs a raw text fallback
    search against product model names.
    """
    stmt = select(Product).options(
        selectinload(Product.manufacturer),
        selectinload(Product.category),
    )
    result = await db.execute(stmt)
    products = result.scalars().all()

    scored = []
    for product in products:
        mfr_name = product.manufacturer.name if product.manufacturer else None

        mfr_score = _fuzzy_score(manufacturer, mfr_name)
        model_score = _fuzzy_score(model, product.model)
        energy_score = _fuzzy_score(energy_class, product.energy_class)
        fuel_score = _fuzzy_score(fuel_type, product.fuel_type)
        output_score = _fuzzy_score(heat_output, product.heat_output)

        composite = _compute_composite(
            mfr_score, model_score, energy_score, fuel_score, output_score,
            manufacturer, model,
        )

        # Raw text fallback: search OCR text against product model
        raw_score = 0.0
        if raw_text and product.model:
            raw_score = fuzz.partial_ratio(
                raw_text.lower(), product.model.lower()
            )
            # Blend raw score into composite (up to 50% boost)
            composite = max(composite, raw_score * 0.5)

        if composite < 5.0:
            continue

        matched_attrs = {}
        reasons = []
        if mfr_score > 40:
            matched_attrs["manufacturer"] = {"score": round(mfr_score, 1), "target": mfr_name}
            reasons.append("Manufacturer match: %s (%.0f%%)" % (mfr_name, mfr_score))
        if model_score > 40:
            matched_attrs["model"] = {"score": round(model_score, 1), "target": product.model}
            reasons.append("Model match: %s (%.0f%%)" % (product.model, model_score))
        if energy_score > 40:
            matched_attrs["energy_class"] = {"score": round(energy_score, 1), "target": product.energy_class}
        if fuel_score > 40:
            matched_attrs["fuel_type"] = {"score": round(fuel_score, 1), "target": product.fuel_type}
        if output_score > 40:
            matched_attrs["heat_output"] = {"score": round(output_score, 1), "target": product.heat_output}
        if raw_score > 60:
            matched_attrs["raw_text_match"] = {"score": round(raw_score, 1), "target": product.model}
            reasons.append("Raw text match: %s (%.0f%%)" % (product.model, raw_score))

        scored.append({
            "product_id": product.id,
            "manufacturer": mfr_name or "Unknown",
            "model": product.model,
            "energy_class": product.energy_class,
            "fuel_type": product.fuel_type,
            "heat_output": product.heat_output,
            "score": round(composite, 2),
            "matched_attributes": matched_attrs,
            "reason": "; ".join(reasons) if reasons else "Partial match",
        })

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:limit]
