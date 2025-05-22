# app/models.py
import uuid
from datetime import datetime, date, timezone
from typing import List, Optional
from sqlmodel import SQLModel, Field, Relationship

class Workspace(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str
    slack_webhook: str
    timezone: str = "UTC"
    birthdays: List["Birthday"] = Relationship(back_populates="workspace")

class BirthdayBase(SQLModel):
    name: str
    date_of_birth: date
    workspace_id: uuid.UUID

class Birthday(BirthdayBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    workspace_id: uuid.UUID = Field(foreign_key="workspace.id")
    workspace: Optional[Workspace] = Relationship(back_populates="birthdays")