"""
Supplier CRUD routes — /api/v1/organizations/{organization_id}/suppliers

Authoritative source: docs/DATA_MODEL.md section 12 & docs/TASKS.md T1.15, T1.16, T1.17.
Endpoints:
  POST   /api/v1/organizations/{organization_id}/suppliers
  GET    /api/v1/organizations/{organization_id}/suppliers
  GET    /api/v1/organizations/{organization_id}/suppliers/{supplier_id}
  PATCH  /api/v1/organizations/{organization_id}/suppliers/{supplier_id}
  DELETE /api/v1/organizations/{organization_id}/suppliers/{supplier_id}
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
from app.models.supplier import Supplier
from app.models.user import User
from app.schemas.supplier import (
    VALID_VERIFICATION_STATUSES,
    SupplierCreate,
    SupplierListResponse,
    SupplierRead,
    SupplierUpdate,
)

router = APIRouter(
    prefix="/organizations/{organization_id}/suppliers",
    tags=["Suppliers"],
)


@router.get(
    "",
    response_model=SupplierListResponse,
    summary="List suppliers for an organization with search, filtering, and pagination",
)
def list_suppliers(
    organization_id: uuid.UUID,
    q: Optional[str] = Query(None, description="Case-insensitive search across company_name, contact_name, email"),
    country: Optional[str] = Query(None, description="Exact 2-letter ISO country code"),
    verification_status: Optional[str] = Query(None, description="Exact verification status filter"),
    supplier_type: Optional[str] = Query(None, description="Exact supplier type filter"),
    limit: int = Query(20, ge=1, le=100, description="Page limit (1-100, default 20)"),
    offset: int = Query(0, ge=0, description="Page offset (>= 0, default 0)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SupplierListResponse:
    """List suppliers belonging to the organization with optional search, filters, and pagination."""
    get_membership_or_403(organization_id, current_user, db)

    query = db.query(Supplier).filter_by(organization_id=organization_id)

    # Search (q) across company_name, contact_name, email (case-insensitive)
    if q is not None and q.strip():
        search_pattern = f"%{q.strip()}%"
        query = query.filter(
            or_(
                Supplier.company_name.ilike(search_pattern),
                Supplier.contact_name.ilike(search_pattern),
                Supplier.email.ilike(search_pattern),
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
        query = query.filter(Supplier.country == cleaned_country)

    # Verification status filter (exact, validated against allowed statuses)
    if verification_status is not None:
        cleaned_status = verification_status.strip().upper()
        if cleaned_status not in VALID_VERIFICATION_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid verification status '{verification_status}'. Allowed values are: {', '.join(sorted(VALID_VERIFICATION_STATUSES))}",
            )
        query = query.filter(Supplier.verification_status == cleaned_status)

    # Supplier type filter (exact)
    if supplier_type is not None and supplier_type.strip():
        query = query.filter(Supplier.supplier_type == supplier_type.strip())

    total = query.count()
    items = (
        query.order_by(Supplier.created_at.desc(), Supplier.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return SupplierListResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post(
    "",
    response_model=SupplierRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new supplier",
)
def create_supplier(
    organization_id: uuid.UUID,
    body: SupplierCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SupplierRead:
    """Create a new supplier under the specified organization."""
    require_organization_membership(organization_id, current_user, db)

    supplier = Supplier(
        organization_id=organization_id,
        **body.model_dump(),
    )
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier


@router.get(
    "/{supplier_id}",
    response_model=SupplierRead,
    summary="Get supplier details by ID",
)
def get_supplier(
    organization_id: uuid.UUID,
    supplier_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SupplierRead:
    """Retrieve supplier details by ID. Scoped strictly to the caller's organization."""
    get_membership_or_403(organization_id, current_user, db)

    supplier = (
        db.query(Supplier)
        .filter_by(id=supplier_id, organization_id=organization_id)
        .first()
    )
    if supplier is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found.",
        )
    return supplier


@router.patch(
    "/{supplier_id}",
    response_model=SupplierRead,
    summary="Update a supplier by ID",
)
def update_supplier(
    organization_id: uuid.UUID,
    supplier_id: uuid.UUID,
    body: SupplierUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SupplierRead:
    """Update fields on an existing supplier. Scoped strictly to the caller's organization."""
    require_organization_membership(organization_id, current_user, db)

    supplier = (
        db.query(Supplier)
        .filter_by(id=supplier_id, organization_id=organization_id)
        .first()
    )
    if supplier is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found.",
        )

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(supplier, field, value)

    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier


@router.delete(
    "/{supplier_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a supplier by ID",
)
def delete_supplier(
    organization_id: uuid.UUID,
    supplier_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Delete a supplier record by ID. Scoped strictly to the caller's organization."""
    require_organization_membership(organization_id, current_user, db)

    supplier = (
        db.query(Supplier)
        .filter_by(id=supplier_id, organization_id=organization_id)
        .first()
    )
    if supplier is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found.",
        )

    db.delete(supplier)
    db.commit()
