"""Pydantic schemas for OCR endpoints."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


class OCRMatchResult(BaseModel):
    """A single product match from OCR analysis."""

    product_id: uuid.UUID
    manufacturer: str
    model: str
    energy_class: Optional[str] = None
    fuel_type: Optional[str] = None
    heat_output: Optional[str] = None
    score: float = Field(ge=0, le=100)
    matched_attributes: Optional[dict] = None
    reason: Optional[str] = None


class OCRResponse(BaseModel):
    """Response from the OCR endpoint."""

    ocr_result_id: uuid.UUID
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    confidence: float = Field(ge=0, le=100)
    raw_text: str
    cleaned_text: str
    matches: List[OCRMatchResult] = []
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None
    city: Optional[str] = None
    installation_year: Optional[int] = Field(default=None, ge=1980, le=2030)
    created_at: datetime


class OCRRequest(BaseModel):
    """Optional metadata sent with an OCR upload."""

    installation_year: Optional[int] = Field(default=None, ge=1980, le=2030)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None
    city: Optional[str] = None
