"""Pydantic schemas for CRM Contact management.

Authoritative source: docs/DATA_MODEL.md section 31.
"""
import re
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

EMAIL_REGEX = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class ContactCreate(BaseModel):
    """Schema for creating a new CRM contact."""

    name: str = Field(..., min_length=1, max_length=255, description="Contact full name")
    email: Optional[str] = Field(None, max_length=255, description="Contact email address")
    phone: Optional[str] = Field(None, max_length=50, description="Contact telephone number")
    designation: Optional[str] = Field(None, max_length=100, description="Job title / role")
    notes: Optional[str] = Field(None, description="Contact notes")
    is_primary: bool = Field(False, description="Whether this is the primary contact")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Contact name cannot be empty or whitespace only.")
        return trimmed

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

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        trimmed = v.strip()
        return trimmed if trimmed else None

    @field_validator("designation")
    @classmethod
    def validate_designation(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        trimmed = v.strip()
        return trimmed if trimmed else None


class ContactUpdate(BaseModel):
    """Schema for updating an existing CRM contact (partial update)."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    designation: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None
    is_primary: Optional[bool] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Contact name cannot be empty or whitespace only.")
        return trimmed

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

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        trimmed = v.strip()
        return trimmed if trimmed else None

    @field_validator("designation")
    @classmethod
    def validate_designation(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        trimmed = v.strip()
        return trimmed if trimmed else None


class ContactRead(BaseModel):
    """Response schema for a CRM Contact record."""

    id: uuid.UUID
    organization_id: uuid.UUID
    buyer_id: Optional[uuid.UUID]
    supplier_id: Optional[uuid.UUID]
    name: str
    email: Optional[str]
    phone: Optional[str]
    designation: Optional[str]
    notes: Optional[str]
    is_primary: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
