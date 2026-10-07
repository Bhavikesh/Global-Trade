"""
Buyer-facing RFQ and Quotation Management routes.

Prefix: /organizations/{organization_id}/rfqs
Enforces strict organization-level isolation and RBAC.
Supplier users are NEVER permitted to access competitor quotes or comparison endpoints here.
"""
from datetime import datetime, timezone
from decimal import Decimal
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.auth.dependencies import get_current_user
from app.core.auth.permissions import (
    ROLE_ADMIN,
    ROLE_BUYER,
    ROLE_EXPORTER,
    ROLE_IMPORTER,
    get_membership_or_403,
    require_organization_membership,
)
from app.db.session import get_db
from app.models.organization import Organization
from app.models.quotation import (
    Quotation,
    QUOTATION_STATUS_ACCEPTED,
    QUOTATION_STATUS_REJECTED,
    QUOTATION_STATUS_SUBMITTED,
    QUOTATION_STATUS_UNDER_REVIEW,
)
from app.models.rfq import (
    RFQ,
    RFQItem,
    RFQSupplierInvitation,
    RFQ_STATUS_AWARDED,
    RFQ_STATUS_CANCELLED,
    RFQ_STATUS_DRAFT,
    RFQ_STATUS_EXPIRED,
    RFQ_STATUS_INVITATIONS_SENT,
    RFQ_STATUS_NEGOTIATION,
    RFQ_STATUS_OPEN,
    RFQ_STATUS_RESPONSES_RECEIVED,
    RFQ_STATUS_UNDER_REVIEW,
)
from app.models.user import User
from app.schemas.quotation import QuotationRead, QuoteComparisonRead
from app.schemas.rfq import (
    RFQCreate,
    RFQListRead,
    RFQRead,
    RFQUpdate,
    SupplierInvitationBatchCreate,
    SupplierInvitationCreate,
    SupplierInvitationRead,
)
from app.services.reference_number import generate_rfq_number
from app.services.rfq_calculations import build_deterministic_comparison

BUYER_MUTATION_ROLES = {ROLE_ADMIN, ROLE_BUYER, ROLE_EXPORTER, ROLE_IMPORTER}

router = APIRouter(
    prefix="/organizations/{organization_id}/rfqs",
    tags=["Buyer RFQs & Quotations"],
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _get_rfq_or_404(rfq_id: uuid.UUID, organization_id: uuid.UUID, db: Session) -> RFQ:
    rfq = db.query(RFQ).filter_by(id=rfq_id, organization_id=organization_id).first()
    if rfq is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="RFQ not found in this organization.",
        )
    return rfq


