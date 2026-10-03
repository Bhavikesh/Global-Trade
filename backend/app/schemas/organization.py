"""Pydantic schemas for Organization / Company Profile."""
import re
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


def _clean_str(v: Optional[str]) -> Optional[str]:
    if v is None:
        return None
    trimmed = v.strip()
    return trimmed if trimmed else None


class OrganizationCreate(BaseModel):
    """Fields required to create a new organization."""

    legal_name: str = Field(..., min_length=1, max_length=500, description="Official registered legal name")
    display_name: Optional[str] = Field(None, max_length=255, description="Public display / trade name")
    business_type: Optional[str] = Field(None, max_length=100, description="Business structure or classification")
    country: Optional[str] = Field(None, max_length=2, description="ISO 3166-1 alpha-2 country code")
    address: Optional[str] = Field(None, max_length=2000, description="Registered business address")
    tax_identifier: Optional[str] = Field(None, max_length=100, description="Tax ID / EIN / GSTIN")
    vat_identifier: Optional[str] = Field(None, max_length=100, description="VAT registration number")
    iec_number: Optional[str] = Field(None, max_length=100, description="Import Export Code (e.g. India IEC)")
    website: Optional[str] = Field(None, max_length=500, description="Corporate website URL")
    contact_information: Optional[str] = Field(None, max_length=2000, description="Contact details / phone / email notes")

    @field_validator("legal_name")
    @classmethod
    def validate_legal_name(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Legal name cannot be empty or whitespace only.")
        return trimmed

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
        # Basic URL structure check
        if "." not in cleaned:
            raise ValueError("Website must be a valid domain URL.")
        return cleaned


class OrganizationUpdate(BaseModel):
    """Fields that may be updated on an existing organization / company profile."""

    legal_name: Optional[str] = Field(None, min_length=1, max_length=500)
    display_name: Optional[str] = Field(None, max_length=255)
    business_type: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=2)
    address: Optional[str] = Field(None, max_length=2000)
    tax_identifier: Optional[str] = Field(None, max_length=100)
    vat_identifier: Optional[str] = Field(None, max_length=100)
    iec_number: Optional[str] = Field(None, max_length=100)
    website: Optional[str] = Field(None, max_length=500)
    contact_information: Optional[str] = Field(None, max_length=2000)

    @field_validator("legal_name")
    @classmethod
    def validate_legal_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Legal name cannot be empty or whitespace only.")
        return trimmed

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


class OrganizationRead(BaseModel):
    """Response schema for an Organization record."""

    id: uuid.UUID
    legal_name: str
    display_name: Optional[str]
    business_type: Optional[str]
    country: Optional[str]
    address: Optional[str]
    tax_identifier: Optional[str]
    vat_identifier: Optional[str]
    iec_number: Optional[str]
    website: Optional[str]
    contact_information: Optional[str]
    verification_status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
