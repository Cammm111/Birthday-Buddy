# app/services/birthday_service.py

import uuid
from typing import List, Optional
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from app.models.birthday_model import Birthday
from app.models.user_model import User
from app.schemas.birthday_schema import BirthdayCreate, BirthdayUpdate
from app.services.redis_cache_service import (
    get_cached_birthdays,
    set_cached_birthdays,
    invalidate_birthdays_cache,
)


def sync_birthday_from_user(session: Session, user: User) -> None:
    birthday = session.exec(select(Birthday).where(Birthday.user_id == user.user_id)).first()
    if birthday:
        birthday.name = user.email  # or user.name
        birthday.date_of_birth = user.date_of_birth
        birthday.workspace_id = user.workspace_id
        session.add(birthday)
    else:
        birthday = Birthday(
            user_id=user.user_id,
            name=user.email,
            date_of_birth=user.date_of_birth,
            workspace_id=user.workspace_id,
        )
        session.add(birthday)
    session.commit()


def create_birthday(session: Session, user_id: uuid.UUID, payload: BirthdayCreate) -> Birthday:
    bday = Birthday(**payload.dict())
    bday.user_id = user_id
    session.add(bday)
    try:
        session.commit()
        session.refresh(bday)
    except IntegrityError:
        session.rollback()
        raise HTTPException(...)

    invalidate_birthdays_cache(user_id)
    return bday


def list_birthdays(session: Session, user_id: uuid.UUID) -> List[Birthday]:
    cached = get_cached_birthdays(user_id)
    if cached:
        return cached

    stmt = select(Birthday).where(Birthday.user_id == user_id)
    results = session.exec(stmt).all()
    set_cached_birthdays(user_id, results)
    return results


def get_birthday(session: Session, user_id: uuid.UUID, bday_id: uuid.UUID) -> Optional[Birthday]:
    bday = session.get(Birthday, bday_id)
    if not bday or bday.user_id != user_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Birthday not found")
    return bday


def update_birthday(session: Session, user_id: uuid.UUID, bday_id: uuid.UUID, payload: BirthdayUpdate) -> Optional[Birthday]:
    bday = session.get(Birthday, bday_id)
    if not bday or bday.user_id != user_id:
        return None

    for field, value in payload.dict(exclude_unset=True).items():
        setattr(bday, field, value)

    session.add(bday)
    session.commit()
    session.refresh(bday)

    invalidate_birthdays_cache(user_id)
    return bday


def delete_birthday(session: Session, user_id: uuid.UUID, bday_id: uuid.UUID) -> bool:
    bday = session.get(Birthday, bday_id)
    if not bday or bday.user_id != user_id:
        return False

    session.delete(bday)
    session.commit()

    invalidate_birthdays_cache(user_id)
    return True