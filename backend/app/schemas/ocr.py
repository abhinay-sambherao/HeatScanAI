"""Pydantic schemas for OCR endpoints."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


class OCRMatchResult(BaseModel):
    """A single product match from OCR analysis."""

    product_id: Optional[uuid.UUID] = None
    manufacturer: str
    model: str
    name: Optional[str] = None
    retail_url: Optional[str] = None
    retail_price: Optional[float] = None
    retail_currency: Optional[str] = None
    retail_source: Optional[str] = None
    energy_class: Optional[str] = None
    fuel_type: Optional[str] = None
    heat_output: Optional[str] = None
    score: float = Field(ge=0, le=100)
    match_type: Optional[str] = None
    matched_attributes: Optional[dict] = None
    reason: Optional[str] = None


class ImageResult(BaseModel):
    """OCR result for a single image in a multi-image upload."""

    filename: str
    confidence: float = Field(ge=0, le=100)
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    energy_class: Optional[str] = None
    fuel_type: Optional[str] = None
    heat_output: Optional[str] = None
    raw_text: str = ""


class OCRResponse(BaseModel):
    """Response from the OCR endpoint."""

    ocr_result_id: uuid.UUID
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    energy_class: Optional[str] = None
    fuel_type: Optional[str] = None
    heat_output: Optional[str] = None
    confidence: float = Field(ge=0, le=100)
    raw_text: str
    cleaned_text: str
    matches: List[OCRMatchResult] = []
    images: List[ImageResult] = []
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None
    installation_year: Optional[int] = Field(default=None, ge=1980, le=2030)
    created_at: datetime


class OCRRequest(BaseModel):
    """Optional metadata sent with an OCR upload."""

    installation_year: Optional[int] = Field(default=None, ge=1980, le=2030)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None


class RematchRequest(BaseModel):
    """Request to re-match an OCR result with a user-provided year."""

    installation_year: int = Field(ge=1980, le=2030)


class RematchResponse(BaseModel):
    """Response from the rematch endpoint."""

    ocr_result_id: uuid.UUID
    installation_year: int
    matches: List[OCRMatchResult]
