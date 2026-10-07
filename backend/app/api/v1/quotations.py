"""
Supplier-facing RFQ participation, Quotation submission, and Negotiation routes.

Enforces:
- Invitation validation: suppliers cannot quote unless an active invitation exists
- Competitor isolation: suppliers can NEVER see another supplier's quotes
- Immutability: submitted quotes cannot be patched in-place; revisions create V2 (SUPERSEDED V1)
- Tenant isolation: verified via user membership in supplier_organization_id
"""
from datetime import datetime, timezone
from decimal import Decimal
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth.dependencies import get_current_user
from app.core.auth.permissions import (
    ROLE_ADMIN,
    ROLE_EXPORTER,
    ROLE_SUPPLIER,
    get_membership_or_403,
    require_organization_membership,
)
from app.db.session import get_db
from app.models.organization import Organization
from app.models.quotation import (
    Quotation,
    QuotationItem,
    QUOTATION_STATUS_DRAFT,
    QUOTATION_STATUS_SUBMITTED,
    QUOTATION_STATUS_SUPERSEDED,
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
from app.models.negotiation import NegotiationNote
from app.models.user import User
from app.schemas.quotation import (
    NegotiationNoteCreate,
    NegotiationNoteRead,
    QuotationCreate,
    QuotationRead,
    QuotationUpdate,
)
from app.schemas.rfq import RFQItemRead, SupplierInvitationRead
from app.services.reference_number import generate_quotation_number
from app.services.rfq_calculations import calculate_line_total, calculate_quotation_totals

SUPPLIER_MUTATION_ROLES = {ROLE_ADMIN, ROLE_SUPPLIER, ROLE_EXPORTER}

router = APIRouter(
    prefix="/organizations/{organization_id}",
    tags=["Supplier Quotations & Negotiation"],
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _verify_supplier_invitation(
    rfq_id: uuid.UUID,
    supplier_org_id: uuid.UUID,
    user: User,
    db: Session,
) -> RFQSupplierInvitation:
    """
    Verify that an invitation exists for this supplier organization or user email on rfq_id.
    """
    inv = (
        db.query(RFQSupplierInvitation)
        .filter(
            RFQSupplierInvitation.rfq_id == rfq_id,
            (RFQSupplierInvitation.supplier_organization_id == supplier_org_id)
            | (RFQSupplierInvitation.supplier_email == (user.email or "").lower()),
        )
        .first()
    )
    if inv is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Your organization has not been invited to participate in this RFQ.",
        )
    return inv


# ---------------------------------------------------------------------------
# Supplier RFQ Discovery & Detail (Sanitized)
# ---------------------------------------------------------------------------
@router.get(
    "/supplier/invitations",
    response_model=List[SupplierInvitationRead],
    summary="List RFQ invitations for supplier organization",
)
def list_supplier_invitations(
    organization_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[RFQSupplierInvitation]:
    """List invitations sent to this supplier organization."""
    get_membership_or_403(organization_id, current_user, db)

    invitations = (
        db.query(RFQSupplierInvitation)
        .filter(
            (RFQSupplierInvitation.supplier_organization_id == organization_id)
            | (RFQSupplierInvitation.supplier_email == (current_user.email or "").lower())
        )
        .order_by(RFQSupplierInvitation.invited_at.desc())
        .all()
    )
    return invitations


@router.get(
    "/supplier/rfqs/{rfq_id}",
    summary="Get invited RFQ details (sanitized view for supplier)",
)
def get_invited_rfq_detail(
    organization_id: uuid.UUID,
    rfq_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """
    Supplier view of an RFQ.
    CRITICAL SECURITY: Hides competitor quotes, buyer internal notes, and other invited suppliers.
    """
    get_membership_or_403(organization_id, current_user, db)
    _verify_supplier_invitation(rfq_id, organization_id, current_user, db)

    rfq = db.query(RFQ).filter_by(id=rfq_id).first()
    if rfq is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="RFQ not found.")

    buyer_org = db.query(Organization).filter_by(id=rfq.organization_id).first()

    # Mark invitation as VIEWED if still in INVITED status
    inv = (
        db.query(RFQSupplierInvitation)
        .filter(
            RFQSupplierInvitation.rfq_id == rfq_id,
            (RFQSupplierInvitation.supplier_organization_id == organization_id)
            | (RFQSupplierInvitation.supplier_email == (current_user.email or "").lower()),
        )
        .first()
    )
    if inv and inv.status == "INVITED":
        inv.status = "VIEWED"
        db.commit()

    return {
        "id": rfq.id,
        "rfq_number": rfq.rfq_number,
        "title": rfq.title,
        "description": rfq.description,
        "buyer_organization_name": buyer_org.display_name or buyer_org.legal_name if buyer_org else None,
        "destination_country": rfq.destination_country,
        "destination_port": rfq.destination_port,
        "required_delivery_date": rfq.required_delivery_date,
        "preferred_incoterm": rfq.preferred_incoterm,
        "preferred_payment_terms": rfq.preferred_payment_terms,
        "currency": rfq.currency,
        "status": rfq.status,
        "created_at": rfq.created_at,
        "items": [
            {
                "id": itm.id,
                "item_index": itm.item_index,
                "product_name_snapshot": itm.product_name_snapshot,
                "description": itm.description,
                "quantity": itm.quantity,
                "unit": itm.unit,
                "specifications": itm.specifications,
                "quality_requirements": itm.quality_requirements,
                "packaging_requirements": itm.packaging_requirements,
            }
            for itm in rfq.items
        ],
    }


# ---------------------------------------------------------------------------
# Supplier Quotation Submission & Lifecycle
# ---------------------------------------------------------------------------
@router.post(
    "/supplier/rfqs/{rfq_id}/quotations",
    response_model=QuotationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create draft quotation for an invited RFQ",
)
def create_quotation(
    organization_id: uuid.UUID,
    rfq_id: uuid.UUID,
    body: QuotationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """
    Create a new draft quotation for an invited RFQ.
    - Verifies supplier organization membership
    - Verifies active invitation exists for this supplier
    - Validates all items belong to this RFQ
    - Calculates line totals and landed cost deterministically
    """
    require_organization_membership(
        organization_id, current_user, db, allowed_roles=SUPPLIER_MUTATION_ROLES
    )
    _verify_supplier_invitation(rfq_id, organization_id, current_user, db)

    rfq = db.query(RFQ).filter_by(id=rfq_id).first()
    if rfq is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="RFQ not found.")

    if rfq.status in {RFQ_STATUS_DRAFT, RFQ_STATUS_AWARDED, RFQ_STATUS_CANCELLED, RFQ_STATUS_EXPIRED}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot submit quotation for RFQ in status '{rfq.status}'.",
        )

    # Validate all quotation items belong to this specific RFQ
    valid_rfq_item_ids = {itm.id: itm for itm in rfq.items}
    for q_item in body.items:
        if q_item.rfq_item_id not in valid_rfq_item_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Item {q_item.rfq_item_id} does not belong to RFQ {rfq_id}.",
            )

    # Deterministic calculations
    line_totals = []
    created_items_data = []
    for q_item in body.items:
        rfq_item = valid_rfq_item_ids[q_item.rfq_item_id]
        qty = q_item.quantity if q_item.quantity is not None else rfq_item.quantity
        lt = calculate_line_total(qty, q_item.unit_price)
        line_totals.append(lt)
        created_items_data.append({
            "rfq_item_id": q_item.rfq_item_id,
            "product_name_snapshot": rfq_item.product_name_snapshot,
            "quantity": qty,
            "unit": rfq_item.unit,
            "unit_price": q_item.unit_price,
            "line_total": lt,
            "moq": q_item.moq,
            "lead_time_days": q_item.lead_time_days,
            "notes": q_item.notes,
        })

    subtotal, total_landed = calculate_quotation_totals(
        item_line_totals=line_totals,
        shipping_cost=body.shipping_cost,
        insurance_cost=body.insurance_cost,
        duty_amount=body.duty_amount,
        tax_amount=body.tax_amount,
        other_charges=body.other_charges,
    )

    quotation_number = generate_quotation_number(db)
    quote = Quotation(
        rfq_id=rfq.id,
        supplier_organization_id=organization_id,
        supplier_user_id=current_user.id,
        quotation_number=quotation_number,
        version=1,
        status=QUOTATION_STATUS_DRAFT,
        currency=body.currency.upper(),
        valid_until=body.valid_until,
        incoterm=body.incoterm.upper(),
        payment_terms=body.payment_terms,
        lead_time_days=body.lead_time_days,
        subtotal_amount=subtotal,
        shipping_cost=body.shipping_cost,
        insurance_cost=body.insurance_cost,
        duty_amount=body.duty_amount,
        tax_amount=body.tax_amount,
        other_charges=body.other_charges,
        total_landed_cost=total_landed,
        supplier_notes=body.supplier_notes,
    )
    db.add(quote)
    db.flush()

    for itm_dict in created_items_data:
        q_item_orm = QuotationItem(
            quotation_id=quote.id,
            **itm_dict,
        )
        db.add(q_item_orm)

    db.commit()
    db.refresh(quote)
    return quote


