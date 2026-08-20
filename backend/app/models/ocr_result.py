from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, Text, Float, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class OCRResult(Base):
    """Stores the result of an OCR scan on an uploaded image."""

    __tablename__ = "ocr_results"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    cleaned_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    image_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    installation_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    matches: Mapped[list["Match"]] = relationship("Match", back_populates="ocr_result")

    def __repr__(self) -> str:
        return f"<OCRResult {self.filename} confidence={self.confidence}>"
