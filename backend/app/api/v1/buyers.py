"""
Buyer CRUD routes — /api/v1/organizations/{organization_id}/buyers

Authoritative source: docs/DATA_MODEL.md section 11 & docs/TASKS.md T1.13, T1.14.
Endpoints:
  POST   /api/v1/organizations/{organization_id}/buyers
  GET    /api/v1/organizations/{organization_id}/buyers
  GET    /api/v1/organizations/{organization_id}/buyers/{buyer_id}
  PATCH  /api/v1/organizations/{organization_id}/buyers/{buyer_id}
  DELETE /api/v1/organizations/{organization_id}/buyers/{buyer_id}
"""
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.auth.dependencies import get_current_user
from app.core.auth.permissions import (
    get_membership_or_403,
    require_organization_membership,
)
from app.db.session import get_db
from app.models.buyer import Buyer
from app.models.user import User
from app.schemas.buyer import (
    VALID_VERIFICATION_STATUSES,
    BuyerCreate,
    BuyerListResponse,
    BuyerRead,
    BuyerUpdate,
)

router = APIRouter(
    prefix="/organizations/{organization_id}/buyers",
    tags=["Buyers"],
)


@router.get(
    "",
    response_model=BuyerListResponse,
    summary="List buyers for an organization with search, filtering, and pagination",
)
def list_buyers(
    organization_id: uuid.UUID,
    q: Optional[str] = Query(None, description="Case-insensitive search across company_name, contact_name, email"),
    country: Optional[str] = Query(None, description="Exact 2-letter ISO country code"),
    verification_status: Optional[str] = Query(None, description="Exact verification status filter"),
    industry: Optional[str] = Query(None, description="Exact industry filter"),
    limit: int = Query(20, ge=1, le=100, description="Page limit (1-100, default 20)"),
    offset: int = Query(0, ge=0, description="Page offset (>= 0, default 0)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BuyerListResponse:
    """List buyers belonging to the organization with optional search, filters, and pagination."""
    get_membership_or_403(organization_id, current_user, db)

    query = db.query(Buyer).filter_by(organization_id=organization_id)

    # Search (q) across company_name, contact_name, email (case-insensitive)
    if q is not None and q.strip():
        search_pattern = f"%{q.strip()}%"
        query = query.filter(
            or_(
                Buyer.company_name.ilike(search_pattern),
                Buyer.contact_name.ilike(search_pattern),
                Buyer.email.ilike(search_pattern),
            )
        )

    # Country filter (exact, validated against 2-letter alpha-2 format)
    if country is not None:
        cleaned_country = country.strip().upper()
        if len(cleaned_country) != 2 or not cleaned_country.isalpha():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Country code must be a 2-letter ISO 3166-1 alpha-2 code.",
            )
        query = query.filter(Buyer.country == cleaned_country)

    # Verification status filter (exact, validated against allowed statuses)
    if verification_status is not None:
        cleaned_status = verification_status.strip().upper()
        if cleaned_status not in VALID_VERIFICATION_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid verification status '{verification_status}'. Allowed values are: {', '.join(sorted(VALID_VERIFICATION_STATUSES))}",
            )
        query = query.filter(Buyer.verification_status == cleaned_status)

    # Industry filter (exact)
    if industry is not None and industry.strip():
        query = query.filter(Buyer.industry == industry.strip())

    total = query.count()
    items = (
        query.order_by(Buyer.created_at.desc(), Buyer.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return BuyerListResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post(
    "",
    response_model=BuyerRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new buyer",
)
def create_buyer(
    organization_id: uuid.UUID,
    body: BuyerCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BuyerRead:
    """Create a new buyer under the specified organization."""
    require_organization_membership(organization_id, current_user, db)

    buyer = Buyer(
        organization_id=organization_id,
        **body.model_dump(),
    )
    db.add(buyer)
    db.commit()
    db.refresh(buyer)
    return buyer


@router.get(
    "/{buyer_id}",
    response_model=BuyerRead,
    summary="Get buyer details by ID",
)
def get_buyer(
    organization_id: uuid.UUID,
    buyer_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BuyerRead:
    """Retrieve buyer details by ID. Scoped strictly to the caller's organization."""
    get_membership_or_403(organization_id, current_user, db)

    buyer = (
        db.query(Buyer)
        .filter_by(id=buyer_id, organization_id=organization_id)
        .first()
    )
    if buyer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Buyer not found.",
        )
    return buyer


@router.patch(
    "/{buyer_id}",
    response_model=BuyerRead,
    summary="Update a buyer by ID",
)
def update_buyer(
    organization_id: uuid.UUID,
    buyer_id: uuid.UUID,
    body: BuyerUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BuyerRead:
    """Update fields on an existing buyer. Scoped strictly to the caller's organization."""
    require_organization_membership(organization_id, current_user, db)

    buyer = (
        db.query(Buyer)
        .filter_by(id=buyer_id, organization_id=organization_id)
        .first()
    )
    if buyer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Buyer not found.",
        )

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(buyer, field, value)

    db.add(buyer)
    db.commit()
    db.refresh(buyer)
    return buyer


@router.delete(
    "/{buyer_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a buyer by ID",
)
def delete_buyer(
    organization_id: uuid.UUID,
    buyer_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Delete a buyer record by ID. Scoped strictly to the caller's organization."""
    require_organization_membership(organization_id, current_user, db)

    buyer = (
        db.query(Buyer)
        .filter_by(id=buyer_id, organization_id=organization_id)
        .first()
    )
    if buyer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Buyer not found.",
        )

    db.delete(buyer)
    db.commit()
