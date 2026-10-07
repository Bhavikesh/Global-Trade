"""Phase 1: products, product_files

Revision ID: 0003_products
Revises: 0002_phase1_identity
Create Date: 2026-10-07 00:00:00.000000

Creates:
  - products
  - product_files
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003_products"
down_revision: Union[str, None] = "0002_phase1_identity"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # products
    # ------------------------------------------------------------------
    op.create_table(
        "products",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("specifications", sa.Text, nullable=True),
        sa.Column("moq", sa.String(100), nullable=True),
        sa.Column("packaging", sa.Text, nullable=True),
        sa.Column("pricing_information", sa.Text, nullable=True),
        sa.Column("hs_code", sa.String(20), nullable=True),
        sa.Column("keywords", sa.Text, nullable=True),
        sa.Column("seo_description", sa.Text, nullable=True),
        sa.Column("international_description", sa.Text, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="ACTIVE"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint("status IN ('ACTIVE', 'ARCHIVED')", name="ck_products_status"),
    )
    op.create_index(
        "ix_products_organization_id",
        "products",
        ["organization_id"],
    )

    # ------------------------------------------------------------------
    # product_files
    # ------------------------------------------------------------------
    op.create_table(
        "product_files",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "product_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("products.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("file_reference", sa.String(1024), nullable=False),
        sa.Column("file_type", sa.String(50), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_product_files_product_id",
        "product_files",
        ["product_id"],
    )
    op.create_index(
        "ix_product_files_organization_id",
        "product_files",
        ["organization_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_product_files_organization_id", table_name="product_files")
    op.drop_index("ix_product_files_product_id", table_name="product_files")
    op.drop_table("product_files")
    op.drop_index("ix_products_organization_id", table_name="products")
    op.drop_table("products")
