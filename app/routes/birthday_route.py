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
from app.services.auth_service import current_active_user, current_superuser

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
    if user.is_superuser and payload.user_id:
        target_user_id = payload.user_id
    else:
        target_user_id = user.id

    bday = create_birthday(session, target_user_id, payload)
    invalidate_birthdays_cache(target_user_id)
    return bday

@router.get("/", response_model=List[BirthdayRead])
def list_birthdays_endpoint(
    session: Session = Depends(get_session),
    user=Depends(current_active_user),
):
    lookup_id = user.id if not user.is_superuser else user.id  # or None if superusers should see all
    # sync cache lookup
    cached = get_cached_birthdays(lookup_id)
    if cached is not None:
        # cached is a list of dicts
        return [BirthdayRead(**d) for d in cached]

    items = list_birthdays(session, lookup_id)
    set_cached_birthdays(lookup_id, items)
    return items

@router.get("/{bday_id}", response_model=BirthdayRead)
def get_birthday_endpoint(
    bday_id: UUID,
    session: Session = Depends(get_session),
    user=Depends(current_active_user),
):
    lookup_id = user.id if not user.is_superuser else user.id
    bday = get_birthday(session, lookup_id, bday_id)
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
    lookup_id = user.id if not user.is_superuser else user.id
    bday = update_birthday(session, lookup_id, bday_id, payload)
    if not bday:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Birthday not found")
    invalidate_birthdays_cache(lookup_id)
    return bday

@router.delete("/{bday_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_birthday_endpoint(
    bday_id: UUID,
    session: Session = Depends(get_session),
    user=Depends(current_active_user),
):
    lookup_id = user.id if not user.is_superuser else user.id
    success = delete_birthday(session, lookup_id, bday_id)
    if not success:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Birthday not found")
    invalidate_birthdays_cache(lookup_id)
