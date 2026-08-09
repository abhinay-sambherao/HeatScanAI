from __future__ import annotations

"""Product endpoints: detail view and paginated list."""

import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.product import Product
from app.schemas.product import ProductDetail, ProductListItem, ProductList
from app.services.product_service import get_product_by_id, list_products
from app.core.exceptions import ProductNotFoundError

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("/{product_id}", response_model=ProductDetail)
async def get_product(
    product_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> ProductDetail:
    """Get full product details by ID."""
    product = await get_product_by_id(db, product_id)
    if not product:
        raise ProductNotFoundError(str(product_id))

    return ProductDetail(
        id=product.id,
        eprel_id=product.eprel_id,
        manufacturer_name=product.manufacturer.name if product.manufacturer else None,
        category_name=product.category.name if product.category else None,
        model=product.model,
        supplier=product.supplier,
        energy_class=product.energy_class,
        heat_output=product.heat_output,
        efficiency=product.efficiency,
        fuel_type=product.fuel_type,
        release_date=product.release_date,
        created_at=product.created_at,
        raw_json=product.raw_json,
    )


@router.get("/eprel/{eprel_id}", response_model=ProductDetail)
async def get_product_by_eprel(
    eprel_id: str,
    db: AsyncSession = Depends(get_db),
) -> ProductDetail:
    """Get full product details by EPREL registration number."""
    stmt = (
        select(Product)
        .options(selectinload(Product.manufacturer), selectinload(Product.category))
        .where(Product.eprel_id == eprel_id)
    )
    result = await db.execute(stmt)
    product = result.scalar_one_or_none()
    if not product:
        raise ProductNotFoundError(eprel_id)

    return ProductDetail(
        id=product.id,
        eprel_id=product.eprel_id,
        manufacturer_name=product.manufacturer.name if product.manufacturer else None,
        category_name=product.category.name if product.category else None,
        model=product.model,
        supplier=product.supplier,
        energy_class=product.energy_class,
        heat_output=product.heat_output,
        efficiency=product.efficiency,
        fuel_type=product.fuel_type,
        release_date=product.release_date,
        created_at=product.created_at,
        raw_json=product.raw_json,
    )


@router.get("", response_model=ProductList)
async def get_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    energy_class: Optional[str] = Query(None),
    fuel_type: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> ProductList:
    """List products with pagination and optional search/filters."""
    products, total = await list_products(
        db,
        page=page,
        page_size=page_size,
        search=search,
        category=category,
        energy_class=energy_class,
        fuel_type=fuel_type,
    )

    items = [
        ProductListItem(
            id=p.id,
            eprel_id=p.eprel_id,
            model=p.model,
            energy_class=p.energy_class,
            fuel_type=p.fuel_type,
            manufacturer_name=p.manufacturer.name if p.manufacturer else None,
            category_name=p.category.name if p.category else None,
            heat_output=p.heat_output,
        )
        for p in products
    ]

    return ProductList(items=items, total=total, page=page, page_size=page_size)
