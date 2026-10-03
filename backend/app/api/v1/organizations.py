"""
Organization routes — /api/v1/organizations

POST   /                         — create a new organization (creator becomes ADMIN)
GET    /                         — list organizations the authenticated user belongs to
GET    /{organization_id}        — get a specific organization (members only)
PATCH  /{organization_id}        — update organization details (ADMIN only)

Membership sub-routes:
GET    /{organization_id}/members                   — list members (any active member)
POST   /{organization_id}/members                   — invite a user (ADMIN only)
PATCH  /{organization_id}/members/{membership_id}   — update member role (ADMIN only)
DELETE /{organization_id}/members/{membership_id}   — remove a member (ADMIN only)
"""
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth.dependencies import get_current_user
from app.core.auth.permissions import (
    ROLE_ADMIN,
    require_admin,
    get_membership_or_403,
)
from app.db.session import get_db
from app.models.organization import Organization
from app.models.organization_membership import OrganizationMembership
from app.models.user import User
from app.schemas.organization import OrganizationCreate, OrganizationRead, OrganizationUpdate
from app.schemas.membership import MembershipInvite, MembershipRead, MembershipRoleUpdate

router = APIRouter(prefix="/organizations", tags=["Organizations"])


# ---------------------------------------------------------------------------
# Organization CRUD
# ---------------------------------------------------------------------------


@router.post(
    "/",
    response_model=OrganizationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new organization",
)
def create_organization(
    body: OrganizationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OrganizationRead:
    """
    Create a new organization.
    The authenticated user automatically becomes the organization ADMIN.
    """
    org = Organization(**body.model_dump())
    db.add(org)
    db.flush()  # obtain org.id before creating membership

    membership = OrganizationMembership(
        organization_id=org.id,
        user_id=current_user.id,
        role=ROLE_ADMIN,
        status="ACTIVE",
    )
    db.add(membership)
    db.commit()
    db.refresh(org)
    return org


@router.get(
    "/",
    response_model=List[OrganizationRead],
    summary="List organizations the authenticated user belongs to",
)
def list_my_organizations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[OrganizationRead]:
    """Return all organizations the authenticated user is an active member of."""
    memberships = (
        db.query(OrganizationMembership)
        .filter_by(user_id=current_user.id, status="ACTIVE")
        .all()
    )
    org_ids = [m.organization_id for m in memberships]
    if not org_ids:
        return []
    return db.query(Organization).filter(Organization.id.in_(org_ids)).all()


@router.get(
    "/{organization_id}",
    response_model=OrganizationRead,
    summary="Get an organization (members only)",
)
def get_organization(
    organization_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OrganizationRead:
    """Return organization details.  Accessible only to active members."""
    get_membership_or_403(organization_id, current_user, db)

    org = db.query(Organization).filter_by(id=organization_id).first()
    if org is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found.")
    return org


@router.patch(
    "/{organization_id}",
    response_model=OrganizationRead,
    summary="Update organization details (ADMIN only)",
)
def update_organization(
    organization_id: uuid.UUID,
    body: OrganizationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OrganizationRead:
    """Update mutable fields on an organization.  Requires ADMIN role."""
    require_admin(organization_id, current_user, db)

    org = db.query(Organization).filter_by(id=organization_id).first()
    if org is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found.")

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(org, field, value)

    db.add(org)
    db.commit()
    db.refresh(org)
    return org


# ---------------------------------------------------------------------------
# Membership sub-routes
# ---------------------------------------------------------------------------


@router.get(
    "/{organization_id}/members",
    response_model=List[MembershipRead],
    summary="List organization members (any active member)",
)
def list_members(
    organization_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[MembershipRead]:
    """List all active memberships in an organization."""
    get_membership_or_403(organization_id, current_user, db)

    return (
        db.query(OrganizationMembership)
        .filter_by(organization_id=organization_id)
        .all()
    )


@router.post(
    "/{organization_id}/members",
    response_model=MembershipRead,
    status_code=status.HTTP_201_CREATED,
    summary="Add a member to the organization (ADMIN only)",
)
def add_member(
    organization_id: uuid.UUID,
    body: MembershipInvite,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MembershipRead:
    """Add an existing user to the organization.  Requires ADMIN role."""
    require_admin(organization_id, current_user, db)

    # Verify target user exists
    target_user = db.query(User).filter_by(id=body.user_id).first()
    if target_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    # Prevent duplicate membership
    existing = (
        db.query(OrganizationMembership)
        .filter_by(organization_id=organization_id, user_id=body.user_id)
        .first()
    )
    if existing:
        if existing.status == "ACTIVE":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User is already an active member of this organization.",
            )
        # Re-activate removed/inactive membership
        existing.status = "ACTIVE"
        existing.role = body.role
        db.add(existing)
        db.commit()
        db.refresh(existing)
        return existing

    membership = OrganizationMembership(
        organization_id=organization_id,
        user_id=body.user_id,
        role=body.role,
        status="ACTIVE",
    )
    db.add(membership)
    db.commit()
    db.refresh(membership)
    return membership


@router.patch(
    "/{organization_id}/members/{membership_id}",
    response_model=MembershipRead,
    summary="Update a member's role (ADMIN only)",
)
def update_member_role(
    organization_id: uuid.UUID,
    membership_id: uuid.UUID,
    body: MembershipRoleUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MembershipRead:
    """Update the role of an organization member.  Requires ADMIN role."""
    require_admin(organization_id, current_user, db)

    membership = (
        db.query(OrganizationMembership)
        .filter_by(id=membership_id, organization_id=organization_id)
        .first()
    )
    if membership is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membership not found.")

    # Prevent demoting the last active ADMIN
    if membership.role == ROLE_ADMIN and membership.status == "ACTIVE" and body.role != ROLE_ADMIN:
        admin_count = (
            db.query(OrganizationMembership)
            .filter_by(organization_id=organization_id, role=ROLE_ADMIN, status="ACTIVE")
            .count()
        )
        if admin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot demote the last active ADMIN from an organization.",
            )

    membership.role = body.role
    db.add(membership)
    db.commit()
    db.refresh(membership)
    return membership


@router.delete(
    "/{organization_id}/members/{membership_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a member from the organization (ADMIN only)",
)
def remove_member(
    organization_id: uuid.UUID,
    membership_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Remove a member from the organization (marks status as REMOVED).  Requires ADMIN role."""
    require_admin(organization_id, current_user, db)

    membership = (
        db.query(OrganizationMembership)
        .filter_by(id=membership_id, organization_id=organization_id)
        .first()
    )
    if membership is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membership not found.")

    # Prevent removing the last active ADMIN
    if membership.role == ROLE_ADMIN and membership.status == "ACTIVE":
        admin_count = (
            db.query(OrganizationMembership)
            .filter_by(organization_id=organization_id, role=ROLE_ADMIN, status="ACTIVE")
            .count()
        )
        if admin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove the last active ADMIN from an organization.",
            )

    membership.status = "REMOVED"
    db.add(membership)
    db.commit()

