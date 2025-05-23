# app/routers/birthdays.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select, Session

from app.models import Birthday, BirthdayCreate
from app.db import get_session

router = APIRouter(prefix="/birthdays", tags=["birthdays"])

@router.post("/", response_model=Birthday, status_code=201)
def create_birthday(data: BirthdayCreate, session: Session = Depends(get_session)):
    """Create a new birthday entry."""
    birthday = Birthday.from_orm(data)      # convert Pydantic → ORM
    session.add(birthday)
    session.commit()
    session.refresh(birthday)
    return birthday

@router.get("/", response_model=List[Birthday])
def list_birthdays(session: Session = Depends(get_session)):
    """Return all birthdays sorted by month/day."""
    stmt = select(Birthday).order_by(Birthday.date_of_birth)
    return session.exec(stmt).all()
