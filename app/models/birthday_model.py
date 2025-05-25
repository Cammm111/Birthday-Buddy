# app/models/birthday_model.py

import uuid
from datetime import date, datetime, timezone
from typing import Optional, TYPE_CHECKING

from sqlalchemy import UniqueConstraint
from sqlmodel import SQLModel, Field, Relationship
from app.models.workspace_model import Workspace

if TYPE_CHECKING:
    from app.models.user_model import User

class Birthday(SQLModel, table=True):
    __tablename__ = "birthday"
    __table_args__ = (UniqueConstraint("user_id", name="uq_birthday_user"),)

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: Optional[uuid.UUID] = Field(default=None, foreign_key="user.user_id", unique=True)
    name: str = Field(nullable=False)
    date_of_birth: date = Field(nullable=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    workspace_id: Optional[uuid.UUID] = Field(default=None, foreign_key="workspace.id")

    # back to the owning User (if any)
    user: Optional["User"] = Relationship(back_populates="birthday")
    workspace: Optional["Workspace"] = Relationship(back_populates="birthdays")