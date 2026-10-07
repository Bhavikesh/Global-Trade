"""
Supplier CRUD routes — /api/v1/organizations/{organization_id}/suppliers

Authoritative source: docs/DATA_MODEL.md section 12 & docs/TASKS.md T1.15, T1.16.
Endpoints:
  POST   /api/v1/organizations/{organization_id}/suppliers
  GET    /api/v1/organizations/{organization_id}/suppliers/{supplier_id}
  PATCH  /api/v1/organizations/{organization_id}/suppliers/{supplier_id}
  DELETE /api/v1/organizations/{organization_id}/suppliers/{supplier_id}
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth.dependencies import get_current_user
from app.core.auth.permissions import (
    get_membership_or_403,
    require_organization_membership,
)
from app.db.session import get_db
from app.models.supplier import Supplier
from app.models.user import User
from app.schemas.supplier import SupplierCreate, SupplierRead, SupplierUpdate

router = APIRouter(
    prefix="/organizations/{organization_id}/suppliers",
    tags=["Suppliers"],
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
