# app/routes/user_route.py

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.core.db import get_session
from app.models.user_model import User
from app.schemas.user_schema import UserRead, UserUpdate
from app.services.auth_service import current_active_user, current_superuser

router = APIRouter(
    prefix="/users",
    tags=["users"],
)

# ─── General users / superusers ─────────────────────────────────────────────────

@router.get(
    "/",
    response_model=List[UserRead],
    summary="List users in your workspace  (Auth: any active user)",
    description="Returns all users belonging to the authenticated user's workspace."
)
def list_users(
    session: Session = Depends(get_session),
    user=Depends(current_active_user),
):
    stmt = select(User).where(User.workspace_id == user.workspace_id)
    return session.exec(stmt).all()

@router.get(
    "/all",
    response_model=List[UserRead],
    dependencies=[Depends(current_superuser)],
    summary="List all users  (Auth: superuser)",
    description="Returns every user in the system, regardless of workspace."
)
def list_all_users(
    session: Session = Depends(get_session),
):
    stmt = select(User)
    return session.exec(stmt).all()

@router.patch(
    "/{user_id}",
    response_model=UserRead,
    summary="Update a user  (Auth: self or superuser)",
    description=(
        "General users may only update their own account; superusers may update any user."
    )
)
def patch_user(
    user_id: UUID,
    payload: UserUpdate,
    session: Session = Depends(get_session),
    user=Depends(current_active_user),
):
    target = session.get(User, user_id)
    if not target:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

    # only allow non-superusers to patch themselves
    if not user.is_superuser and user.id != user_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Cannot modify other users")

    update_data = payload.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(target, field, value)

    session.add(target)
    session.commit()
    session.refresh(target)
    return target

# ─── Superuser only ─────────────────────────────────────────────────────────────

@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(current_superuser)],
    summary="Delete a user  (Auth: superuser)",
    description="Remove any user by ID. Superusers only."
)
def delete_user(
    user_id: UUID,
    session: Session = Depends(get_session),
):
    target = session.get(User, user_id)
    if not target:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    session.delete(target)
    session.commit()
    return
