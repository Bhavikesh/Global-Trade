"""Phase 1: users, organizations, organization_memberships

Revision ID: 0002_phase1_identity
Revises: 0001_init_vector
Create Date: 2026-10-02 00:00:00.000000

Creates:
  - users
  - organizations
  - organization_memberships
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002_phase1_identity"
down_revision: Union[str, None] = "0001_init_vector"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # users
    # ------------------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "identity_provider_id",
            sa.String(255),
            unique=True,
            nullable=False,
            comment="Auth0 subject claim (sub) — unique user identity from the IdP.",
        ),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="ACTIVE"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
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
    op.create_index("ix_users_identity_provider_id", "users", ["identity_provider_id"], unique=True)
    op.create_index("ix_users_email", "users", ["email"])

    # ------------------------------------------------------------------
    # organizations
    # ------------------------------------------------------------------
    op.create_table(
        "organizations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("legal_name", sa.String(500), nullable=False),
        sa.Column("display_name", sa.String(255), nullable=True),
        sa.Column("business_type", sa.String(100), nullable=True),
        sa.Column(
            "country",
            sa.String(2),
            nullable=True,
            comment="ISO 3166-1 alpha-2 country code.",
        ),
        sa.Column("address", sa.Text, nullable=True),
        sa.Column("tax_identifier", sa.String(100), nullable=True),
        sa.Column("vat_identifier", sa.String(100), nullable=True),
        sa.Column(
            "iec_number",
            sa.String(100),
            nullable=True,
            comment="Import Export Code (India).",
        ),
        sa.Column("website", sa.String(500), nullable=True),
        sa.Column("contact_information", sa.Text, nullable=True),
        sa.Column(
            "verification_status",
            sa.String(50),
            nullable=False,
            server_default="UNVERIFIED",
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
    )

    # ------------------------------------------------------------------
    # organization_memberships
    # ------------------------------------------------------------------
    op.create_table(
        "organization_memberships",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.String(50), nullable=False, server_default="MEMBER"),
        sa.Column("status", sa.String(50), nullable=False, server_default="ACTIVE"),
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
        sa.UniqueConstraint("organization_id", "user_id", name="uq_org_user"),
    )
    op.create_index(
        "ix_org_memberships_organization_id",
        "organization_memberships",
        ["organization_id"],
    )
    op.create_index(
        "ix_org_memberships_user_id",
        "organization_memberships",
        ["user_id"],
    )


def downgrade() -> None:
    op.drop_table("organization_memberships")
    op.drop_table("organizations")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_identity_provider_id", table_name="users")
    op.drop_table("users")
