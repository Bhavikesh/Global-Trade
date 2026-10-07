"""
Product and ProductFile models.

Product — represents a trade product managed by an organization.
ProductFile — represents metadata for files/media associated with a product.
"""
import uuid
from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import relationship

from app.db.session import Base


class Product(Base):
    __tablename__ = "products"

    __table_args__ = (
        CheckConstraint("status IN ('ACTIVE', 'ARCHIVED')", name="ck_products_status"),
    )

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

    name: str = Column(String(255), nullable=False)
    description: str = Column(Text, nullable=True)
    category: str = Column(String(100), nullable=True)
    specifications: str = Column(Text, nullable=True)
    moq: str = Column(String(100), nullable=True)
    packaging: str = Column(Text, nullable=True)
    pricing_information: str = Column(Text, nullable=True)
    hs_code: str = Column(String(20), nullable=True)
    keywords: str = Column(Text, nullable=True)
    seo_description: str = Column(Text, nullable=True)
    international_description: str = Column(Text, nullable=True)

    # ACTIVE | ARCHIVED
    status: str = Column(String(20), nullable=False, default="ACTIVE")

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
    # Organization.products is NOT defined (organization.py is a shared file).
    organization = relationship("Organization")
    files = relationship(
        "ProductFile",
        back_populates="product",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Product id={self.id} name={self.name!r} org={self.organization_id}>"


class ProductFile(Base):
    __tablename__ = "product_files"

    id: uuid.UUID = Column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )

    product_id: uuid.UUID = Column(
        Uuid(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    organization_id: uuid.UUID = Column(
        Uuid(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    file_reference: str = Column(String(1024), nullable=False)
    file_type: str = Column(String(50), nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    product = relationship("Product", back_populates="files")

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<ProductFile id={self.id} product={self.product_id} "
            f"type={self.file_type!r}>"
        )