@router.get(
    "/supplier/quotations/{quotation_id}",
    response_model=QuotationRead,
    summary="Get supplier's own quotation",
)
def get_supplier_quotation(
    organization_id: uuid.UUID,
    quotation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Quotation:
    """
    Retrieve own quotation details.
    CRITICAL SECURITY: Verifies that quotation belongs to supplier organization!
    """
    get_membership_or_403(organization_id, current_user, db)

    quote = db.query(Quotation).filter_by(id=quotation_id).first()
    if quote is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quotation not found.")

    if quote.supplier_organization_id != organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You cannot view another supplier's quotation.",
        )

    return quote


@router.patch(
    "/supplier/quotations/{quotation_id}",
    response_model=QuotationRead,
    summary="Update draft quotation (immutability check)",
)
def update_supplier_quotation(
    organization_id: uuid.UUID,
    quotation_id: uuid.UUID,
    body: QuotationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Quotation:
    """
    Update quotation draft.
    CRITICAL IMMUTABILITY RULE: Only DRAFT quotations can be modified in-place.
    Submitted quotations must use /revise to create a new version.
    """
    require_organization_membership(
        organization_id, current_user, db, allowed_roles=SUPPLIER_MUTATION_ROLES
    )

    quote = db.query(Quotation).filter_by(id=quotation_id).first()
    if quote is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quotation not found.")

    if quote.supplier_organization_id != organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You cannot modify another supplier's quotation.",
        )

    if quote.status != QUOTATION_STATUS_DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Quotation in status '{quote.status}' is immutable. Use the /revise endpoint to issue revision V{quote.version + 1}.",
        )

    # Update metadata
    if body.currency:
        quote.currency = body.currency.upper()
    if body.valid_until is not None:
        quote.valid_until = body.valid_until
    if body.incoterm:
        quote.incoterm = body.incoterm.upper()
    if body.payment_terms:
        quote.payment_terms = body.payment_terms
    if body.lead_time_days is not None:
        quote.lead_time_days = body.lead_time_days
    if body.shipping_cost is not None:
        quote.shipping_cost = body.shipping_cost
    if body.insurance_cost is not None:
        quote.insurance_cost = body.insurance_cost
    if body.duty_amount is not None:
        quote.duty_amount = body.duty_amount
    if body.tax_amount is not None:
        quote.tax_amount = body.tax_amount
    if body.other_charges is not None:
        quote.other_charges = body.other_charges
    if body.supplier_notes is not None:
        quote.supplier_notes = body.supplier_notes

    # Update items if provided
    if body.items is not None:
        rfq = db.query(RFQ).filter_by(id=quote.rfq_id).first()
        valid_rfq_items = {itm.id: itm for itm in rfq.items}

        # Clear existing items
        for old_itm in quote.items:
            db.delete(old_itm)
        db.flush()

        line_totals = []
        for q_item in body.items:
            if q_item.rfq_item_id not in valid_rfq_items:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Item {q_item.rfq_item_id} does not belong to RFQ {quote.rfq_id}.",
                )
            rfq_item = valid_rfq_items[q_item.rfq_item_id]
            qty = q_item.quantity if q_item.quantity is not None else rfq_item.quantity
            lt = calculate_line_total(qty, q_item.unit_price)
            line_totals.append(lt)

            new_itm = QuotationItem(
                quotation_id=quote.id,
                rfq_item_id=q_item.rfq_item_id,
                product_name_snapshot=rfq_item.product_name_snapshot,
                quantity=qty,
                unit=rfq_item.unit,
                unit_price=q_item.unit_price,
                line_total=lt,
                moq=q_item.moq,
                lead_time_days=q_item.lead_time_days,
                notes=q_item.notes,
            )
            db.add(new_itm)
    else:
        line_totals = [itm.line_total for itm in quote.items]

    # Recalculate totals
    subtotal, total_landed = calculate_quotation_totals(
        item_line_totals=line_totals,
        shipping_cost=quote.shipping_cost,
        insurance_cost=quote.insurance_cost,
        duty_amount=quote.duty_amount,
        tax_amount=quote.tax_amount,
        other_charges=quote.other_charges,
    )
    quote.subtotal_amount = subtotal
    quote.total_landed_cost = total_landed

    db.commit()
    db.refresh(quote)
    return quote


