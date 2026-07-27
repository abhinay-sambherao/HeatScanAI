from __future__ import annotations

"""Manufacturer endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.manufacturer import ManufacturerOut
from app.services.product_service import list_manufacturers

router = APIRouter(prefix="/manufacturers", tags=["Manufacturers"])


@router.get("", response_model=list[ManufacturerOut])
async def get_manufacturers(
    db: AsyncSession = Depends(get_db),
) -> list[ManufacturerOut]:
    """List all manufacturers with product counts."""
    manufacturers = await list_manufacturers(db)
    return [
        ManufacturerOut(
            id=m["id"],
            name=m["name"],
            product_count=m["product_count"],
            created_at=m["created_at"],
        )
        for m in manufacturers
    ]
