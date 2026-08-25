from __future__ import annotations

"""Matching engine using RapidFuzz to find the best product matches
for OCR-extracted fields."""

import re

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

# P0: minimum model score when both OCR and EPREL have a model string
MIN_MODEL_SCORE = 50

# P1: heat output tolerance — same logic as crawler_service._kw_in_range
_HEAT_OUTPUT_BAND_FACTOR = 0.25
_HEAT_OUTPUT_BAND_MIN = 2.0  # kW absolute minimum band

# P2: installation year tolerance — skip EPREL products registered more
# than this many years after the nameplate year.
_INSTALL_YEAR_TOLERANCE = 2


def _fuzzy_score(query, target) -> float:
    """Compute fuzzy match ratio between two strings. Returns 0 if either is None."""
    if not query or not target:
        return 0.0
    return fuzz.token_sort_ratio(query.lower(), target.lower())


def _extract_kw(value) -> float | None:
    """Parse a heat-output value ('17.2 kW' string or number) into kW float."""
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

    Tolerance is the larger of 25% relative or 2 kW absolute.
    """
    band = max(_HEAT_OUTPUT_BAND_MIN, _HEAT_OUTPUT_BAND_FACTOR * detected_kw)
    return abs(hit_kw - detected_kw) <= band


def _brand_consistent(mfr_name, manufacturer, raw_text) -> bool:
    """Check the product's brand plausibly matches the detected manufacturer.

    Fuzzy brand comparison is unreliable for short names: 'truma' vs 'terma'
    scores 80, 'truma' vs 'trane' 60, 'truma' vs 'termia' 73 — none of which
    are actually the same brand. Use hard evidence instead:
      1. the detected manufacturer's leading word appears as a whole word in
         the product's brand ("Vaillant" in "Vaillant GmbH"),
      2. the product brand's leading word appears verbatim in the OCR text
         (the nameplate itself is ground truth).
    """
    if not mfr_name or not manufacturer:
        return False
    det_word = manufacturer.split()[0]
    try:
        if re.search(r"\b" + re.escape(det_word) + r"\b", mfr_name, re.IGNORECASE):
            return True
    except re.error:
        pass
    if raw_text:
        first = mfr_name.split()[0]
        if len(first) >= 3:
            try:
                if re.search(r"\b" + re.escape(first) + r"\b", raw_text, re.IGNORECASE):
                    return True
            except re.error:
                pass
    return False


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
    installation_year=None,
    limit: int = 5,
):
    """Find the top matching products using RapidFuzz fuzzy scoring.

    When manufacturer/model are None (OCR didn't detect them), weights are
    redistributed to the remaining fields. Also performs a raw text fallback
    search against product model names.

    When installation_year is provided, filters out EPREL products registered
    more than _INSTALL_YEAR_TOLERANCE years after the nameplate year.
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

        # Raw text fallback: search OCR text against product model. Only trust
        # it for long, distinctive model names — short fragments ("PS 300",
        # "90", "BRITA" in "Britain") appear in any long nameplate text.
        raw_score = 0.0
        if raw_text and product.model and len(product.model.strip()) >= 8:
            raw_score = fuzz.partial_ratio(
                raw_text.lower(), product.model.lower()
            )

        # Require the matched product to actually agree with the detected
        # fields. token_sort on brand names is loose ('truma' vs 'terma'
        # scores 80, 'truma' vs 'termia' 73), so a moderate manufacturer
        # score alone is not proof of a match. Confirmed brands come from
        # hard evidence (substring / presence in the OCR text) or a near-
        # identical fuzzy score. Short model names also produce false
        # positives ("PS 300" matches the "300" inside "S 3004"), so paths
        # that do not require a confirmed brand only apply to long,
        # distinctive models.
        brand_ok = _brand_consistent(mfr_name, manufacturer, raw_text)
        long_model = product.model and len(product.model.strip()) >= 8
        if manufacturer and model:
            has_primary_match = (
                brand_ok
                or mfr_score >= 90
                or (model_score >= 80 and long_model)
                or (brand_ok and model_score >= 55)
            )
        elif manufacturer:
            has_primary_match = brand_ok or mfr_score >= 90 or (mfr_score >= 70 and long_model)
        elif model:
            has_primary_match = (model_score >= 60 and long_model) or raw_score >= 90
        else:
            has_primary_match = raw_score >= 90

        if not has_primary_match:
            continue

        # P0: When both OCR and EPREL have a model, require minimum overlap.
        # This prevents brand-only matches from returning wrong products
        # (e.g. Ochsner "Europa MINI EW P" → "AIR 80 C13A").
        if model and product.model and model_score < MIN_MODEL_SCORE:
            continue

        # P1: Heat output hard filter — skip products whose rated output is
        # implausible given the nameplate value. This is the most reliable
        # discriminator when model strings don't align.
        detected_kw = _extract_kw(heat_output)
        hit_kw = _extract_kw(product.heat_output)
        if detected_kw is not None and hit_kw is not None:
            if not _kw_in_range(detected_kw, hit_kw):
                continue

        # P2: Installation year filter — skip EPREL products whose release
        # date is more than _INSTALL_YEAR_TOLERANCE years after the nameplate
        # year. This prevents matching old nameplates to newer products that
        # share similar model strings.
        if installation_year and product.release_date:
            product_year = product.release_date.year
            if product_year > installation_year + _INSTALL_YEAR_TOLERANCE:
                continue

        # Blend raw text boost (only if substantial match)
        # Don't boost if manufacturer is clearly different
        if raw_score > 60 and (manufacturer is None or mfr_score > 30):
            composite = max(composite, raw_score * 0.5)
        if composite < 30.0:
            continue

        matched_attrs = {}
        reasons = []
        if mfr_score > 50:
            matched_attrs["manufacturer"] = {"score": round(mfr_score, 1), "target": mfr_name}
            reasons.append("Manufacturer match: %s (%.0f%%)" % (mfr_name, mfr_score))
        if model_score > 50:
            matched_attrs["model"] = {"score": round(model_score, 1), "target": product.model}
            reasons.append("Model match: %s (%.0f%%)" % (product.model, model_score))
        if energy_score > 50:
            matched_attrs["energy_class"] = {"score": round(energy_score, 1), "target": product.energy_class}
        if fuel_score > 50:
            matched_attrs["fuel_type"] = {"score": round(fuel_score, 1), "target": product.fuel_type}
        if output_score > 50:
            matched_attrs["heat_output"] = {"score": round(output_score, 1), "target": product.heat_output}
        if raw_score > 70:
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
