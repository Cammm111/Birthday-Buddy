import uuid
from datetime import date, datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field

class Birthday(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str
    date_of_birth: date
    user_id: Optional[uuid.UUID] = Field(default=None, foreign_key="user.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
