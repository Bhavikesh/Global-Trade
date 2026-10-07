"""
Pydantic v2 schemas for Quotation, Quotation Items, Negotiation Notes, and Comparison.
"""
from datetime import date, datetime
from decimal import Decimal
import uuid
from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Quotation Item Schemas
# ---------------------------------------------------------------------------
class QuotationItemCreate(BaseModel):
    rfq_item_id: uuid.UUID
    unit_price: Decimal = Field(..., ge=0)
    quantity: Decimal | None = Field(default=None, gt=0)
    moq: Decimal | None = Field(default=None, gt=0)
    lead_time_days: int | None = Field(default=None, ge=0)
    notes: str | None = None


class QuotationItemRead(BaseModel):
    id: uuid.UUID
    quotation_id: uuid.UUID
    rfq_item_id: uuid.UUID
    product_name_snapshot: str
    quantity: Decimal
    unit: str
    unit_price: Decimal
    line_total: Decimal
    moq: Decimal | None
    lead_time_days: int | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Quotation Schemas
# ---------------------------------------------------------------------------
class QuotationCreate(BaseModel):
    currency: str = Field(default="USD", min_length=3, max_length=3)
    valid_until: date | None = None
    incoterm: str = Field(..., min_length=2, max_length=10)
    payment_terms: str = Field(..., min_length=2, max_length=100)
    lead_time_days: int = Field(default=0, ge=0)
    shipping_cost: Decimal | None = Field(default=None, ge=0)
    insurance_cost: Decimal | None = Field(default=None, ge=0)
    duty_amount: Decimal | None = Field(default=None, ge=0)
    tax_amount: Decimal | None = Field(default=None, ge=0)
    other_charges: Decimal | None = Field(default=None, ge=0)
    supplier_notes: str | None = None
    items: list[QuotationItemCreate] = Field(..., min_length=1)


class QuotationUpdate(BaseModel):
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    valid_until: date | None = None
    incoterm: str | None = Field(default=None, min_length=2, max_length=10)
    payment_terms: str | None = Field(default=None, min_length=2, max_length=100)
    lead_time_days: int | None = Field(default=None, ge=0)
    shipping_cost: Decimal | None = Field(default=None, ge=0)
    insurance_cost: Decimal | None = Field(default=None, ge=0)
    duty_amount: Decimal | None = Field(default=None, ge=0)
    tax_amount: Decimal | None = Field(default=None, ge=0)
    other_charges: Decimal | None = Field(default=None, ge=0)
    supplier_notes: str | None = None
    items: list[QuotationItemCreate] | None = None


class QuotationRead(BaseModel):
    id: uuid.UUID
    rfq_id: uuid.UUID
    supplier_organization_id: uuid.UUID
    supplier_organization_name: str | None = None
    supplier_user_id: uuid.UUID
    quotation_number: str
    version: int
    parent_quotation_id: uuid.UUID | None
    status: str
    currency: str
    valid_until: date | None
    incoterm: str
    payment_terms: str
    lead_time_days: int
    subtotal_amount: Decimal
    shipping_cost: Decimal | None
    insurance_cost: Decimal | None
    duty_amount: Decimal | None
    tax_amount: Decimal | None
    other_charges: Decimal | None
    total_landed_cost: Decimal
    supplier_notes: str | None
    submitted_at: datetime | None
    created_at: datetime
    updated_at: datetime

    items: list[QuotationItemRead] = []

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Negotiation Note Schemas
# ---------------------------------------------------------------------------
class NegotiationNoteCreate(BaseModel):
    note_type: str = Field(..., pattern="^(BUYER_NOTE|COUNTER_OFFER|SUPPLIER_RESPONSE)$")
    proposed_target_price: Decimal | None = Field(default=None, ge=0)
    proposed_terms: str | None = None
    message: str = Field(..., min_length=1)


class NegotiationNoteRead(BaseModel):
    id: uuid.UUID
    quotation_id: uuid.UUID
    organization_id: uuid.UUID
    author_user_id: uuid.UUID
    author_name: str | None = None
    note_type: str
    proposed_target_price: Decimal | None
    proposed_terms: str | None
    message: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Quotation Comparison Schema
# ---------------------------------------------------------------------------
class QuoteComparisonRead(BaseModel):
    quotation_count: int
    currency_consistent: bool
    currency: str | None
    lowest_subtotal_quotation_id: str | None
    lowest_landed_cost_quotation_id: str | None
    fastest_delivery_quotation_id: str | None
    items_comparison: list[dict]
    quotations: list[QuotationRead]
