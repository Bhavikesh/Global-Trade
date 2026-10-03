"""
Organization model — represents a business or organization using GlobalTrade.ai.

Each Organization is the tenant boundary for all business data.
Organization isolation is enforced by backend authorization (DEC-028).
"""
import uuid
from sqlalchemy import Column, String, DateTime, func, Text, Uuid
from sqlalchemy.orm import relationship

from app.db.session import Base


class Organization(Base):
    __tablename__ = "organizations"

    id: uuid.UUID = Column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )

    legal_name: str = Column(String(500), nullable=False)
    display_name: str = Column(String(255), nullable=True)

    # COMPANY | INDIVIDUAL | PARTNERSHIP | etc.
    business_type: str = Column(String(100), nullable=True)

    country: str = Column(String(2), nullable=True, comment="ISO 3166-1 alpha-2 country code.")
    address: str = Column(Text, nullable=True)

    # Regulatory identifiers (country-dependent)
    tax_identifier: str = Column(String(100), nullable=True)
    vat_identifier: str = Column(String(100), nullable=True)
    iec_number: str = Column(String(100), nullable=True, comment="Import Export Code (India).")

    website: str = Column(String(500), nullable=True)
    contact_information: str = Column(Text, nullable=True)

    # UNVERIFIED | PENDING | VERIFIED | SUSPENDED
    verification_status: str = Column(
        String(50), nullable=False, default="UNVERIFIED"
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    memberships = relationship(
        "OrganizationMembership",
        back_populates="organization",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Organization id={self.id} legal_name={self.legal_name!r}>"
