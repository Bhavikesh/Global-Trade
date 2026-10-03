"""
current_user dependency — resolves a verified JWT claim set into an
application-level User database record.

On first login, a new User row is automatically created (upsert by
identity_provider_id).  This keeps user provisioning simple without a
separate sign-up flow.

The User record is the foundation for all subsequent authorization checks,
including OrganizationMembership and role resolution.
"""
from typing import Any

from fastapi import Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.auth.jwt import verify_jwt
from app.db.session import get_db
from app.models.user import User


def get_current_user(
    claims: dict[str, Any] = Depends(verify_jwt),
    db: Session = Depends(get_db),
) -> User:
    """
    FastAPI dependency.

    Verifies the Auth0 JWT via `verify_jwt`, then looks up (or creates) the
    corresponding User record in the application database.

    Returns the User ORM object for downstream use.

    Usage:
        @router.get("/me")
        def me(user: User = Depends(get_current_user)):
            ...
    """
    identity_provider_id: str = claims.get("sub", "")
    if not identity_provider_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identity claim missing from token.",
        )

    user = db.query(User).filter_by(identity_provider_id=identity_provider_id).first()

    if user is None:
        # First login — provision application User record.
        user = User(
            identity_provider_id=identity_provider_id,
            email=claims.get("email"),
            name=claims.get("name"),
        )
        db.add(user)
        try:
            db.commit()
            db.refresh(user)
        except IntegrityError:
            db.rollback()
            user = (
                db.query(User)
                .filter_by(identity_provider_id=identity_provider_id)
                .first()
            )
            if user is None:
                raise

    return user

