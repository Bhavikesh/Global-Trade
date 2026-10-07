"""Pydantic schemas for Product and ProductFile."""
import re
import uuid
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProductCreate(BaseModel):
    """Fields required to create a new product."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(..., min_length=1, max_length=255, description="Product name")
    description: Optional[str] = Field(None, description="Detailed product description")
    category: Optional[str] = Field(None, max_length=100, description="Product category")
    specifications: Optional[str] = Field(None, description="Technical specifications")
    moq: Optional[str] = Field(None, max_length=100, description="Minimum order quantity")
    packaging: Optional[str] = Field(None, description="Packaging details")
    pricing_information: Optional[str] = Field(None, description="Pricing terms / details")
    hs_code: Optional[str] = Field(None, max_length=20, description="Harmonized System tariff code")
    keywords: Optional[str] = Field(None, description="Search and classification keywords")
    seo_description: Optional[str] = Field(None, description="SEO optimized description")
    international_description: Optional[str] = Field(None, description="International trade description")

    @field_validator("hs_code")
    @classmethod
    def validate_hs_code(cls, v: Optional[str]) -> Optional[str]:
        if v is None or not v:
            return None
        if not re.match(r"^[0-9. ]+$", v):
            raise ValueError("HS code may only contain digits, dots, and spaces.")
        return v


class ProductUpdate(BaseModel):
    """Fields that may be updated on a product. All fields default to None."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)
    specifications: Optional[str] = None
    moq: Optional[str] = Field(None, max_length=100)
    packaging: Optional[str] = None
    pricing_information: Optional[str] = None
    hs_code: Optional[str] = Field(None, max_length=20)
    keywords: Optional[str] = None
    seo_description: Optional[str] = None
    international_description: Optional[str] = None
    status: Optional[Literal["ACTIVE", "ARCHIVED"]] = None

    @field_validator("name", "status")
    @classmethod
    def check_not_null(cls, v):
        if v is None:
            raise ValueError("This field cannot be null")
        return v

    @field_validator("hs_code")
    @classmethod
    def validate_hs_code(cls, v: Optional[str]) -> Optional[str]:
        if v is None or not v:
            return None
        if not re.match(r"^[0-9. ]+$", v):
            raise ValueError("HS code may only contain digits, dots, and spaces.")
        return v


class ProductRead(BaseModel):
    """Response schema for a Product record."""

    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    specifications: Optional[str] = None
    moq: Optional[str] = None
    packaging: Optional[str] = None
    pricing_information: Optional[str] = None
    hs_code: Optional[str] = None
    keywords: Optional[str] = None
    seo_description: Optional[str] = None
    international_description: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProductFileCreate(BaseModel):
    """Schema for attaching a file to a product."""

    model_config = ConfigDict(str_strip_whitespace=True)

    file_reference: str = Field(..., min_length=1, max_length=1024, description="URI or path reference to the file")
    file_type: str = Field(..., min_length=1, max_length=50, description="Type: IMAGE, CERTIFICATE, SPECIFICATION, etc.")


class ProductFileRead(BaseModel):
    """Response schema for a ProductFile record."""

    id: uuid.UUID
    product_id: uuid.UUID
    organization_id: uuid.UUID
    file_reference: str
    file_type: str
    created_at: datetime

    model_config = {"from_attributes": True}
