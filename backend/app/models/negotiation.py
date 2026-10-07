"""
Negotiation models — Structured counter-offer and negotiation timeline foundation.

Provides deterministic audit history of buyer counter-offers and supplier responses.
NO automated AI agents or auto-negotiation in this phase.
"""
import uuid
from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    Numeric,
    ForeignKey,
    CheckConstraint,
    func,
    Uuid,
)
from sqlalchemy.orm import relationship

from app.db.session import Base

NOTE_TYPE_BUYER_NOTE = "BUYER_NOTE"
NOTE_TYPE_COUNTER_OFFER = "COUNTER_OFFER"
NOTE_TYPE_SUPPLIER_RESPONSE = "SUPPLIER_RESPONSE"

ALL_NOTE_TYPES = {
    NOTE_TYPE_BUYER_NOTE,
    NOTE_TYPE_COUNTER_OFFER,
    NOTE_TYPE_SUPPLIER_RESPONSE,
}


class NegotiationNote(Base):
    """
    Message or counter-offer associated with a quotation.
    """
    __tablename__ = "negotiation_notes"
    __table_args__ = (
        CheckConstraint(
            f"note_type IN ('BUYER_NOTE', 'COUNTER_OFFER', 'SUPPLIER_RESPONSE')",
            name="ck_negotiation_notes_type",
        ),
        CheckConstraint(
            "proposed_target_price IS NULL OR proposed_target_price >= 0",
            name="ck_negotiation_notes_price_non_negative",
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

    # Organization of the author
    organization_id: uuid.UUID = Column(
        Uuid(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    author_user_id: uuid.UUID = Column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    note_type: str = Column(String(50), nullable=False)
    proposed_target_price = Column(Numeric(14, 4), nullable=True)
    proposed_terms: str = Column(Text, nullable=True)
    message: str = Column(Text, nullable=False)

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    quotation = relationship("Quotation", back_populates="negotiation_notes")
    organization = relationship("Organization")
    author_user = relationship("User")
