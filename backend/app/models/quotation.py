"""
Quotation models — Supplier responses to RFQs and line item breakdowns.

Follows docs/DATA_MODEL.md Sections 16, 17, 18.
Uses exact Decimal/Numeric representations for money and arithmetic.
Submitted commercial values are immutable; revisions create a new version.
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
    func,
    Uuid,
)
from sqlalchemy.orm import relationship

from app.db.session import Base

# ---------------------------------------------------------------------------
# Quotation Status Constants
# ---------------------------------------------------------------------------
QUOTATION_STATUS_DRAFT = "DRAFT"
QUOTATION_STATUS_SUBMITTED = "SUBMITTED"
QUOTATION_STATUS_UNDER_REVIEW = "UNDER_REVIEW"
QUOTATION_STATUS_ACCEPTED = "ACCEPTED"
QUOTATION_STATUS_REJECTED = "REJECTED"
QUOTATION_STATUS_SUPERSEDED = "SUPERSEDED"
QUOTATION_STATUS_EXPIRED = "EXPIRED"

ALL_QUOTATION_STATUSES = {
    QUOTATION_STATUS_DRAFT,
    QUOTATION_STATUS_SUBMITTED,
    QUOTATION_STATUS_UNDER_REVIEW,
    QUOTATION_STATUS_ACCEPTED,
    QUOTATION_STATUS_REJECTED,
    QUOTATION_STATUS_SUPERSEDED,
    QUOTATION_STATUS_EXPIRED,
}


class Quotation(Base):
    """
    Supplier quotation submitted against an RFQ.
    Tenant boundary: supplier_organization_id.
    """
    __tablename__ = "quotations"
    __table_args__ = (
        CheckConstraint(
            f"status IN ('DRAFT', 'SUBMITTED', 'UNDER_REVIEW', 'ACCEPTED', "
            f"'REJECTED', 'SUPERSEDED', 'EXPIRED')",
            name="ck_quotations_status",
        ),
        CheckConstraint("version >= 1", name="ck_quotations_version_positive"),
        CheckConstraint(
            "lead_time_days >= 0", name="ck_quotations_lead_time_non_negative"
        ),
        CheckConstraint(
            "subtotal_amount >= 0", name="ck_quotations_subtotal_non_negative"
        ),
        CheckConstraint(
            "total_landed_cost >= 0",
            name="ck_quotations_total_landed_cost_non_negative",
        ),
        CheckConstraint(
            "shipping_cost IS NULL OR shipping_cost >= 0",
            name="ck_quotations_shipping_non_negative",
        ),
        CheckConstraint(
            "insurance_cost IS NULL OR insurance_cost >= 0",
            name="ck_quotations_insurance_non_negative",
        ),
        CheckConstraint(
            "duty_amount IS NULL OR duty_amount >= 0",
            name="ck_quotations_duty_non_negative",
        ),
        CheckConstraint(
            "tax_amount IS NULL OR tax_amount >= 0",
            name="ck_quotations_tax_non_negative",
        ),
        CheckConstraint(
            "other_charges IS NULL OR other_charges >= 0",
            name="ck_quotations_other_charges_non_negative",
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

    # Tenant boundary for supplier
    supplier_organization_id: uuid.UUID = Column(
        Uuid(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Author user
    supplier_user_id: uuid.UUID = Column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    # Human-readable reference number (e.g. QT-2026-XXXX)
    quotation_number: str = Column(
        String(50), unique=True, nullable=False, index=True
    )

    # Version tracking for revisions
    version: int = Column(Integer, nullable=False, default=1)
    parent_quotation_id: uuid.UUID = Column(
        Uuid(as_uuid=True),
        ForeignKey("quotations.id", ondelete="SET NULL"),
        nullable=True,
    )

    status: str = Column(
        String(50), nullable=False, default=QUOTATION_STATUS_DRAFT, index=True
    )

    currency: str = Column(String(3), nullable=False, default="USD")
    valid_until = Column(Date, nullable=True)

    incoterm: str = Column(String(10), nullable=False, comment="FOB, CIF, etc.")
    payment_terms: str = Column(String(100), nullable=False)
    lead_time_days: int = Column(Integer, nullable=False, default=0)

    # Exact commercial figures
    subtotal_amount = Column(
        Numeric(14, 2), nullable=False, default=0.00
    )
    shipping_cost = Column(Numeric(14, 2), nullable=True)
    insurance_cost = Column(Numeric(14, 2), nullable=True)
    duty_amount = Column(Numeric(14, 2), nullable=True)
    tax_amount = Column(Numeric(14, 2), nullable=True)
    other_charges = Column(Numeric(14, 2), nullable=True)
    total_landed_cost = Column(
        Numeric(14, 2), nullable=False, default=0.00
    )

    supplier_notes: str = Column(Text, nullable=True)
    submitted_at = Column(DateTime(timezone=True), nullable=True)

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
    rfq = relationship("RFQ", back_populates="quotations")
    supplier_organization = relationship("Organization")
    supplier_user = relationship("User")
    items = relationship(
        "QuotationItem",
        back_populates="quotation",
        cascade="all, delete-orphan",
    )
    parent_quotation = relationship(
        "Quotation",
        remote_side=[id],
        backref="revisions",
    )
    negotiation_notes = relationship(
        "NegotiationNote",
        back_populates="quotation",
        cascade="all, delete-orphan",
    )


class QuotationItem(Base):
    """
    Individual item pricing within a Quotation.
    Matches a specific RFQItem.
    """
    __tablename__ = "quotation_items"
    __table_args__ = (
        CheckConstraint(
            "quantity > 0", name="ck_quotation_items_quantity_positive"
        ),
        CheckConstraint(
            "unit_price >= 0", name="ck_quotation_items_unit_price_non_negative"
        ),
        CheckConstraint(
            "line_total >= 0", name="ck_quotation_items_line_total_non_negative"
        ),
        CheckConstraint(
            "moq IS NULL OR moq > 0", name="ck_quotation_items_moq_positive"
        ),
        CheckConstraint(
            "lead_time_days IS NULL OR lead_time_days >= 0",
            name="ck_quotation_items_lead_time_non_negative",
        ),
    )

    id: uuid.UUID = Column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )

    quotation_id: uuid.UUID = Column(
        Uuid(as_uuid=True),
        ForeignKey("quotations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    rfq_item_id: uuid.UUID = Column(
        Uuid(as_uuid=True),
        ForeignKey("rfq_items.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # Product snapshot for commercial certainty
    product_name_snapshot: str = Column(String(255), nullable=False)

    quantity = Column(Numeric(14, 2), nullable=False)
    unit: str = Column(String(20), nullable=False, default="PCS")

    unit_price = Column(Numeric(14, 4), nullable=False)
    line_total = Column(Numeric(14, 2), nullable=False)

    moq = Column(Numeric(14, 2), nullable=True)
    lead_time_days: int = Column(Integer, nullable=True)
    notes: str = Column(Text, nullable=True)

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
    quotation = relationship("Quotation", back_populates="items")
    rfq_item = relationship("RFQItem", back_populates="quotation_items")
