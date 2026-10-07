"""
CRM Contact routes — /api/v1/organizations/{organization_id}/...

Authoritative source: docs/DATA_MODEL.md section 31 & docs/TASKS.md T1.15.
Endpoints:
  POST   /api/v1/organizations/{organization_id}/buyers/{buyer_id}/contacts
  GET    /api/v1/organizations/{organization_id}/buyers/{buyer_id}/contacts
  POST   /api/v1/organizations/{organization_id}/suppliers/{supplier_id}/contacts
  GET    /api/v1/organizations/{organization_id}/suppliers/{supplier_id}/contacts
  PATCH  /api/v1/organizations/{organization_id}/contacts/{contact_id}
  DELETE /api/v1/organizations/{organization_id}/contacts/{contact_id}
"""
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth.dependencies import get_current_user
from app.core.auth.permissions import (
    get_membership_or_403,
    require_organization_membership,
)
from app.db.session import get_db
from app.models.buyer import Buyer
from app.models.supplier import Supplier
from app.models.contact import CRMContact
from app.models.user import User
from app.schemas.contact import ContactCreate, ContactRead, ContactUpdate

router = APIRouter(
    prefix="/organizations/{organization_id}",
    tags=["Contacts"],
)


# ---------------------------------------------------------------------------
# Buyer Contacts
# ---------------------------------------------------------------------------


@router.post(
    "/buyers/{buyer_id}/contacts",
    response_model=ContactRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new contact for a buyer",
)
def create_buyer_contact(
    organization_id: uuid.UUID,
    buyer_id: uuid.UUID,
    body: ContactCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ContactRead:
    """Create a new contact associated with a buyer under the specified organization."""
    require_organization_membership(organization_id, current_user, db)

    # Verify buyer exists and belongs to the specified organization (orphan prevention)
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

    contact = CRMContact(
        organization_id=organization_id,
        buyer_id=buyer_id,
        supplier_id=None,
        **body.model_dump(),
    )
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


@router.get(
    "/buyers/{buyer_id}/contacts",
    response_model=List[ContactRead],
    summary="List contacts for a buyer",
)
def list_buyer_contacts(
    organization_id: uuid.UUID,
    buyer_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[ContactRead]:
    """Retrieve all contacts associated with a buyer under the specified organization."""
    get_membership_or_403(organization_id, current_user, db)

    # Verify buyer exists and belongs to the specified organization
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

    contacts = (
        db.query(CRMContact)
        .filter_by(organization_id=organization_id, buyer_id=buyer_id)
        .order_by(CRMContact.created_at.desc(), CRMContact.id.desc())
        .all()
    )
    return contacts


# ---------------------------------------------------------------------------
# Supplier Contacts
# ---------------------------------------------------------------------------


@router.post(
    "/suppliers/{supplier_id}/contacts",
    response_model=ContactRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new contact for a supplier",
)
def create_supplier_contact(
    organization_id: uuid.UUID,
    supplier_id: uuid.UUID,
    body: ContactCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ContactRead:
    """Create a new contact associated with a supplier under the specified organization."""
    require_organization_membership(organization_id, current_user, db)

    # Verify supplier exists and belongs to the specified organization (orphan prevention)
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

    contact = CRMContact(
        organization_id=organization_id,
        buyer_id=None,
        supplier_id=supplier_id,
        **body.model_dump(),
    )
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


@router.get(
    "/suppliers/{supplier_id}/contacts",
    response_model=List[ContactRead],
    summary="List contacts for a supplier",
)
def list_supplier_contacts(
    organization_id: uuid.UUID,
    supplier_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[ContactRead]:
    """Retrieve all contacts associated with a supplier under the specified organization."""
    get_membership_or_403(organization_id, current_user, db)

    # Verify supplier exists and belongs to the specified organization
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

    contacts = (
        db.query(CRMContact)
        .filter_by(organization_id=organization_id, supplier_id=supplier_id)
        .order_by(CRMContact.created_at.desc(), CRMContact.id.desc())
        .all()
    )
    return contacts


# ---------------------------------------------------------------------------
# Contact Mutation (PATCH / DELETE)
# ---------------------------------------------------------------------------


@router.patch(
    "/contacts/{contact_id}",
    response_model=ContactRead,
    summary="Update a contact by ID",
)
def update_contact(
    organization_id: uuid.UUID,
    contact_id: uuid.UUID,
    body: ContactUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ContactRead:
    """Update mutable fields on an existing CRM contact. Scoped strictly to the caller's organization."""
    require_organization_membership(organization_id, current_user, db)

    contact = (
        db.query(CRMContact)
        .filter_by(id=contact_id, organization_id=organization_id)
        .first()
    )
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found.",
        )

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(contact, field, value)

    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


@router.delete(
    "/contacts/{contact_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a contact by ID",
)
def delete_contact(
    organization_id: uuid.UUID,
    contact_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Delete a CRM contact by ID. Scoped strictly to the caller's organization."""
    require_organization_membership(organization_id, current_user, db)

    contact = (
        db.query(CRMContact)
        .filter_by(id=contact_id, organization_id=organization_id)
        .first()
    )
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found.",
        )

    db.delete(contact)
    db.commit()
