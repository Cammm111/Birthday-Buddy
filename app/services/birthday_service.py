# app/services/birthday_service.py

import uuid
from typing import List, Optional
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from app.models.birthday_model import Birthday
from app.schemas.birthday_schema import BirthdayCreate, BirthdayRead, BirthdayUpdate

def create_birthday(
    session: Session,
    user_id: uuid.UUID,
    payload: BirthdayCreate
) -> Birthday:
    """
    Create a new birthday record for the given user.
    Enforces one birthday per user via DB unique constraint.
    """
    bday = Birthday(**payload.dict())
    bday.user_id = user_id
    session.add(bday)
    try:
        session.commit()
        session.refresh(bday)
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has a birthday on file."
        )
    return bday

def list_birthdays(
    session: Session,
    user_id: uuid.UUID
) -> List[Birthday]:
    """
    Return all birthdays belonging to a user.
    """
    stmt = select(Birthday).where(Birthday.user_id == user_id)
    return session.exec(stmt).all()

def get_birthday(
    session: Session,
    user_id: uuid.UUID,
    bday_id: uuid.UUID
) -> Optional[Birthday]:
    """
    Retrieve a single birthday by its ID if it belongs to the user.
    """
    bday = session.get(Birthday, bday_id)
    if bday and bday.user_id == user_id:
        return bday
    return None

def update_birthday(
    session: Session,
    user_id: uuid.UUID,
    bday_id: uuid.UUID,
    payload: BirthdayUpdate
) -> Optional[Birthday]:
    """
    Update fields of an existing birthday.
    """
    bday = session.get(Birthday, bday_id)
    if not bday or bday.user_id != user_id:
        return None
    update_data = payload.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(bday, field, value)
    session.add(bday)
    session.commit()
    session.refresh(bday)
    return bday

def delete_birthday(
    session: Session,
    user_id: uuid.UUID,
    bday_id: uuid.UUID
) -> bool:
    """
    Delete a birthday if it belongs to the user.
    Returns True if deleted, False otherwise.
    """
    bday = session.get(Birthday, bday_id)
    if not bday or bday.user_id != user_id:
        return False
    session.delete(bday)
    session.commit()
    return True
