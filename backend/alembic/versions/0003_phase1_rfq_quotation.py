"""Phase 1: rfqs, rfq_items, rfq_supplier_invitations, quotations, quotation_items, negotiation_notes

Revision ID: 0003_phase1_rfq_quotation
Revises: 0002_phase1_identity
Create Date: 2026-10-06 00:00:00.000000

Creates:
  - rfqs
  - rfq_items
  - rfq_supplier_invitations
  - quotations
  - quotation_items
  - negotiation_notes
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003_phase1_rfq_quotation"
down_revision: Union[str, None] = "0002_phase1_identity"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # rfqs
    # ------------------------------------------------------------------
    op.create_table(
        "rfqs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("rfq_number", sa.String(50), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column(
            "destination_country",
            sa.String(2),
            nullable=False,
            comment="ISO 3166-1 alpha-2 country code.",
        ),
        sa.Column("destination_port", sa.String(100), nullable=True),
        sa.Column("required_delivery_date", sa.Date, nullable=True),
        sa.Column("preferred_incoterm", sa.String(10), nullable=True),
        sa.Column("preferred_payment_terms", sa.String(100), nullable=True),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("status", sa.String(50), nullable=False, server_default="DRAFT"),
        sa.Column("awarded_quotation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column(
            "created_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
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
        sa.CheckConstraint(
            "status IN ('DRAFT', 'OPEN', 'INVITATIONS_SENT', 'RESPONSES_RECEIVED', "
            "'UNDER_REVIEW', 'NEGOTIATION', 'AWARDED', 'CANCELLED', 'EXPIRED')",
            name="ck_rfqs_status",
        ),
    )
    op.create_index("ix_rfqs_organization_id", "rfqs", ["organization_id"])
    op.create_index("ix_rfqs_rfq_number", "rfqs", ["rfq_number"], unique=True)
    op.create_index("ix_rfqs_status", "rfqs", ["status"])

    # ------------------------------------------------------------------
    # rfq_items
    # ------------------------------------------------------------------
    op.create_table(
        "rfq_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "rfq_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("rfqs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("item_index", sa.Integer, nullable=False, server_default="1"),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("product_name_snapshot", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("quantity", sa.Numeric(14, 2), nullable=False),
        sa.Column("unit", sa.String(20), nullable=False, server_default="PCS"),
        sa.Column("target_unit_price", sa.Numeric(14, 4), nullable=True),
        sa.Column("specifications", sa.Text, nullable=True),
        sa.Column("quality_requirements", sa.Text, nullable=True),
        sa.Column("packaging_requirements", sa.Text, nullable=True),
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
        sa.CheckConstraint("quantity > 0", name="ck_rfq_items_quantity_positive"),
        sa.CheckConstraint(
            "target_unit_price IS NULL OR target_unit_price >= 0",
            name="ck_rfq_items_target_price_non_negative",
        ),
    )
    op.create_index("ix_rfq_items_rfq_id", "rfq_items", ["rfq_id"])

    # ------------------------------------------------------------------
    # rfq_supplier_invitations
    # ------------------------------------------------------------------
    op.create_table(
        "rfq_supplier_invitations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "rfq_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("rfqs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "supplier_organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("supplier_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("supplier_email", sa.String(255), nullable=False),
        sa.Column("supplier_name", sa.String(255), nullable=False),
        sa.Column(
            "invited_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("status", sa.String(50), nullable=False, server_default="INVITED"),
        sa.Column("response_deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "invited_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("rfq_id", "supplier_email", name="uq_rfq_invitation_rfq_email"),
        sa.CheckConstraint(
            "status IN ('INVITED', 'VIEWED', 'RESPONDED', 'DECLINED', 'EXPIRED')",
            name="ck_rfq_invitations_status",
        ),
    )
    op.create_index("ix_rfq_supplier_invitations_rfq_id", "rfq_supplier_invitations", ["rfq_id"])
    op.create_index(
        "ix_rfq_supplier_invitations_supplier_org_id",
        "rfq_supplier_invitations",
        ["supplier_organization_id"],
    )

    # ------------------------------------------------------------------
    # quotations
    # ------------------------------------------------------------------
    op.create_table(
        "quotations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "rfq_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("rfqs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "supplier_organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "supplier_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("quotation_number", sa.String(50), nullable=False),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column(
            "parent_quotation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("quotations.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("status", sa.String(50), nullable=False, server_default="DRAFT"),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("valid_until", sa.Date, nullable=True),
        sa.Column("incoterm", sa.String(10), nullable=False),
        sa.Column("payment_terms", sa.String(100), nullable=False),
        sa.Column("lead_time_days", sa.Integer, nullable=False, server_default="0"),
        sa.Column("subtotal_amount", sa.Numeric(14, 2), nullable=False, server_default="0.00"),
        sa.Column("shipping_cost", sa.Numeric(14, 2), nullable=True),
        sa.Column("insurance_cost", sa.Numeric(14, 2), nullable=True),
        sa.Column("duty_amount", sa.Numeric(14, 2), nullable=True),
        sa.Column("tax_amount", sa.Numeric(14, 2), nullable=True),
        sa.Column("other_charges", sa.Numeric(14, 2), nullable=True),
        sa.Column("total_landed_cost", sa.Numeric(14, 2), nullable=False, server_default="0.00"),
        sa.Column("supplier_notes", sa.Text, nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.CheckConstraint(
            "status IN ('DRAFT', 'SUBMITTED', 'UNDER_REVIEW', 'ACCEPTED', "
            "'REJECTED', 'SUPERSEDED', 'EXPIRED')",
            name="ck_quotations_status",
        ),
        sa.CheckConstraint("version >= 1", name="ck_quotations_version_positive"),
        sa.CheckConstraint("lead_time_days >= 0", name="ck_quotations_lead_time_non_negative"),
        sa.CheckConstraint("subtotal_amount >= 0", name="ck_quotations_subtotal_non_negative"),
        sa.CheckConstraint("total_landed_cost >= 0", name="ck_quotations_total_landed_cost_non_negative"),
        sa.CheckConstraint("shipping_cost IS NULL OR shipping_cost >= 0", name="ck_quotations_shipping_non_negative"),
        sa.CheckConstraint("insurance_cost IS NULL OR insurance_cost >= 0", name="ck_quotations_insurance_non_negative"),
        sa.CheckConstraint("duty_amount IS NULL OR duty_amount >= 0", name="ck_quotations_duty_non_negative"),
        sa.CheckConstraint("tax_amount IS NULL OR tax_amount >= 0", name="ck_quotations_tax_non_negative"),
        sa.CheckConstraint("other_charges IS NULL OR other_charges >= 0", name="ck_quotations_other_charges_non_negative"),
    )
    op.create_index("ix_quotations_rfq_id", "quotations", ["rfq_id"])
    op.create_index("ix_quotations_supplier_org_id", "quotations", ["supplier_organization_id"])
    op.create_index("ix_quotations_quotation_number", "quotations", ["quotation_number"], unique=True)
    op.create_index("ix_quotations_status", "quotations", ["status"])

    # ------------------------------------------------------------------
    # quotation_items
    # ------------------------------------------------------------------
    op.create_table(
        "quotation_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "quotation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("quotations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "rfq_item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("rfq_items.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("product_name_snapshot", sa.String(255), nullable=False),
        sa.Column("quantity", sa.Numeric(14, 2), nullable=False),
        sa.Column("unit", sa.String(20), nullable=False, server_default="PCS"),
        sa.Column("unit_price", sa.Numeric(14, 4), nullable=False),
        sa.Column("line_total", sa.Numeric(14, 2), nullable=False),
        sa.Column("moq", sa.Numeric(14, 2), nullable=True),
        sa.Column("lead_time_days", sa.Integer, nullable=True),
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
        sa.CheckConstraint("quantity > 0", name="ck_quotation_items_quantity_positive"),
        sa.CheckConstraint("unit_price >= 0", name="ck_quotation_items_unit_price_non_negative"),
        sa.CheckConstraint("line_total >= 0", name="ck_quotation_items_line_total_non_negative"),
        sa.CheckConstraint("moq IS NULL OR moq > 0", name="ck_quotation_items_moq_positive"),
        sa.CheckConstraint("lead_time_days IS NULL OR lead_time_days >= 0", name="ck_quotation_items_lead_time_non_negative"),
    )
    op.create_index("ix_quotation_items_quotation_id", "quotation_items", ["quotation_id"])
    op.create_index("ix_quotation_items_rfq_item_id", "quotation_items", ["rfq_item_id"])

    # ------------------------------------------------------------------
    # negotiation_notes
    # ------------------------------------------------------------------
    op.create_table(
        "negotiation_notes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "quotation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("quotations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "author_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("note_type", sa.String(50), nullable=False),
        sa.Column("proposed_target_price", sa.Numeric(14, 4), nullable=True),
        sa.Column("proposed_terms", sa.Text, nullable=True),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "note_type IN ('BUYER_NOTE', 'COUNTER_OFFER', 'SUPPLIER_RESPONSE')",
            name="ck_negotiation_notes_type",
        ),
        sa.CheckConstraint(
            "proposed_target_price IS NULL OR proposed_target_price >= 0",
            name="ck_negotiation_notes_price_non_negative",
        ),
    )
    op.create_index("ix_negotiation_notes_quotation_id", "negotiation_notes", ["quotation_id"])
    op.create_index("ix_negotiation_notes_organization_id", "negotiation_notes", ["organization_id"])


def downgrade() -> None:
    op.drop_table("negotiation_notes")
    op.drop_table("quotation_items")
    op.drop_table("quotations")
    op.drop_table("rfq_supplier_invitations")
    op.drop_table("rfq_items")
    op.drop_table("rfqs")
