"""Phase 1: buyers, suppliers, crm_contacts

Revision ID: 0003_buyer_supplier_contacts
Revises: 0002_phase1_identity
Create Date: 2026-10-07 00:00:00.000000

Creates:
  - buyers
  - suppliers
  - crm_contacts
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003_buyer_supplier_contacts"
down_revision: Union[str, None] = "0002_phase1_identity"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # buyers
    # ------------------------------------------------------------------
    op.create_table(
        "buyers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("company_name", sa.String(255), nullable=False),
        sa.Column("contact_name", sa.String(255), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column(
            "country",
            sa.String(2),
            nullable=True,
            comment="ISO 3166-1 alpha-2 country code.",
        ),
        sa.Column("address", sa.Text, nullable=True),
        sa.Column("website", sa.String(500), nullable=True),
        sa.Column("industry", sa.String(100), nullable=True),
        sa.Column(
            "verification_status",
            sa.String(50),
            nullable=False,
            server_default="UNVERIFIED",
        ),
        sa.Column("notes", sa.Text, nullable=True),
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
    )
    op.create_index("ix_buyers_organization_id", "buyers", ["organization_id"])
    op.create_index("ix_buyers_company_name", "buyers", ["company_name"])
    op.create_index("ix_buyers_email", "buyers", ["email"])
    op.create_index("ix_buyers_country", "buyers", ["country"])
    op.create_index("ix_buyers_industry", "buyers", ["industry"])
    op.create_index("ix_buyers_verification_status", "buyers", ["verification_status"])

    # ------------------------------------------------------------------
    # suppliers
    # ------------------------------------------------------------------
    op.create_table(
        "suppliers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("company_name", sa.String(255), nullable=False),
        sa.Column("contact_name", sa.String(255), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column(
            "country",
            sa.String(2),
            nullable=True,
            comment="ISO 3166-1 alpha-2 country code.",
        ),
        sa.Column("address", sa.Text, nullable=True),
        sa.Column("website", sa.String(500), nullable=True),
        sa.Column("supplier_type", sa.String(100), nullable=True),
        sa.Column(
            "verification_status",
            sa.String(50),
            nullable=False,
            server_default="UNVERIFIED",
        ),
        sa.Column("certifications", sa.Text, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
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
    )
    op.create_index("ix_suppliers_organization_id", "suppliers", ["organization_id"])
    op.create_index("ix_suppliers_company_name", "suppliers", ["company_name"])
    op.create_index("ix_suppliers_email", "suppliers", ["email"])
    op.create_index("ix_suppliers_country", "suppliers", ["country"])
    op.create_index("ix_suppliers_supplier_type", "suppliers", ["supplier_type"])
    op.create_index("ix_suppliers_verification_status", "suppliers", ["verification_status"])

    # ------------------------------------------------------------------
    # crm_contacts
    # ------------------------------------------------------------------
    op.create_table(
        "crm_contacts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "buyer_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("buyers.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "supplier_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("suppliers.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("designation", sa.String(100), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("is_primary", sa.Boolean, nullable=False, server_default=sa.false()),
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
    )
    op.create_index("ix_crm_contacts_organization_id", "crm_contacts", ["organization_id"])
    op.create_index("ix_crm_contacts_buyer_id", "crm_contacts", ["buyer_id"])
    op.create_index("ix_crm_contacts_supplier_id", "crm_contacts", ["supplier_id"])


def downgrade() -> None:
    op.drop_table("crm_contacts")
    op.drop_table("suppliers")
    op.drop_table("buyers")
