# app/schemas/birthday_schema.py

import uuid
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field as PydanticField

class BirthdayBase(BaseModel):
    name: str
    date_of_birth: date
    user_id: Optional[uuid.UUID] = None

class BirthdayCreate(BirthdayBase):
    pass

class BirthdayRead(BirthdayBase):
    id: uuid.UUID
    created_at: datetime

class BirthdayUpdate(BaseModel):
    """
    All fields optional; only the provided ones will be updated.
    """
    name: Optional[str] = None
    date_of_birth: Optional[date] = None
