from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, ForeignKey, Text, Float, Date, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Product(Base):
    """Represents a product from the EPREL database."""

    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    eprel_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    manufacturer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("manufacturers.id"), nullable=False)
    category_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("categories.id"), nullable=True)
    model: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    supplier: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    energy_class: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    heat_output: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    efficiency: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    fuel_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    release_date: Mapped[Optional[datetime]] = mapped_column(Date, nullable=True)
    source: Mapped[Optional[str]] = mapped_column(String(50), nullable=True,
                                                  server_default="EPREL", index=True)
    raw_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    manufacturer: Mapped["Manufacturer"] = relationship("Manufacturer", back_populates="products")
    category: Mapped[Optional["Category"]] = relationship("Category", back_populates="products")
    matches: Mapped[list["Match"]] = relationship("Match", back_populates="product")

    def __repr__(self) -> str:
        return f"<Product {self.manufacturer_id} {self.model}>"
