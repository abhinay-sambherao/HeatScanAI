from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, ForeignKey, Text, Float, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Match(Base):
    """Links an OCR result to a matched product with a confidence score."""

    __tablename__ = "matches"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    ocr_result_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ocr_results.id"), nullable=False)
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id"), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    matched_attributes: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    ocr_result: Mapped["OCRResult"] = relationship("OCRResult", back_populates="matches")
    product: Mapped["Product"] = relationship("Product", back_populates="matches")

    def __repr__(self) -> str:
        return f"<Match score={self.score}>"
