# app/routes/user_route.py

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.core.db import get_session
from app.models.user_model import User
from app.schemas.user_schema import UserRead, UserCreate, UserUpdate
from app.services.auth_service import current_active_user, current_superuser

router = APIRouter(
    prefix="/users",
    tags=["users"],
)

# ─── READ ───────────────────────────────────────────────────────────────────────

@router.get(
    "/",
    response_model=List[UserRead],
    summary="List users in your workspace (or all users if superuser)"
)
def list_users_endpoint(
    session: Session = Depends(get_session),
    current_user: User = Depends(current_active_user),
):
    stmt = select(User)
    if not current_user.is_superuser:
        stmt = stmt.where(User.workspace_id == current_user.workspace_id)
    users = session.exec(stmt).all()
    return users


@router.get(
    "/{user_id}",
    response_model=UserRead,
    summary="Get a single user by ID"
)
def get_user_endpoint(
    user_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(current_active_user),
):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    if not current_user.is_superuser and user.workspace_id != current_user.workspace_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not authorized to view this user")
    return user


# ─── UPDATE (partial & full) ────────────────────────────────────────────────────

@router.patch(
    "/{user_id}",
    response_model=UserRead,
    summary="Partially update your own user (or any user if superuser)"
)
def patch_user_endpoint(
    user_id: UUID,
    payload: UserUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(current_active_user),
):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

    # permission: self or superuser
    if not current_user.is_superuser and current_user.id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not authorized to update this user")

    data = payload.dict(exclude_unset=True)

    # regular users may not change workspace_id or is_superuser flags
    if not current_user.is_superuser:
        forbidden = {"workspace_id", "is_superuser", "is_verified", "is_active"}
        if any(field in forbidden for field in data):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Cannot modify that field")

    for field, value in data.items():
        setattr(user, field, value)

    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@router.put(
    "/{user_id}",
    response_model=UserRead,
    dependencies=[Depends(current_superuser)],
    summary="Fully replace a user (superusers only)"
)
def put_user_endpoint(
    user_id: UUID,
    payload: UserCreate,
    session: Session = Depends(get_session),
):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

    # overwrite all fields
    for field, value in payload.dict().items():
        setattr(user, field, value)

    session.add(user)
    session.commit()
    session.refresh(user)
    return user


# ─── CREATE & DELETE (superuser-only) ───────────────────────────────────────────

@router.post(
    "/",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(current_superuser)],
    summary="Create a new user (superusers only)"
)
def create_user_endpoint(
    payload: UserCreate,
    session: Session = Depends(get_session),
):
    user = User.from_orm(payload)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(current_superuser)],
    summary="Delete a user (superusers only)"
)
def delete_user_endpoint(
    user_id: UUID,
    session: Session = Depends(get_session),
):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    session.delete(user)
    session.commit()
    return
