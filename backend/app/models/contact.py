"""
CRMContact model — represents an individual contact associated with a buyer or supplier.

Authoritative source: docs/DATA_MODEL.md section 31.
Every CRMContact record is tenant-isolated by organization_id (DEC-028).
"""
import uuid
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, func, Uuid
from sqlalchemy.orm import relationship

from app.db.session import Base


class CRMContact(Base):
    __tablename__ = "crm_contacts"

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

    buyer_id: uuid.UUID = Column(
        Uuid(as_uuid=True),
        ForeignKey("buyers.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    supplier_id: uuid.UUID = Column(
        Uuid(as_uuid=True),
        ForeignKey("suppliers.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    name: str = Column(String(255), nullable=False)
    email: str = Column(String(255), nullable=True)
    phone: str = Column(String(50), nullable=True)
    designation: str = Column(String(100), nullable=True)
    notes: str = Column(Text, nullable=True)
    is_primary: bool = Column(Boolean, nullable=False, default=False)

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
    organization = relationship("Organization", back_populates="contacts")
    buyer = relationship("Buyer", back_populates="contacts")
    supplier = relationship("Supplier", back_populates="contacts")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<CRMContact id={self.id} name={self.name!r}>"
