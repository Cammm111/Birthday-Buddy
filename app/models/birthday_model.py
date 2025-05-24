# app/models/birthday_model.py

import uuid
from datetime import date, datetime, timezone
from typing import Optional

from sqlmodel import SQLModel, Field, Relationship

class Birthday(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    name: str
    date_of_birth: date
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # back to the owning User
    user: "User" = Relationship(back_populates="birthdays")
