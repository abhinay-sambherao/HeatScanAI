"""Add location columns to ocr_results table.

Revision ID: 002_add_location_to_ocr
Revises: 001_initial
Create Date: 2026-07-29
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002_add_location_to_ocr"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("ocr_results", sa.Column("latitude", sa.Float(), nullable=True))
    op.add_column("ocr_results", sa.Column("longitude", sa.Float(), nullable=True))
    op.add_column("ocr_results", sa.Column("address", sa.String(500), nullable=True))
    op.add_column("ocr_results", sa.Column("city", sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column("ocr_results", "city")
    op.drop_column("ocr_results", "address")
    op.drop_column("ocr_results", "longitude")
    op.drop_column("ocr_results", "latitude")
