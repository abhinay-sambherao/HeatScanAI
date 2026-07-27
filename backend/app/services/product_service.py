from __future__ import annotations

"""Product CRUD service."""

import uuid
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.product import Product
from app.models.manufacturer import Manufacturer


async def get_product_by_id(db: AsyncSession, product_id: uuid.UUID) -> Product | None:
    """Fetch a single product by ID with manufacturer and category."""
    stmt = (
        select(Product)
        .options(selectinload(Product.manufacturer), selectinload(Product.category))
        .where(Product.id == product_id)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def list_products(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    search: str | None = None,
) -> tuple[list[Product], int]:
    """List products with pagination and optional search.

    Returns:
        Tuple of (products list, total count).
    """
    base_stmt = select(Product).options(
        selectinload(Product.manufacturer),
        selectinload(Product.category),
    )

    if search:
        pattern = f"%{search}%"
        base_stmt = base_stmt.where(
            Product.model.ilike(pattern) | Product.eprel_id.ilike(pattern)
        )

    count_stmt = select(func.count()).select_from(Product)
    if search:
        pattern = f"%{search}%"
        count_stmt = count_stmt.where(
            Product.model.ilike(pattern) | Product.eprel_id.ilike(pattern)
        )

    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    stmt = base_stmt.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    products = list(result.scalars().all())

    return products, total


async def list_manufacturers(db: AsyncSession) -> list[dict]:
    """List all manufacturers with product counts."""
    stmt = (
        select(
            Manufacturer.id,
            Manufacturer.name,
            Manufacturer.created_at,
            func.count(Product.id).label("product_count"),
        )
        .outerjoin(Product, Manufacturer.id == Product.manufacturer_id)
        .group_by(Manufacturer.id, Manufacturer.name, Manufacturer.created_at)
        .order_by(Manufacturer.name)
    )
    result = await db.execute(stmt)
    return [
        {
            "id": row.id,
            "name": row.name,
            "product_count": row.product_count,
            "created_at": row.created_at,
        }
        for row in result.all()
    ]
