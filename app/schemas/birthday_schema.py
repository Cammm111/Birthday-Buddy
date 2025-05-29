# app/schemas/birthday_schema.py

import uuid
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel

# ─────────────────────────────Pydantic base model for birthdays─────────────────────────────
class BirthdayBase(BaseModel):
    name: str
    date_of_birth: date
    user_id: Optional[uuid.UUID] = None
    workspace_id: Optional[uuid.UUID] = None

# ─────────────────────────────Pydantic create model for birthdays─────────────────────────────
class BirthdayCreate(BirthdayBase):  # Threw in for potential future additions (welcome emails or something)
    pass

# ─────────────────────────────Pydantic read model for birthdays─────────────────────────────
class BirthdayRead(BirthdayBase):
    id: uuid.UUID
    created_at: datetime
    class Config:
        from_attributes = True

# ─────────────────────────────Pydantic update model for birthdays─────────────────────────────
class BirthdayUpdate(BaseModel):
    name: Optional[str] = None
    date_of_birth: Optional[date] = None
    workspace_id: Optional[uuid.UUID] = None