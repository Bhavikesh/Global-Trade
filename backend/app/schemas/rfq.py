"""
Pydantic v2 schemas for RFQ, RFQ Items, and Supplier Invitations.
"""
from datetime import date, datetime
from decimal import Decimal
import uuid
from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# RFQ Item Schemas
# ---------------------------------------------------------------------------
class RFQItemBase(BaseModel):
    item_index: int = Field(default=1, ge=1)
    product_id: uuid.UUID | None = None
    product_name_snapshot: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    quantity: Decimal = Field(..., gt=0)
    unit: str = Field(default="PCS", min_length=1, max_length=20)
    target_unit_price: Decimal | None = Field(default=None, ge=0)
    specifications: str | None = None
    quality_requirements: str | None = None
    packaging_requirements: str | None = None


class RFQItemCreate(RFQItemBase):
    pass


class RFQItemRead(RFQItemBase):
    id: uuid.UUID
    rfq_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# RFQ Supplier Invitation Schemas
# ---------------------------------------------------------------------------
class SupplierInvitationCreate(BaseModel):
    supplier_email: str = Field(..., pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", max_length=255)
    supplier_name: str = Field(..., min_length=1, max_length=255)
    supplier_organization_id: uuid.UUID | None = None
    supplier_id: uuid.UUID | None = None
    response_deadline: datetime | None = None


class SupplierInvitationBatchCreate(BaseModel):
    invitations: list[SupplierInvitationCreate] = Field(..., min_length=1)


class SupplierInvitationRead(BaseModel):
    id: uuid.UUID
    rfq_id: uuid.UUID
    supplier_organization_id: uuid.UUID | None
    supplier_id: uuid.UUID | None
    supplier_email: str
    supplier_name: str
    invited_by_user_id: uuid.UUID
    status: str
    response_deadline: datetime | None
    invited_at: datetime
    responded_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Master RFQ Schemas
# ---------------------------------------------------------------------------
class RFQCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    description: str | None = None
    destination_country: str = Field(..., min_length=2, max_length=2, description="ISO 3166-1 alpha-2")
    destination_port: str | None = Field(default=None, max_length=100)
    required_delivery_date: date | None = None
    preferred_incoterm: str | None = Field(default=None, max_length=10)
    preferred_payment_terms: str | None = Field(default=None, max_length=100)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    notes: str | None = None
    items: list[RFQItemCreate] = Field(..., min_length=1, description="At least one item required")


class RFQUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = None
    destination_country: str | None = Field(default=None, min_length=2, max_length=2)
    destination_port: str | None = Field(default=None, max_length=100)
    required_delivery_date: date | None = None
    preferred_incoterm: str | None = Field(default=None, max_length=10)
    preferred_payment_terms: str | None = Field(default=None, max_length=100)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    notes: str | None = None


class RFQRead(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    rfq_number: str
    title: str
    description: str | None
    destination_country: str
    destination_port: str | None
    required_delivery_date: date | None
    preferred_incoterm: str | None
    preferred_payment_terms: str | None
    currency: str
    status: str
    awarded_quotation_id: uuid.UUID | None
    notes: str | None
    created_by_user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    items: list[RFQItemRead] = []
    invitations_count: int = 0
    quotations_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class RFQListRead(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    rfq_number: str
    title: str
    destination_country: str
    preferred_incoterm: str | None
    currency: str
    status: str
    required_delivery_date: date | None
    created_at: datetime
    items_count: int = 0
    invitations_count: int = 0
    quotations_count: int = 0

    model_config = ConfigDict(from_attributes=True)
