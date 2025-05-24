# app/routes/birthdays_route.py

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.core.db import get_session
from app.schemas.birthday_schema import BirthdayCreate, BirthdayRead, BirthdayUpdate
from app.services.birthday_service import (
    create_birthday,
    list_birthdays,
    get_birthday,
    update_birthday,
    delete_birthday,
)
from app.services.redis_cache_service import (
    get_cached_birthdays,
    set_cached_birthdays,
    invalidate_birthdays_cache,
)
from app.services.auth_service import current_active_user

router = APIRouter(
    prefix="/birthdays",
    tags=["birthdays"],
    dependencies=[Depends(current_active_user)],
)

@router.post("/", response_model=BirthdayRead, status_code=status.HTTP_201_CREATED)
def create_birthday_endpoint(
    payload: BirthdayCreate,
    session: Session = Depends(get_session),
    user=Depends(current_active_user),
):
    bday = create_birthday(session, user.id, payload)
    # Invalidate cache so next GET shows updated list
    invalidate_birthdays_cache(user.id)
    return bday

@router.get("/", response_model=List[BirthdayRead])
def list_birthdays_endpoint(
    session: Session = Depends(get_session),
    user=Depends(current_active_user),
):
    # Try cache first
    cached = get_cached_birthdays(user.id)
    if cached is not None:
        return cached
    items = list_birthdays(session, user.id)
    set_cached_birthdays(user.id, items)
    return items

@router.get("/{bday_id}", response_model=BirthdayRead)
def get_birthday_endpoint(
    bday_id: UUID,
    session: Session = Depends(get_session),
    user=Depends(current_active_user),
):
    bday = get_birthday(session, user.id, bday_id)
    if not bday:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Birthday not found")
    return bday

@router.put("/{bday_id}", response_model=BirthdayRead)
def update_birthday_endpoint(
    bday_id: UUID,
    payload: BirthdayUpdate,
    session: Session = Depends(get_session),
    user=Depends(current_active_user),
):
    bday = update_birthday(session, user.id, bday_id, payload)
    if not bday:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Birthday not found")
    invalidate_birthdays_cache(user.id)
    return bday

@router.delete("/{bday_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_birthday_endpoint(
    bday_id: UUID,
    session: Session = Depends(get_session),
    user=Depends(current_active_user),
):
    success = delete_birthday(session, user.id, bday_id)
    if not success:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Birthday not found")
    invalidate_birthdays_cache(user.id)
    return
