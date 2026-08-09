"""Pydantic schemas for product endpoints."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel


class ProductDetail(BaseModel):
    """Full product detail response."""

    id: uuid.UUID
    eprel_id: str
    manufacturer_name: Optional[str] = None
    category_name: Optional[str] = None
    model: str
    supplier: Optional[str] = None
    energy_class: Optional[str] = None
    heat_output: Optional[str] = None
    efficiency: Optional[str] = None
    fuel_type: Optional[str] = None
    release_date: Optional[datetime] = None
    created_at: datetime
    raw_json: Optional[dict] = None

    model_config = {"from_attributes": True}


class ProductListItem(BaseModel):
    """Lightweight product for list views."""

    id: uuid.UUID
    eprel_id: str
    model: str
    energy_class: Optional[str] = None
    fuel_type: Optional[str] = None
    manufacturer_name: Optional[str] = None
    category_name: Optional[str] = None
    heat_output: Optional[str] = None

    model_config = {"from_attributes": True}


class ProductList(BaseModel):
    """Paginated product list."""

    items: List[ProductListItem]
    total: int
    page: int
    page_size: int