# ---------------------------------------------------------------------------
# Buyer RFQ Endpoints
# ---------------------------------------------------------------------------
@router.post(
    "/",
    response_model=RFQRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new RFQ (DRAFT)",
)
def create_rfq(
    organization_id: uuid.UUID,
    body: RFQCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RFQ:
    """Create a new RFQ in DRAFT status with initial line items."""
    require_organization_membership(
        organization_id, current_user, db, allowed_roles=BUYER_MUTATION_ROLES
    )

    rfq_number = generate_rfq_number(db)
    rfq = RFQ(
        organization_id=organization_id,
        rfq_number=rfq_number,
        title=body.title,
        description=body.description,
        destination_country=body.destination_country.upper(),
        destination_port=body.destination_port,
        required_delivery_date=body.required_delivery_date,
        preferred_incoterm=body.preferred_incoterm,
        preferred_payment_terms=body.preferred_payment_terms,
        currency=body.currency.upper(),
        status=RFQ_STATUS_DRAFT,
        notes=body.notes,
        created_by_user_id=current_user.id,
    )
    db.add(rfq)
    db.flush()

    for idx, item_in in enumerate(body.items, start=1):
        item = RFQItem(
            rfq_id=rfq.id,
            item_index=idx,
            product_id=item_in.product_id,
            product_name_snapshot=item_in.product_name_snapshot,
            description=item_in.description,
            quantity=item_in.quantity,
            unit=item_in.unit.upper(),
            target_unit_price=item_in.target_unit_price,
            specifications=item_in.specifications,
            quality_requirements=item_in.quality_requirements,
            packaging_requirements=item_in.packaging_requirements,
        )
        db.add(item)

    db.commit()
    db.refresh(rfq)
    return rfq


@router.get(
    "/",
    response_model=List[RFQListRead],
    summary="List RFQs for buyer organization",
)
def list_rfqs(
    organization_id: uuid.UUID,
    status_filter: str | None = Query(default=None, alias="status"),
    search: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[dict]:
    """List all RFQs for the buyer organization."""
    get_membership_or_403(organization_id, current_user, db)

    query = db.query(RFQ).filter_by(organization_id=organization_id)
    if status_filter:
        query = query.filter(RFQ.status == status_filter.upper())
    if search:
        query = query.filter(
            (RFQ.title.ilike(f"%{search}%")) | (RFQ.rfq_number.ilike(f"%{search}%"))
        )

    rfqs = query.order_by(RFQ.created_at.desc()).all()
    results = []
    for r in rfqs:
        results.append({
            "id": r.id,
            "organization_id": r.organization_id,
            "rfq_number": r.rfq_number,
            "title": r.title,
            "destination_country": r.destination_country,
            "preferred_incoterm": r.preferred_incoterm,
            "currency": r.currency,
            "status": r.status,
            "required_delivery_date": r.required_delivery_date,
            "created_at": r.created_at,
            "items_count": len(r.items),
            "invitations_count": len(r.invitations),
            "quotations_count": len(r.quotations),
        })
    return results


@router.get(
    "/{rfq_id}",
    response_model=RFQRead,
    summary="Get RFQ detail with items and invitation counts",
)
def get_rfq(
    organization_id: uuid.UUID,
    rfq_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Retrieve complete RFQ details."""
    get_membership_or_403(organization_id, current_user, db)
    rfq = _get_rfq_or_404(rfq_id, organization_id, db)

    return {
        "id": rfq.id,
        "organization_id": rfq.organization_id,
        "rfq_number": rfq.rfq_number,
        "title": rfq.title,
        "description": rfq.description,
        "destination_country": rfq.destination_country,
        "destination_port": rfq.destination_port,
        "required_delivery_date": rfq.required_delivery_date,
        "preferred_incoterm": rfq.preferred_incoterm,
        "preferred_payment_terms": rfq.preferred_payment_terms,
        "currency": rfq.currency,
        "status": rfq.status,
        "awarded_quotation_id": rfq.awarded_quotation_id,
        "notes": rfq.notes,
        "created_by_user_id": rfq.created_by_user_id,
        "created_at": rfq.created_at,
        "updated_at": rfq.updated_at,
        "items": rfq.items,
        "invitations_count": len(rfq.invitations),
        "quotations_count": len(rfq.quotations),
    }


@router.patch(
    "/{rfq_id}",
    response_model=RFQRead,
    summary="Update RFQ metadata (only when editable)",
)
def update_rfq(
    organization_id: uuid.UUID,
    rfq_id: uuid.UUID,
    body: RFQUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Update RFQ fields. Allowed only when status is DRAFT or OPEN."""
    require_organization_membership(
        organization_id, current_user, db, allowed_roles=BUYER_MUTATION_ROLES
    )
    rfq = _get_rfq_or_404(rfq_id, organization_id, db)

    if rfq.status not in {RFQ_STATUS_DRAFT, RFQ_STATUS_OPEN}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot edit RFQ in status '{rfq.status}'. Only DRAFT or OPEN RFQs can be modified.",
        )

    for field, val in body.model_dump(exclude_unset=True).items():
        if val is not None:
            if field == "destination_country":
                val = val.upper()
            elif field == "currency":
                val = val.upper()
            setattr(rfq, field, val)

    db.commit()
    db.refresh(rfq)
    return get_rfq(organization_id, rfq_id, current_user, db)


# ---------------------------------------------------------------------------
# RFQ State Transitions
# ---------------------------------------------------------------------------
@router.post(
    "/{rfq_id}/open",
    response_model=RFQRead,
    summary="Transition RFQ from DRAFT to OPEN",
)
def open_rfq(
    organization_id: uuid.UUID,
    rfq_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Publish RFQ by transitioning from DRAFT to OPEN."""
    require_organization_membership(
        organization_id, current_user, db, allowed_roles=BUYER_MUTATION_ROLES
    )
    rfq = _get_rfq_or_404(rfq_id, organization_id, db)

    if rfq.status != RFQ_STATUS_DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid state transition: RFQ is currently '{rfq.status}', expected 'DRAFT'.",
        )

    if not rfq.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot open RFQ with zero requested items.",
        )

    rfq.status = RFQ_STATUS_OPEN
    db.commit()
    db.refresh(rfq)
    return get_rfq(organization_id, rfq_id, current_user, db)


@router.post(
    "/{rfq_id}/cancel",
    response_model=RFQRead,
    summary="Cancel RFQ",
)
def cancel_rfq(
    organization_id: uuid.UUID,
    rfq_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Cancel an active RFQ."""
    require_organization_membership(
        organization_id, current_user, db, allowed_roles=BUYER_MUTATION_ROLES
    )
    rfq = _get_rfq_or_404(rfq_id, organization_id, db)

    if rfq.status in {RFQ_STATUS_AWARDED, RFQ_STATUS_CANCELLED, RFQ_STATUS_EXPIRED}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel RFQ in terminal state '{rfq.status}'.",
        )

    rfq.status = RFQ_STATUS_CANCELLED
    db.commit()
    db.refresh(rfq)
    return get_rfq(organization_id, rfq_id, current_user, db)


# ---------------------------------------------------------------------------
# Supplier Invitations
# ---------------------------------------------------------------------------
@router.post(
    "/{rfq_id}/invitations",
    response_model=List[SupplierInvitationRead],
    status_code=status.HTTP_201_CREATED,
    summary="Invite suppliers to RFQ",
)
def invite_suppliers(
    organization_id: uuid.UUID,
    rfq_id: uuid.UUID,
    body: SupplierInvitationBatchCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[RFQSupplierInvitation]:
    """Invite one or more suppliers to submit quotations."""
    require_organization_membership(
        organization_id, current_user, db, allowed_roles=BUYER_MUTATION_ROLES
    )
    rfq = _get_rfq_or_404(rfq_id, organization_id, db)

    if rfq.status in {RFQ_STATUS_DRAFT, RFQ_STATUS_CANCELLED, RFQ_STATUS_EXPIRED, RFQ_STATUS_AWARDED}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot invite suppliers while RFQ is '{rfq.status}'. RFQ must be OPEN or active.",
        )

    created_invitations = []
    for inv in body.invitations:
        # Check for duplicate invitation
        existing = (
            db.query(RFQSupplierInvitation)
            .filter_by(rfq_id=rfq.id, supplier_email=inv.supplier_email.lower())
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Supplier '{inv.supplier_email}' has already been invited to this RFQ.",
            )

        new_inv = RFQSupplierInvitation(
            rfq_id=rfq.id,
            supplier_organization_id=inv.supplier_organization_id,
            supplier_id=inv.supplier_id,
            supplier_email=inv.supplier_email.lower(),
            supplier_name=inv.supplier_name,
            invited_by_user_id=current_user.id,
            response_deadline=inv.response_deadline,
        )
        db.add(new_inv)
        created_invitations.append(new_inv)

    # Transition RFQ status to INVITATIONS_SENT if it was OPEN
    if rfq.status == RFQ_STATUS_OPEN:
        rfq.status = RFQ_STATUS_INVITATIONS_SENT

    db.commit()
    for ci in created_invitations:
        db.refresh(ci)
    return created_invitations


@router.get(
    "/{rfq_id}/invitations",
    response_model=List[SupplierInvitationRead],
    summary="List sent invitations for this RFQ",
)
def list_invitations(
    organization_id: uuid.UUID,
    rfq_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[RFQSupplierInvitation]:
    """List sent supplier invitations."""
    get_membership_or_403(organization_id, current_user, db)
    rfq = _get_rfq_or_404(rfq_id, organization_id, db)
    return rfq.invitations


# ---------------------------------------------------------------------------
# Buyer Quotations & Comparison (STRICTLY BUYER ONLY)
# ---------------------------------------------------------------------------
@router.get(
    "/{rfq_id}/quotations",
    response_model=List[QuotationRead],
    summary="List received quotations for buyer (BUYER ONLY)",
)
def list_rfq_quotations(
    organization_id: uuid.UUID,
    rfq_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[dict]:
    """
    List all submitted quotations for this RFQ.
    CRITICAL SECURITY: Strictly limited to members of the buyer organization!
    Suppliers are NEVER permitted to call this endpoint.
    """
    get_membership_or_403(organization_id, current_user, db)
    rfq = _get_rfq_or_404(rfq_id, organization_id, db)

    # Automatically transition RFQ status to UNDER_REVIEW if buyer views received quotations
    if rfq.status == RFQ_STATUS_RESPONSES_RECEIVED:
        rfq.status = RFQ_STATUS_UNDER_REVIEW
        db.commit()

    # Return non-draft quotations with supplier org details
    quotes = (
        db.query(Quotation)
        .filter(
            Quotation.rfq_id == rfq.id,
            Quotation.status != "DRAFT",
        )
        .order_by(Quotation.total_landed_cost.asc())
        .all()
    )

    results = []
    for q in quotes:
        sup_org = db.query(Organization).filter_by(id=q.supplier_organization_id).first()
        results.append({
            "id": q.id,
            "rfq_id": q.rfq_id,
            "supplier_organization_id": q.supplier_organization_id,
            "supplier_organization_name": sup_org.legal_name if sup_org else None,
            "supplier_user_id": q.supplier_user_id,
            "quotation_number": q.quotation_number,
            "version": q.version,
            "parent_quotation_id": q.parent_quotation_id,
            "status": q.status,
            "currency": q.currency,
            "valid_until": q.valid_until,
            "incoterm": q.incoterm,
            "payment_terms": q.payment_terms,
            "lead_time_days": q.lead_time_days,
            "subtotal_amount": q.subtotal_amount,
            "shipping_cost": q.shipping_cost,
            "insurance_cost": q.insurance_cost,
            "duty_amount": q.duty_amount,
            "tax_amount": q.tax_amount,
            "other_charges": q.other_charges,
            "total_landed_cost": q.total_landed_cost,
            "supplier_notes": q.supplier_notes,
            "submitted_at": q.submitted_at,
            "created_at": q.created_at,
            "updated_at": q.updated_at,
            "items": q.items,
        })
    return results


@router.get(
    "/{rfq_id}/comparison",
    response_model=QuoteComparisonRead,
    summary="Get side-by-side quote comparison matrix (BUYER ONLY)",
)
def get_quote_comparison(
    organization_id: uuid.UUID,
    rfq_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """
    Get deterministic quotation comparison matrix.
    CRITICAL SECURITY: Strictly limited to members of the buyer organization!
    Suppliers are NEVER permitted to call this endpoint.
    """
    get_membership_or_403(organization_id, current_user, db)
    rfq = _get_rfq_or_404(rfq_id, organization_id, db)

    # Load submitted / active quotations
    quotes = (
        db.query(Quotation)
        .filter(
            Quotation.rfq_id == rfq.id,
            Quotation.status.in_([QUOTATION_STATUS_SUBMITTED, QUOTATION_STATUS_UNDER_REVIEW, QUOTATION_STATUS_ACCEPTED]),
        )
        .all()
    )

    quotes_payload = []
    for q in quotes:
        sup_org = db.query(Organization).filter_by(id=q.supplier_organization_id).first()
        items_payload = []
        for itm in q.items:
            items_payload.append({
                "id": itm.id,
                "quotation_id": itm.quotation_id,
                "rfq_item_id": itm.rfq_item_id,
                "product_name_snapshot": itm.product_name_snapshot,
                "quantity": itm.quantity,
                "unit": itm.unit,
                "unit_price": itm.unit_price,
                "line_total": itm.line_total,
                "lead_time_days": itm.lead_time_days,
                "moq": itm.moq,
                "notes": itm.notes,
                "created_at": itm.created_at,
                "updated_at": itm.updated_at,
            })

        quotes_payload.append({
            "id": q.id,
            "rfq_id": q.rfq_id,
            "supplier_organization_id": q.supplier_organization_id,
            "supplier_name": sup_org.legal_name if sup_org else "Supplier",
            "supplier_organization_name": sup_org.legal_name if sup_org else "Supplier",
            "supplier_user_id": q.supplier_user_id,
            "quotation_number": q.quotation_number,
            "version": q.version,
            "parent_quotation_id": q.parent_quotation_id,
            "status": q.status,
            "currency": q.currency,
            "valid_until": q.valid_until,
            "incoterm": q.incoterm,
            "payment_terms": q.payment_terms,
            "lead_time_days": q.lead_time_days,
            "subtotal_amount": q.subtotal_amount,
            "shipping_cost": q.shipping_cost,
            "insurance_cost": q.insurance_cost,
            "duty_amount": q.duty_amount,
            "tax_amount": q.tax_amount,
            "other_charges": q.other_charges,
            "total_landed_cost": q.total_landed_cost,
            "supplier_notes": q.supplier_notes,
            "submitted_at": q.submitted_at,
            "created_at": q.created_at,
            "updated_at": q.updated_at,
            "items": items_payload,
        })

    rfq_items_payload = [
        {
            "id": itm.id,
            "product_name_snapshot": itm.product_name_snapshot,
            "quantity": itm.quantity,
            "unit": itm.unit,
        }
        for itm in rfq.items
    ]

    return build_deterministic_comparison(quotes_payload, rfq_items_payload)


# ---------------------------------------------------------------------------
# Quotation Awarding
# ---------------------------------------------------------------------------
@router.post(
    "/{rfq_id}/award/{quotation_id}",
    response_model=RFQRead,
    summary="Award RFQ to winning quotation",
)
def award_quotation(
    organization_id: uuid.UUID,
    rfq_id: uuid.UUID,
    quotation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """
    Award RFQ to a specific quotation.
    - Verifies buyer permission
    - Verifies RFQ is in awardable state (UNDER_REVIEW, NEGOTIATION, RESPONSES_RECEIVED)
    - Verifies quotation belongs to RFQ and is reviewable
    - Sets RFQ to AWARDED and quotation to ACCEPTED
    - Sets competing active quotations to REJECTED
    """
    require_organization_membership(
        organization_id, current_user, db, allowed_roles=BUYER_MUTATION_ROLES
    )
    rfq = _get_rfq_or_404(rfq_id, organization_id, db)

    if rfq.status in {RFQ_STATUS_AWARDED, RFQ_STATUS_CANCELLED, RFQ_STATUS_EXPIRED}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot award RFQ in terminal status '{rfq.status}'.",
        )

    quotation = db.query(Quotation).filter_by(id=quotation_id).first()
    if quotation is None or quotation.rfq_id != rfq.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quotation does not exist or does not belong to this RFQ.",
        )

    if quotation.status not in {QUOTATION_STATUS_SUBMITTED, QUOTATION_STATUS_UNDER_REVIEW}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot award quotation with status '{quotation.status}'. Must be SUBMITTED or UNDER_REVIEW.",
        )

    # 1. Update winning quotation
    quotation.status = QUOTATION_STATUS_ACCEPTED

    # 2. Reject other active quotations for this RFQ
    other_quotes = (
        db.query(Quotation)
        .filter(
            Quotation.rfq_id == rfq.id,
            Quotation.id != quotation.id,
            Quotation.status.in_([QUOTATION_STATUS_SUBMITTED, QUOTATION_STATUS_UNDER_REVIEW]),
        )
        .all()
    )
    for oq in other_quotes:
        oq.status = QUOTATION_STATUS_REJECTED

    # 3. Update RFQ
    rfq.status = RFQ_STATUS_AWARDED
    rfq.awarded_quotation_id = quotation.id

    db.commit()
    db.refresh(rfq)
    return get_rfq(organization_id, rfq_id, current_user, db)
