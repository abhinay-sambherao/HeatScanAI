"""OCR service: orchestrates pipeline execution and database persistence."""
from __future__ import annotations

import uuid
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ocr_result import OCRResult
from app.models.match import Match
from app.ocr.pipeline import run_pipeline
from app.services.matching_service import find_matches
from app.services.crawler_service import search_and_add_product
from app.services.manufacturer_scraper import search_and_add_from_manufacturer


def _merge_pipeline_results(results: List[dict]) -> dict:
    """Merge OCR results from multiple images using best-confidence strategy.

    For each extracted field, picks the value from the image with the highest
    confidence (provided the field was actually detected). Raw texts are
    concatenated. Overall confidence is the max across all images.
    """
    if not results:
        return {}
    if len(results) == 1:
        return results[0]

    best_confidence = max(r["confidence"] for r in results)
    combined_raw = "\n\n---\n\n".join(r["raw_text"].strip() for r in results if r["raw_text"].strip())
    combined_cleaned = "\n\n---\n\n".join(r["cleaned_text"].strip() for r in results if r["cleaned_text"].strip())

    merged = {
        "raw_text": combined_raw,
        "cleaned_text": combined_cleaned,
        "confidence": best_confidence,
    }

    str_fields = ["manufacturer", "model", "energy_class", "heat_output", "fuel_type"]
    for field in str_fields:
        candidates = [(r["confidence"], r[field]) for r in results if r.get(field) and r[field] != "Not detected"]
        if candidates:
            candidates.sort(key=lambda x: x[0], reverse=True)
            merged[field] = candidates[0][1]
        else:
            merged[field] = None

    merged["per_image"] = [
        {
            "filename": r["filename"],
            "confidence": r["confidence"],
            "manufacturer": r.get("manufacturer"),
            "model": r.get("model"),
            "energy_class": r.get("energy_class"),
            "fuel_type": r.get("fuel_type"),
            "heat_output": r.get("heat_output"),
            "raw_text": r.get("raw_text", ""),
        }
        for r in results
    ]

    return merged


async def process_upload(
    db: AsyncSession,
    image_data: bytes,
    filename: str,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    address: Optional[str] = None,
    postal_code: Optional[str] = None,
    city: Optional[str] = None,
    installation_year: Optional[int] = None,
) -> dict:
    """Process a single uploaded image through the full OCR + matching pipeline."""
    pipeline_result = run_pipeline(image_data)
    pipeline_result["filename"] = filename

    return await _persist_and_match(
        db=db,
        merged=pipeline_result,
        latitude=latitude,
        longitude=longitude,
        address=address,
        postal_code=postal_code,
        city=city,
        installation_year=installation_year,
    )

async def process_multiple_uploads(
    db: AsyncSession,
    images: List[Tuple[str, bytes]],
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    address: Optional[str] = None,
    postal_code: Optional[str] = None,
    city: Optional[str] = None,
    installation_year: Optional[int] = None,
) -> dict:
    """Process multiple images and merge results with best-confidence strategy.

    Args:
        images: List of (filename, image_data) tuples.
    """
    pipeline_results = []
    for filename, data in images:
        result = run_pipeline(data)
        result["filename"] = filename
        pipeline_results.append(result)

    merged = _merge_pipeline_results(pipeline_results)

    return await _persist_and_match(
        db=db,
        merged=merged,
        latitude=latitude,
        longitude=longitude,
        address=address,
        postal_code=postal_code,
        city=city,
        installation_year=installation_year,
    )


async def _persist_and_match(
    db: AsyncSession,
    merged: dict,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    address: Optional[str] = None,
    postal_code: Optional[str] = None,
    city: Optional[str] = None,
    installation_year: Optional[int] = None,
) -> dict:
    """Save OCR result to DB, run matching (with fallbacks), persist matches."""
    first_filename = merged.get("per_image", [{}])[0].get("filename", "unknown") if merged.get("per_image") else "unknown"

    ocr_result = OCRResult(
        id=uuid.uuid4(),
        filename=first_filename,
        raw_text=merged["raw_text"],
        cleaned_text=merged["cleaned_text"],
        confidence=merged["confidence"],
        latitude=latitude,
        longitude=longitude,
        address=address,
        postal_code=postal_code,
        city=city,
        installation_year=installation_year,
    )
    db.add(ocr_result)
    await db.flush()

    matches = await find_matches(
        db,
        manufacturer=merged.get("manufacturer"),
        model=merged.get("model"),
        energy_class=merged.get("energy_class"),
        fuel_type=merged.get("fuel_type"),
        heat_output=merged.get("heat_output"),
        raw_text=merged["raw_text"],
    )

    # Fallback 1: EPREL API on-demand
    if not matches or matches[0]["score"] < 50:
        new_products = await search_and_add_product(
            db,
            manufacturer=merged.get("manufacturer"),
            model=merged.get("model"),
            fuel_type=merged.get("fuel_type"),
            heat_output=merged.get("heat_output"),
        )
        if new_products:
            matches = await find_matches(
                db,
                manufacturer=merged.get("manufacturer"),
                model=merged.get("model"),
                energy_class=merged.get("energy_class"),
                fuel_type=merged.get("fuel_type"),
                heat_output=merged.get("heat_output"),
                raw_text=merged["raw_text"],
            )

    # Fallback 2: manufacturer website
    if not matches or matches[0]["score"] < 50:
        web_products = await search_and_add_from_manufacturer(
            db,
            manufacturer=merged.get("manufacturer"),
            model=merged.get("model"),
        )
        if web_products:
            matches = await find_matches(
                db,
                manufacturer=merged.get("manufacturer"),
                model=merged.get("model"),
                energy_class=merged.get("energy_class"),
                fuel_type=merged.get("fuel_type"),
                heat_output=merged.get("heat_output"),
                raw_text=merged["raw_text"],
            )

    for match_data in matches:
        match_obj = Match(
            id=uuid.uuid4(),
            ocr_result_id=ocr_result.id,
            product_id=match_data["product_id"],
            score=match_data["score"],
            matched_attributes=match_data["matched_attributes"],
            reason=match_data["reason"],
        )
        db.add(match_obj)

    await db.flush()

    return {
        "ocr_result_id": ocr_result.id,
        "manufacturer": merged.get("manufacturer"),
        "model": merged.get("model"),
        "energy_class": merged.get("energy_class"),
        "fuel_type": merged.get("fuel_type"),
        "heat_output": merged.get("heat_output"),
        "confidence": merged["confidence"],
        "raw_text": merged["raw_text"],
        "cleaned_text": merged["cleaned_text"],
        "matches": matches,
        "per_image": merged.get("per_image", []),
        "latitude": ocr_result.latitude,
        "longitude": ocr_result.longitude,
        "address": ocr_result.address,
        "postal_code": ocr_result.postal_code,
        "city": ocr_result.city,
        "installation_year": ocr_result.installation_year,
        "created_at": ocr_result.created_at,
    }
