# app/routes/users_route.py

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.core.db import get_session
from app.schemas.user_schema import UserCreate, UserRead, UserUpdate
from app.services.user_service import (
    create_user,
    list_users,
    get_user,
    update_user,
    delete_user,
)
from app.services.auth_service import current_superuser

router = APIRouter(
    prefix="/users",
    tags=["users"],
    dependencies=[Depends(current_superuser)],  # superuser only
)

@router.get("/", response_model=List[UserRead])
def list_users_endpoint(
    session: Session = Depends(get_session),
):
    return list_users(session)

@router.get("/{user_id}", response_model=UserRead)
def get_user_endpoint(
    user_id: UUID,
    session: Session = Depends(get_session),
):
    user = get_user(session, user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    return user

@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user_endpoint(
    payload: UserCreate,
    session: Session = Depends(get_session),
):
    return create_user(session, payload)

@router.put("/{user_id}", response_model=UserRead)
def update_user_endpoint(
    user_id: UUID,
    payload: UserUpdate,
    session: Session = Depends(get_session),
):
    user = update_user(session, user_id, payload)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    return user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_endpoint(
    user_id: UUID,
    session: Session = Depends(get_session),
):
    success = delete_user(session, user_id)
    if not success:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    return
