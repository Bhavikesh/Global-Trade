"""
Buyer CRUD routes — /api/v1/organizations/{organization_id}/buyers

Authoritative source: docs/DATA_MODEL.md section 11 & docs/TASKS.md T1.13.
Endpoints:
  POST   /api/v1/organizations/{organization_id}/buyers
  GET    /api/v1/organizations/{organization_id}/buyers/{buyer_id}
  PATCH  /api/v1/organizations/{organization_id}/buyers/{buyer_id}
  DELETE /api/v1/organizations/{organization_id}/buyers/{buyer_id}
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
from app.models.buyer import Buyer
from app.models.user import User
from app.schemas.buyer import BuyerCreate, BuyerRead, BuyerUpdate

router = APIRouter(
    prefix="/organizations/{organization_id}/buyers",
    tags=["Buyers"],
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
