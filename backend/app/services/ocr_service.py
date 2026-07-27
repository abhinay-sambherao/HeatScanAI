"""OCR service: orchestrates pipeline execution and database persistence."""
from __future__ import annotations

import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ocr_result import OCRResult
from app.models.match import Match
from app.ocr.pipeline import run_pipeline
from app.services.matching_service import find_matches


async def process_upload(
    db: AsyncSession,
    image_data: bytes,
    filename: str,
) -> dict:
    """Process an uploaded image through the full OCR + matching pipeline.

    Steps:
        1. Run OCR pipeline on image bytes
        2. Save OCRResult to database
        3. Find top matches against product database
        4. Save matches to database
        5. Return structured response

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
        "created_at": ocr_result.created_at,
    }
