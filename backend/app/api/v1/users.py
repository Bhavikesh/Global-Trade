"""
User profile routes — /api/v1/users

GET  /me       — return the authenticated user's own profile
PATCH /me      — update name / phone on the authenticated user's profile
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserRead, summary="Get authenticated user's profile")
def get_me(current_user: User = Depends(get_current_user)) -> UserRead:
    """Return the authenticated user's application profile."""
    return current_user


@router.patch("/me", response_model=UserRead, summary="Update authenticated user's profile")
def update_me(
    body: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserRead:
    """Update mutable fields on the authenticated user's profile (name, phone)."""
    if body.name is not None:
        current_user.name = body.name
    if body.phone is not None:
        current_user.phone = body.phone

    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user
