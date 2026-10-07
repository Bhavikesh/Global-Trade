"""Pydantic schemas for Supplier management.

Authoritative source: docs/DATA_MODEL.md section 12 & docs/TASKS.md T1.15, T1.16.
"""
import re
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

VALID_VERIFICATION_STATUSES = {"UNVERIFIED", "PENDING", "VERIFIED", "SUSPENDED"}
EMAIL_REGEX = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class SupplierCreate(BaseModel):
    """Schema for creating a new supplier record."""

    company_name: str = Field(..., min_length=1, max_length=255, description="Supplier company name")
    contact_name: Optional[str] = Field(None, max_length=255, description="Primary contact name")
    email: Optional[str] = Field(None, max_length=255, description="Contact email address")
    phone: Optional[str] = Field(None, max_length=50, description="Contact phone number")
    country: Optional[str] = Field(None, max_length=2, description="ISO 3166-1 alpha-2 country code")
    address: Optional[str] = Field(None, max_length=2000, description="Business address")
    website: Optional[str] = Field(None, max_length=500, description="Company website URL")
    supplier_type: Optional[str] = Field(None, max_length=100, description="Supplier classification")
    verification_status: str = Field("UNVERIFIED", max_length=50, description="Verification status")
    certifications: Optional[str] = Field(None, description="Quality and regulatory certifications")
    notes: Optional[str] = Field(None, description="General sourcing notes")

    @field_validator("company_name")
    @classmethod
    def validate_company_name(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Company name cannot be empty or whitespace only.")
        return trimmed

    @field_validator("contact_name")
    @classmethod
    def validate_contact_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        trimmed = v.strip()
        return trimmed if trimmed else None

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        cleaned = v.strip()
        if not cleaned:
            return None
        if not re.match(EMAIL_REGEX, cleaned):
            raise ValueError("Email must be a valid email address.")
        return cleaned.lower()

    @field_validator("country")
    @classmethod
    def validate_country(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        cleaned = v.strip().upper()
        if not cleaned:
            return None
        if len(cleaned) != 2 or not cleaned.isalpha():
            raise ValueError("Country code must be a 2-letter ISO 3166-1 alpha-2 code.")
        return cleaned

    @field_validator("website")
    @classmethod
    def validate_website(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        cleaned = v.strip()
        if not cleaned:
            return None
        if not (cleaned.startswith("http://") or cleaned.startswith("https://")):
            cleaned = f"https://{cleaned}"
        if "." not in cleaned:
            raise ValueError("Website must be a valid domain URL.")
        return cleaned

    @field_validator("supplier_type")
    @classmethod
    def validate_supplier_type(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        trimmed = v.strip()
        return trimmed if trimmed else None

    @field_validator("verification_status")
    @classmethod
    def validate_verification_status(cls, v: str) -> str:
        cleaned = v.strip().upper()
        if cleaned not in VALID_VERIFICATION_STATUSES:
            raise ValueError(
                f"Invalid verification status '{v}'. Allowed values are: {', '.join(sorted(VALID_VERIFICATION_STATUSES))}"
            )
        return cleaned


class SupplierUpdate(BaseModel):
    """Schema for updating an existing supplier record (partial update)."""

    company_name: Optional[str] = Field(None, min_length=1, max_length=255)
    contact_name: Optional[str] = Field(None, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    country: Optional[str] = Field(None, max_length=2)
    address: Optional[str] = Field(None, max_length=2000)
    website: Optional[str] = Field(None, max_length=500)
    supplier_type: Optional[str] = Field(None, max_length=100)
    verification_status: Optional[str] = Field(None, max_length=50)
    certifications: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("company_name")
    @classmethod
    def validate_company_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Company name cannot be empty or whitespace only.")
        return trimmed

    @field_validator("contact_name")
    @classmethod
    def validate_contact_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        trimmed = v.strip()
        return trimmed if trimmed else None

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        cleaned = v.strip()
        if not cleaned:
            return None
        if not re.match(EMAIL_REGEX, cleaned):
            raise ValueError("Email must be a valid email address.")
        return cleaned.lower()

    @field_validator("country")
    @classmethod
    def validate_country(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        cleaned = v.strip().upper()
        if not cleaned:
            return None
        if len(cleaned) != 2 or not cleaned.isalpha():
            raise ValueError("Country code must be a 2-letter ISO 3166-1 alpha-2 code.")
        return cleaned

    @field_validator("website")
    @classmethod
    def validate_website(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        cleaned = v.strip()
        if not cleaned:
            return None
        if not (cleaned.startswith("http://") or cleaned.startswith("https://")):
            cleaned = f"https://{cleaned}"
        if "." not in cleaned:
            raise ValueError("Website must be a valid domain URL.")
        return cleaned

    @field_validator("supplier_type")
    @classmethod
    def validate_supplier_type(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        trimmed = v.strip()
        return trimmed if trimmed else None

    @field_validator("verification_status")
    @classmethod
    def validate_verification_status(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        cleaned = v.strip().upper()
        if cleaned not in VALID_VERIFICATION_STATUSES:
            raise ValueError(
                f"Invalid verification status '{v}'. Allowed values are: {', '.join(sorted(VALID_VERIFICATION_STATUSES))}"
            )
        return cleaned


class SupplierRead(BaseModel):
    """Response schema for a Supplier record."""

    id: uuid.UUID
    organization_id: uuid.UUID
    company_name: str
    contact_name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    country: Optional[str]
    address: Optional[str]
    website: Optional[str]
    supplier_type: Optional[str]
    verification_status: str
    certifications: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
