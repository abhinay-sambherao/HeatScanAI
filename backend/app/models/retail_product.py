from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Text, DateTime, Float, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class RetailProduct(Base):
    """A product offered by a retail marketplace (e.g. heizungsdiscount24).

    Used as a *retail enrichment* source: after the EPREL/manufacturer
    matching chain, scans can surface a real, currently purchasable unit with
    its reseller URL and price. The model/name is matched against OCR output
    the same way EPREL products are, but a retail entry never replaces an
    EPREL identification — it is shown as an extra, tagged "retail".
    """

    __tablename__ = "retail_products"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="heizungsdiscount24")
    brand: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    model: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    mpn: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    sku: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    currency: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self) -> str:
        return f"<RetailProduct {self.brand} {self.model}>"