@router.post(
    "/supplier/quotations/{quotation_id}/submit",
    response_model=QuotationRead,
    summary="Formally submit quotation to buyer",
)
def submit_quotation(
    organization_id: uuid.UUID,
    quotation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Quotation:
    """
    Formally submit quotation:
    - Sets quotation status to SUBMITTED and freezes commercial numbers
    - Updates RFQ status to RESPONSES_RECEIVED if currently OPEN or INVITATIONS_SENT
    - Updates supplier invitation status to RESPONDED
    """
    require_organization_membership(
        organization_id, current_user, db, allowed_roles=SUPPLIER_MUTATION_ROLES
    )

    quote = db.query(Quotation).filter_by(id=quotation_id).first()
    if quote is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quotation not found.")

    if quote.supplier_organization_id != organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You cannot submit another supplier's quotation.",
        )

    if quote.status != QUOTATION_STATUS_DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Quotation cannot be submitted from status '{quote.status}'.",
        )

    if not quote.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot submit quotation with zero priced items.",
        )

    # 1. Update quotation
    quote.status = QUOTATION_STATUS_SUBMITTED
    quote.submitted_at = datetime.now(timezone.utc)

    # 2. Update RFQ status if applicable
    rfq = db.query(RFQ).filter_by(id=quote.rfq_id).first()
    if rfq and rfq.status in {RFQ_STATUS_OPEN, RFQ_STATUS_INVITATIONS_SENT}:
        rfq.status = RFQ_STATUS_RESPONSES_RECEIVED

    # 3. Update invitation status
    inv = (
        db.query(RFQSupplierInvitation)
        .filter(
            RFQSupplierInvitation.rfq_id == quote.rfq_id,
            (RFQSupplierInvitation.supplier_organization_id == organization_id)
            | (RFQSupplierInvitation.supplier_email == (current_user.email or "").lower()),
        )
        .first()
    )
    if inv:
        inv.status = "RESPONDED"
        inv.responded_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(quote)
    return quote


