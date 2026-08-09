from __future__ import annotations

"""Category endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.category import CategoryOut
from app.services.product_service import list_categories

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("", response_model=list[CategoryOut])
async def get_categories(
    db: AsyncSession = Depends(get_db),
) -> list[CategoryOut]:
    """List all categories with product counts."""
    categories = await list_categories(db)
    return [CategoryOut(name=c["name"], product_count=c["product_count"]) for c in categories]
