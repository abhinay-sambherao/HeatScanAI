"""OCR service: orchestrates pipeline execution and database persistence."""
from __future__ import annotations

import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ocr_result import OCRResult
from app.models.match import Match
from app.ocr.pipeline import run_pipeline
from app.services.matching_service import find_matches
from app.services.crawler_service import search_and_add_product
from app.services.manufacturer_scraper import search_and_add_from_manufacturer


async def process_upload(
    db: AsyncSession,
    image_data: bytes,
    filename: str,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    address: Optional[str] = None,
    city: Optional[str] = None,
    installation_year: Optional[int] = None,
) -> dict:
    """Process an uploaded image through the full OCR + matching pipeline.

    Steps:
        1. Run OCR pipeline on image bytes
        2. Save OCRResult (with location metadata) to database
        3. Find top matches against product database
        4. If no good match, search EPREL API on-demand and re-match
        5. Save matches to database
        6. Return structured response with location

    Returns:
        Dictionary with ocr_result_id, manufacturer, model, confidence, matches, etc.
    """
    pipeline_result = run_pipeline(image_data)

    ocr_result = OCRResult(
        id=uuid.uuid4(),
        filename=filename,
        raw_text=pipeline_result["raw_text"],
        cleaned_text=pipeline_result["cleaned_text"],
        confidence=pipeline_result["confidence"],
        latitude=latitude,
        longitude=longitude,
        address=address,
        city=city,
        installation_year=installation_year,
    )
    db.add(ocr_result)
    await db.flush()

    matches = await find_matches(
        db,
        manufacturer=pipeline_result["manufacturer"],
        model=pipeline_result["model"],
        energy_class=pipeline_result["energy_class"],
        fuel_type=pipeline_result["fuel_type"],
        heat_output=pipeline_result["heat_output"],
        raw_text=pipeline_result["raw_text"],
    )

    # Fallback: no good match → search EPREL API live
    if not matches or matches[0]["score"] < 50:
        new_products = await search_and_add_product(
            db,
            manufacturer=pipeline_result["manufacturer"],
            model=pipeline_result["model"],
        )
        if new_products:
            matches = await find_matches(
                db,
                manufacturer=pipeline_result["manufacturer"],
                model=pipeline_result["model"],
                energy_class=pipeline_result["energy_class"],
                fuel_type=pipeline_result["fuel_type"],
                heat_output=pipeline_result["heat_output"],
                raw_text=pipeline_result["raw_text"],
            )

    # Fallback 2: still no good match → search manufacturer website
    if not matches or matches[0]["score"] < 50:
        web_products = await search_and_add_from_manufacturer(
            db,
            manufacturer=pipeline_result["manufacturer"],
            model=pipeline_result["model"],
        )
        if web_products:
            matches = await find_matches(
                db,
                manufacturer=pipeline_result["manufacturer"],
                model=pipeline_result["model"],
                energy_class=pipeline_result["energy_class"],
                fuel_type=pipeline_result["fuel_type"],
                heat_output=pipeline_result["heat_output"],
                raw_text=pipeline_result["raw_text"],
            )

    match_objects = []
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
        match_objects.append(match_obj)

    await db.flush()

    return {
        "ocr_result_id": ocr_result.id,
        "manufacturer": pipeline_result["manufacturer"],
        "model": pipeline_result["model"],
        "confidence": pipeline_result["confidence"],
        "raw_text": pipeline_result["raw_text"],
        "cleaned_text": pipeline_result["cleaned_text"],
        "matches": matches,
        "latitude": ocr_result.latitude,
        "longitude": ocr_result.longitude,
        "address": ocr_result.address,
        "city": ocr_result.city,
        "installation_year": ocr_result.installation_year,
        "created_at": ocr_result.created_at,
    }
