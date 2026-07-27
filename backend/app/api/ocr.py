"""OCR endpoint: upload an image, run OCR pipeline, return matches."""
from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.config import settings
from app.schemas.ocr import OCRResponse, OCRMatchResult
from app.services.ocr_service import process_upload
from app.core.exceptions import InvalidFileError

router = APIRouter(prefix="/ocr", tags=["OCR"])

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".pdf"}


def _validate_file(file: UploadFile) -> None:
    """Validate uploaded file type and size."""
    if not file.filename:
        raise InvalidFileError("No filename provided")

    ext = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise InvalidFileError(
            f"Invalid file type '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )


@router.post("", response_model=OCRResponse)
async def upload_and_analyze(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> OCRResponse:
    """Upload a heating system nameplate image for OCR analysis.

    Accepts JPEG, PNG, WebP, or PDF files up to 20MB.
    Returns detected manufacturer, model, confidence score, and top product matches.
    """
    _validate_file(file)

    contents = await file.read()
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(contents) > max_bytes:
        raise InvalidFileError(f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE_MB}MB")

    try:
        result = await process_upload(
            db=db,
            image_data=contents,
            filename=file.filename or "unknown",
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {exc}") from exc

    match_results = [
        OCRMatchResult(
            product_id=m["product_id"],
            manufacturer=m["manufacturer"],
            model=m["model"],
            energy_class=m.get("energy_class"),
            fuel_type=m.get("fuel_type"),
            heat_output=m.get("heat_output"),
            score=m["score"],
            matched_attributes=m.get("matched_attributes"),
            reason=m.get("reason"),
        )
        for m in result["matches"]
    ]

    return OCRResponse(
        ocr_result_id=result["ocr_result_id"],
        manufacturer=result["manufacturer"],
        model=result["model"],
        confidence=result["confidence"],
        raw_text=result["raw_text"],
        cleaned_text=result["cleaned_text"],
        matches=match_results,
        created_at=result["created_at"],
    )
