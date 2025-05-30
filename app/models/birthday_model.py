# app/models/birthday_model.py

import uuid
from datetime import date, datetime, timezone
from typing import Optional, TYPE_CHECKING
from sqlalchemy import UniqueConstraint
from sqlmodel import SQLModel, Field, Relationship
from app.models.workspace_model import Workspace # this causes that circular import :(

# ──────────────────────────Prevent circular imports from workspace model───────────────────────────────
if TYPE_CHECKING:
    from app.models.user_model import User

# ──────────────────────────Define birthday model──────────────────────────────────────────
class Birthday(SQLModel, table=True):
    __tablename__ = "birthday"
    __table_args__ = (UniqueConstraint("user_id", name="uq_birthday_user"),)
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: Optional[uuid.UUID] = Field(default=None, foreign_key="user.user_id", unique=True) # Indexing for user_id in birthday
    name: str = Field(nullable=False)
    date_of_birth: date = Field(nullable=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    workspace_id: Optional[uuid.UUID] = Field(default=None, foreign_key="workspace.id")

    # Establish foreign key relationships in database
    user: Optional["User"] = Relationship(back_populates="birthday") # Each user can have at most one birthday
    workspace: Optional["Workspace"] = Relationship(back_populates="birthdays") # Each birthday can have many workspaces