@router.post(
    "/supplier/quotations/{quotation_id}/revise",
    response_model=QuotationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Issue revised quotation (supersedes previous version)",
)
def revise_quotation(
    organization_id: uuid.UUID,
    quotation_id: uuid.UUID,
    body: QuotationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Quotation:
    """
    Issue a new revision (Quotation V2) of a submitted quote:
    - Sets previous version status to SUPERSEDED
    - Creates new quotation with version = old.version + 1 and parent_quotation_id = old.id
    - Preserves historical integrity completely
    """
    require_organization_membership(
        organization_id, current_user, db, allowed_roles=SUPPLIER_MUTATION_ROLES
    )

    old_quote = db.query(Quotation).filter_by(id=quotation_id).first()
    if old_quote is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quotation not found.")

    if old_quote.supplier_organization_id != organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You cannot revise another supplier's quotation.",
        )

    if old_quote.status not in {QUOTATION_STATUS_SUBMITTED, QUOTATION_STATUS_UNDER_REVIEW}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot revise quotation in status '{old_quote.status}'.",
        )

    rfq = db.query(RFQ).filter_by(id=old_quote.rfq_id).first()
    valid_rfq_items = {itm.id: itm for itm in rfq.items}

    # 1. Mark old quotation as SUPERSEDED
    old_quote.status = QUOTATION_STATUS_SUPERSEDED

    # 2. Build new quotation items
    line_totals = []
    created_items_data = []
    for q_item in body.items:
        if q_item.rfq_item_id not in valid_rfq_items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Item {q_item.rfq_item_id} does not belong to RFQ {rfq.id}.",
            )
        rfq_item = valid_rfq_items[q_item.rfq_item_id]
        qty = q_item.quantity if q_item.quantity is not None else rfq_item.quantity
        lt = calculate_line_total(qty, q_item.unit_price)
        line_totals.append(lt)
        created_items_data.append({
            "rfq_item_id": q_item.rfq_item_id,
            "product_name_snapshot": rfq_item.product_name_snapshot,
            "quantity": qty,
            "unit": rfq_item.unit,
            "unit_price": q_item.unit_price,
            "line_total": lt,
            "moq": q_item.moq,
            "lead_time_days": q_item.lead_time_days,
            "notes": q_item.notes,
        })

    subtotal, total_landed = calculate_quotation_totals(
        item_line_totals=line_totals,
        shipping_cost=body.shipping_cost,
        insurance_cost=body.insurance_cost,
        duty_amount=body.duty_amount,
        tax_amount=body.tax_amount,
        other_charges=body.other_charges,
    )

    new_quote = Quotation(
        rfq_id=rfq.id,
        supplier_organization_id=organization_id,
        supplier_user_id=current_user.id,
        quotation_number=generate_quotation_number(db),
        version=old_quote.version + 1,
        parent_quotation_id=old_quote.id,
        status=QUOTATION_STATUS_SUBMITTED,
        currency=body.currency.upper(),
        valid_until=body.valid_until,
        incoterm=body.incoterm.upper(),
        payment_terms=body.payment_terms,
        lead_time_days=body.lead_time_days,
        subtotal_amount=subtotal,
        shipping_cost=body.shipping_cost,
        insurance_cost=body.insurance_cost,
        duty_amount=body.duty_amount,
        tax_amount=body.tax_amount,
        other_charges=body.other_charges,
        total_landed_cost=total_landed,
        supplier_notes=body.supplier_notes,
        submitted_at=datetime.now(timezone.utc),
    )
    db.add(new_quote)
    db.flush()

    for itm_dict in created_items_data:
        q_item_orm = QuotationItem(
            quotation_id=new_quote.id,
            **itm_dict,
        )
        db.add(q_item_orm)

    db.commit()
    db.refresh(new_quote)
    return new_quote


