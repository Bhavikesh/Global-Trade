"""
RFQ models — Request for Quotation, RFQ Items, and Supplier Invitations.

Follows docs/DATA_MODEL.md Sections 13, 14, 15 and ARCHITECTURE.md.
Organization is the tenant boundary (DEC-028).
Decimal/Numeric types are used exclusively for monetary & quantity values.
"""
import uuid
from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    Date,
    Integer,
    Numeric,
    ForeignKey,
    CheckConstraint,
    UniqueConstraint,
    func,
    Uuid,
)
from sqlalchemy.orm import relationship

from app.db.session import Base

# ---------------------------------------------------------------------------
# Allowed RFQ & Invitation Status Constants
# ---------------------------------------------------------------------------
RFQ_STATUS_DRAFT = "DRAFT"
RFQ_STATUS_OPEN = "OPEN"
RFQ_STATUS_INVITATIONS_SENT = "INVITATIONS_SENT"
RFQ_STATUS_RESPONSES_RECEIVED = "RESPONSES_RECEIVED"
RFQ_STATUS_UNDER_REVIEW = "UNDER_REVIEW"
RFQ_STATUS_NEGOTIATION = "NEGOTIATION"
RFQ_STATUS_AWARDED = "AWARDED"
RFQ_STATUS_CANCELLED = "CANCELLED"
RFQ_STATUS_EXPIRED = "EXPIRED"

ALL_RFQ_STATUSES = {
    RFQ_STATUS_DRAFT,
    RFQ_STATUS_OPEN,
    RFQ_STATUS_INVITATIONS_SENT,
    RFQ_STATUS_RESPONSES_RECEIVED,
    RFQ_STATUS_UNDER_REVIEW,
    RFQ_STATUS_NEGOTIATION,
    RFQ_STATUS_AWARDED,
    RFQ_STATUS_CANCELLED,
    RFQ_STATUS_EXPIRED,
}

INVITATION_STATUS_INVITED = "INVITED"
INVITATION_STATUS_VIEWED = "VIEWED"
INVITATION_STATUS_RESPONDED = "RESPONDED"
INVITATION_STATUS_DECLINED = "DECLINED"
INVITATION_STATUS_EXPIRED = "EXPIRED"

ALL_INVITATION_STATUSES = {
    INVITATION_STATUS_INVITED,
    INVITATION_STATUS_VIEWED,
    INVITATION_STATUS_RESPONDED,
    INVITATION_STATUS_DECLINED,
    INVITATION_STATUS_EXPIRED,
}


