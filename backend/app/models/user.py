"""
User model — represents an authenticated platform user.

Authentication credentials are not stored here.
Auth0 is the managed identity provider (DEC-038).
We store only the application-level user record identified by
the Auth0 `sub` claim (identity_provider_id).
"""
import uuid
from sqlalchemy import Column, String, Boolean, DateTime, func, Uuid
from sqlalchemy.orm import relationship

from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id: uuid.UUID = Column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )

    # Auth0 subject claim — unique identifier from the identity provider.
    identity_provider_id: str = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="Auth0 subject claim (sub) — unique user identity from the IdP.",
    )

    name: str = Column(String(255), nullable=True)
    email: str = Column(String(255), nullable=True, index=True)
    phone: str = Column(String(50), nullable=True)

    # ACTIVE | INACTIVE | SUSPENDED
    status: str = Column(String(50), nullable=False, default="ACTIVE")

    # Soft metadata
    is_active: bool = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    memberships = relationship(
        "OrganizationMembership",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User id={self.id} email={self.email!r}>"
