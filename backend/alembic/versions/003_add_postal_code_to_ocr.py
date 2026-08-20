"""Add postal_code column to ocr_results table.

Revision ID: 003_add_postal_code_to_ocr
Revises: 002_add_location_to_ocr
Create Date: 2026-08-18
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "003_add_postal_code_to_ocr"
down_revision: Union[str, None] = "002_add_location_to_ocr"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("ocr_results", sa.Column("postal_code", sa.String(20), nullable=True))


def downgrade() -> None:
    op.drop_column("ocr_results", "postal_code")
