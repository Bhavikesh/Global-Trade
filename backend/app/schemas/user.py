"""Pydantic schemas for User."""
import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserRead(BaseModel):
    """Response schema for a User record."""

    id: uuid.UUID
    identity_provider_id: str
    name: str | None
    email: str | None
    phone: str | None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    """Fields a user may update on their own profile."""

    name: str | None = None
    phone: str | None = None
