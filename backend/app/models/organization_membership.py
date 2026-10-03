"""
OrganizationMembership model — connects users to organizations.

This is the application-level source of truth for tenancy and role-based
permissions (DEC-038).  Auth0 Organization features are NOT used; all
role and membership data lives here.

Roles (initial set — from DATA_MODEL.md section 8):
  ADMIN        — full access within the organization
  EXPORTER     — manages export operations
  IMPORTER     — manages import operations
  BUYER        — manages buyer-side workflows
  SUPPLIER     — manages supplier-side workflows
  OPERATIONS   — logistics and operations tasks
  FINANCE      — finance-related tasks
  COMPLIANCE   — compliance tasks
  LOGISTICS    — logistics tasks
  MEMBER       — read-mostly access

Status:
  ACTIVE | INVITED | INACTIVE | REMOVED
"""
import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, func, UniqueConstraint, Uuid
from sqlalchemy.orm import relationship

from app.db.session import Base


class OrganizationMembership(Base):
    __tablename__ = "organization_memberships"

    __table_args__ = (
        UniqueConstraint("organization_id", "user_id", name="uq_org_user"),
    )

    id: uuid.UUID = Column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )

    organization_id: uuid.UUID = Column(
        Uuid(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    user_id: uuid.UUID = Column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Application role — the source of truth for what the user can do.
    role: str = Column(String(50), nullable=False, default="MEMBER")

    # ACTIVE | INVITED | INACTIVE | REMOVED
    status: str = Column(String(50), nullable=False, default="ACTIVE")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    organization = relationship("Organization", back_populates="memberships")
    user = relationship("User", back_populates="memberships")

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<OrganizationMembership org={self.organization_id} "
            f"user={self.user_id} role={self.role!r}>"
        )
