"""Pydantic schemas for category endpoints."""
from __future__ import annotations

from pydantic import BaseModel


class CategoryOut(BaseModel):
    """Category response."""

    name: str
    product_count: int