class RFQ(Base):
    """
    Request for Quotation model.
    Represents a sourcing request issued by a buyer organization.
    """
    __tablename__ = "rfqs"
    __table_args__ = (
        CheckConstraint(
            f"status IN ('DRAFT', 'OPEN', 'INVITATIONS_SENT', 'RESPONSES_RECEIVED', "
            f"'UNDER_REVIEW', 'NEGOTIATION', 'AWARDED', 'CANCELLED', 'EXPIRED')",
            name="ck_rfqs_status",
        ),
    )

    id: uuid.UUID = Column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )

    # Tenant boundary
    organization_id: uuid.UUID = Column(
        Uuid(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Collision-safe human-readable reference number (e.g. RFQ-2026-XXXX)
    rfq_number: str = Column(String(50), unique=True, nullable=False, index=True)

    title: str = Column(String(255), nullable=False)
    description: str = Column(Text, nullable=True)

    destination_country: str = Column(
        String(2), nullable=False, comment="ISO 3166-1 alpha-2 country code."
    )
    destination_port: str = Column(String(100), nullable=True)
    required_delivery_date = Column(Date, nullable=True)

    preferred_incoterm: str = Column(
        String(10), nullable=True, comment="e.g. FOB, CIF, EXW, DDP"
    )
    preferred_payment_terms: str = Column(
        String(100), nullable=True, comment="e.g. LC at sight, T/T 30/70"
    )
    currency: str = Column(String(3), nullable=False, default="USD")

    status: str = Column(
        String(50), nullable=False, default=RFQ_STATUS_DRAFT, index=True
    )

    # Pointer to winning quotation when awarded
    awarded_quotation_id: uuid.UUID = Column(
        Uuid(as_uuid=True), nullable=True
    )

    notes: str = Column(Text, nullable=True)

    created_by_user_id: uuid.UUID = Column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    organization = relationship("Organization")
    created_by = relationship("User")
    items = relationship(
        "RFQItem",
        back_populates="rfq",
        cascade="all, delete-orphan",
        order_by="RFQItem.item_index",
    )
    invitations = relationship(
        "RFQSupplierInvitation",
        back_populates="rfq",
        cascade="all, delete-orphan",
    )
    quotations = relationship(
        "Quotation",
        back_populates="rfq",
        cascade="all, delete-orphan",
    )


class RFQItem(Base):
    """
    Individual requested product/item requirement within an RFQ.
    Preserves product_name_snapshot and specs to guarantee historical immutability.
    """
    __tablename__ = "rfq_items"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_rfq_items_quantity_positive"),
        CheckConstraint(
            "target_unit_price IS NULL OR target_unit_price >= 0",
            name="ck_rfq_items_target_price_non_negative",
        ),
    )

    id: uuid.UUID = Column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )

    rfq_id: uuid.UUID = Column(
        Uuid(as_uuid=True),
        ForeignKey("rfqs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    item_index: int = Column(Integer, nullable=False, default=1)

    # Future integration: nullable product catalog ID from Developer 1
    product_id: uuid.UUID = Column(Uuid(as_uuid=True), nullable=True)

    # Historical snapshot fields
    product_name_snapshot: str = Column(String(255), nullable=False)
    description: str = Column(Text, nullable=True)

    quantity = Column(Numeric(14, 2), nullable=False)
    unit: str = Column(String(20), nullable=False, default="PCS")

    target_unit_price = Column(Numeric(14, 4), nullable=True)

    specifications: str = Column(Text, nullable=True)
    quality_requirements: str = Column(Text, nullable=True)
    packaging_requirements: str = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    rfq = relationship("RFQ", back_populates="items")
    quotation_items = relationship(
        "QuotationItem",
        back_populates="rfq_item",
    )


class RFQSupplierInvitation(Base):
    """
    Supplier invitation to participate in an RFQ.
    Prevents duplicate invitations and maintains audit trail.
    """
    __tablename__ = "rfq_supplier_invitations"
    __table_args__ = (
        UniqueConstraint(
            "rfq_id", "supplier_email", name="uq_rfq_invitation_rfq_email"
        ),
        CheckConstraint(
            f"status IN ('INVITED', 'VIEWED', 'RESPONDED', 'DECLINED', 'EXPIRED')",
            name="ck_rfq_invitations_status",
        ),
    )

    id: uuid.UUID = Column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )

    rfq_id: uuid.UUID = Column(
        Uuid(as_uuid=True),
        ForeignKey("rfqs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Optional link to registered organization on platform
    supplier_organization_id: uuid.UUID = Column(
        Uuid(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Future integration: nullable supplier counterparty ID from Developer 2
    supplier_id: uuid.UUID = Column(Uuid(as_uuid=True), nullable=True)

    supplier_email: str = Column(String(255), nullable=False)
    supplier_name: str = Column(String(255), nullable=False)

    invited_by_user_id: uuid.UUID = Column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    status: str = Column(
        String(50), nullable=False, default=INVITATION_STATUS_INVITED, index=True
    )

    response_deadline = Column(DateTime(timezone=True), nullable=True)
    invited_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    responded_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    rfq = relationship("RFQ", back_populates="invitations")
    supplier_organization = relationship("Organization")
    invited_by = relationship("User")
