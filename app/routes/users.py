# app/routers/users.py
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from app.db import get_session
from app.models import User, UserRead, UserUpdate
from app.auth import current_active_user, current_superuser

router = APIRouter(prefix="/users", tags=["users"])

@router.get(
    "/",
    response_model=List[UserRead],
    summary="List all users in your workspace",
)
def read_workspace_users(
    current_user: User = Depends(current_active_user),
    session: Session = Depends(get_session),
):
    stmt = select(User).where(User.workspace_id == current_user.workspace_id)
    return session.exec(stmt).all()

@router.get(
    "/all",
    response_model=List[UserRead],
    summary="List all users (superuser only)",
    dependencies=[Depends(current_superuser)],
)
def read_all_users(session: Session = Depends(get_session)):
    return session.exec(select(User)).all()

@router.patch(
    "/{user_id}",
    response_model=UserRead,
    summary="Update a user in your workspace",
)
def update_user(
    user_id: uuid.UUID,
    user_update: UserUpdate,
    current_user: User = Depends(current_active_user),
    session: Session = Depends(get_session),
):
    user = session.get(User, user_id)
    if not user or user.workspace_id != current_user.workspace_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    data = user_update.dict(exclude_unset=True)
    for field, value in data.items():
        setattr(user, field, value)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a user in your workspace",
)
def delete_user(
    user_id: uuid.UUID,
    current_user: User = Depends(current_active_user),
    session: Session = Depends(get_session),
):
    user = session.get(User, user_id)
    if not user or user.workspace_id != current_user.workspace_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    session.delete(user)
    session.commit()
