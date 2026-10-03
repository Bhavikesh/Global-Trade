"""Pydantic schemas for OrganizationMembership."""
import uuid
from datetime import datetime

from pydantic import BaseModel, field_validator

from app.core.auth.permissions import ALL_ROLES


class MembershipRead(BaseModel):
    """Response schema for a membership record."""

    id: uuid.UUID
    organization_id: uuid.UUID
    user_id: uuid.UUID
    role: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MembershipInvite(BaseModel):
    """Schema for inviting an existing user to an organization."""

    user_id: uuid.UUID
    role: str = "MEMBER"

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        if v not in ALL_ROLES:
            raise ValueError(
                f"Invalid role '{v}'. Allowed roles are: {', '.join(sorted(ALL_ROLES))}"
            )
        return v


class MembershipRoleUpdate(BaseModel):
    """Schema for updating a member's role."""

    role: str

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        if v not in ALL_ROLES:
            raise ValueError(
                f"Invalid role '{v}'. Allowed roles are: {', '.join(sorted(ALL_ROLES))}"
            )
        return v

