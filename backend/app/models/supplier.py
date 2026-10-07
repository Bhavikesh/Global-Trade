"""
Supplier model — represents a supplier, manufacturer, factory, or trading company in GlobalTrade.ai.

Authoritative source: docs/DATA_MODEL.md section 12 & docs/TASKS.md T1.15, T1.16.
Every Supplier record is tenant-isolated by organization_id (DEC-028).
"""
import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, func, Uuid
from sqlalchemy.orm import relationship

from app.db.session import Base


class Supplier(Base):
    __tablename__ = "suppliers"

    id: uuid.UUID = Column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )

    organization_id: uuid.UUID = Column(
        Uuid(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    company_name: str = Column(String(255), nullable=False, index=True)
    contact_name: str = Column(String(255), nullable=True)
    email: str = Column(String(255), nullable=True, index=True)
    phone: str = Column(String(50), nullable=True)
    country: str = Column(
        String(2),
        nullable=True,
        index=True,
        comment="ISO 3166-1 alpha-2 country code.",
    )
    address: str = Column(Text, nullable=True)
    website: str = Column(String(500), nullable=True)
    supplier_type: str = Column(String(100), nullable=True, index=True)

    # UNVERIFIED | PENDING | VERIFIED | SUSPENDED
    verification_status: str = Column(
        String(50),
        nullable=False,
        default="UNVERIFIED",
        index=True,
    )

    certifications: str = Column(Text, nullable=True)
    notes: str = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    organization = relationship("Organization", back_populates="suppliers")
    contacts = relationship(
        "CRMContact",
        back_populates="supplier",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Supplier id={self.id} company_name={self.company_name!r}>"
