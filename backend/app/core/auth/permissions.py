"""
Permissions — application-level role-based authorization.

GlobalTrade.ai uses PostgreSQL OrganizationMembership as the source of truth
for roles and access (DEC-038).  Auth0 Organization/RBAC features are NOT used.

Role hierarchy (from DATA_MODEL.md section 8):
  ADMIN       — full organization access
  EXPORTER    — manages export operations
  IMPORTER    — manages import operations
  BUYER       — buyer-side workflows
  SUPPLIER    — supplier-side workflows
  OPERATIONS  — operations tasks
  FINANCE     — finance tasks
  COMPLIANCE  — compliance tasks
  LOGISTICS   — logistics tasks
  MEMBER      — read-mostly access

Permission enforcement must always happen in the backend.
Frontend UI may reflect permissions for UX, but frontend checks are not the
security boundary (DEC-028, ARCHITECTURE.md 3.4).
"""
import uuid
from typing import Set
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth.dependencies import get_current_user
from app.db.session import get_db
from app.models.organization_membership import OrganizationMembership
from app.models.user import User

# ---------------------------------------------------------------------------
# Role constants
# ---------------------------------------------------------------------------
ROLE_ADMIN = "ADMIN"
ROLE_EXPORTER = "EXPORTER"
ROLE_IMPORTER = "IMPORTER"
ROLE_BUYER = "BUYER"
ROLE_SUPPLIER = "SUPPLIER"
ROLE_OPERATIONS = "OPERATIONS"
ROLE_FINANCE = "FINANCE"
ROLE_COMPLIANCE = "COMPLIANCE"
ROLE_LOGISTICS = "LOGISTICS"
ROLE_MEMBER = "MEMBER"

ALL_ROLES = {
    ROLE_ADMIN,
    ROLE_EXPORTER,
    ROLE_IMPORTER,
    ROLE_BUYER,
    ROLE_SUPPLIER,
    ROLE_OPERATIONS,
    ROLE_FINANCE,
    ROLE_COMPLIANCE,
    ROLE_LOGISTICS,
    ROLE_MEMBER,
}

# ---------------------------------------------------------------------------
# Permission helpers
# ---------------------------------------------------------------------------


def require_organization_membership(
    organization_id: uuid.UUID | str,
    user: User,
    db: Session,
    allowed_roles: Set[str] | None = None,
) -> OrganizationMembership:
    """
    Verify that `user` is an ACTIVE member of `organization_id` and (optionally)
    that their role is in `allowed_roles`.

    Raises HTTP 403 if access is denied.  Returns the membership record on success.

    This is the primary enforcement function for organization-level isolation (DEC-028).
    """
    if isinstance(organization_id, str):
        try:
            organization_id = uuid.UUID(organization_id)
        except (ValueError, AttributeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid organization ID format.",
            )

    membership = (
        db.query(OrganizationMembership)
        .filter_by(organization_id=organization_id, user_id=user.id, status="ACTIVE")
        .first()
    )

    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: you are not a member of this organization.",
        )

    if allowed_roles and membership.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: your role '{membership.role}' is not permitted to perform this action.",
        )

    return membership


def get_membership_or_403(
    organization_id: uuid.UUID | str,
    user: User,
    db: Session,
) -> OrganizationMembership:
    """
    Convenience wrapper: verify any active membership exists for `user` in
    `organization_id`.  Used for read operations where any member role suffices.
    """
    return require_organization_membership(organization_id, user, db, allowed_roles=None)


def require_admin(
    organization_id: uuid.UUID | str,
    user: User,
    db: Session,
) -> OrganizationMembership:
    """Verify that the user has the ADMIN role in the organization."""
    return require_organization_membership(
        organization_id, user, db, allowed_roles={ROLE_ADMIN}
    )