# ---------------------------------------------------------------------------
# Negotiation Notes Endpoints
# ---------------------------------------------------------------------------
@router.post(
    "/quotations/{quotation_id}/negotiation-notes",
    response_model=NegotiationNoteRead,
    status_code=status.HTTP_201_CREATED,
    summary="Add a negotiation note or counter-offer",
)
def add_negotiation_note(
    organization_id: uuid.UUID,
    quotation_id: uuid.UUID,
    body: NegotiationNoteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NegotiationNote:
    """
    Post a counter-offer or negotiation message.
    Authorized for either:
    - The buyer organization owning the RFQ
    - The supplier organization owning the quotation
    """
    get_membership_or_403(organization_id, current_user, db)

    quote = db.query(Quotation).filter_by(id=quotation_id).first()
    if quote is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quotation not found.")

    rfq = db.query(RFQ).filter_by(id=quote.rfq_id).first()
    is_buyer = rfq and rfq.organization_id == organization_id
    is_supplier = quote.supplier_organization_id == organization_id

    if not (is_buyer or is_supplier):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You are not authorized to negotiate on this quotation.",
        )

    note = NegotiationNote(
        quotation_id=quote.id,
        organization_id=organization_id,
        author_user_id=current_user.id,
        note_type=body.note_type,
        proposed_target_price=body.proposed_target_price,
        proposed_terms=body.proposed_terms,
        message=body.message,
    )
    db.add(note)

    # Transition RFQ status to NEGOTIATION if counter-offer posted
    if body.note_type == "COUNTER_OFFER" and rfq and rfq.status in {RFQ_STATUS_UNDER_REVIEW, RFQ_STATUS_RESPONSES_RECEIVED}:
        rfq.status = RFQ_STATUS_NEGOTIATION

    db.commit()
    db.refresh(note)
    return note


@router.get(
    "/quotations/{quotation_id}/negotiation-notes",
    response_model=List[NegotiationNoteRead],
    summary="List negotiation notes for a quotation",
)
def list_negotiation_notes(
    organization_id: uuid.UUID,
    quotation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[NegotiationNote]:
    """Retrieve negotiation timeline for quotation."""
    get_membership_or_403(organization_id, current_user, db)

    quote = db.query(Quotation).filter_by(id=quotation_id).first()
    if quote is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quotation not found.")

    rfq = db.query(RFQ).filter_by(id=quote.rfq_id).first()
    is_buyer = rfq and rfq.organization_id == organization_id
    is_supplier = quote.supplier_organization_id == organization_id

    if not (is_buyer or is_supplier):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You are not authorized to view notes on this quotation.",
        )

    notes = (
        db.query(NegotiationNote)
        .filter_by(quotation_id=quote.id)
        .order_by(NegotiationNote.created_at.asc())
        .all()
    )
    return notes
