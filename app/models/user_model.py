# app/models/user_model.py

import uuid
from datetime import date
from typing import Optional

from pydantic import EmailStr
from sqlalchemy import Column, String
from sqlmodel import SQLModel, Field, Relationship

class User(SQLModel, table=True):
    user_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    email: EmailStr = Field(sa_column=Column("email", String, unique=True, index=True, nullable=False))
    name: str = Field(default="Unknown")  # NOT NULL at DB level
    hashed_password: str
    date_of_birth: date = Field(nullable=False)
    workspace_id: Optional[uuid.UUID] = Field(default=None, foreign_key="workspace.id")
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)
    is_verified: bool = Field(default=False)

    birthday: Optional["Birthday"] = Relationship(back_populates="user")
    workspace: Optional["Workspace"] = Relationship(back_populates="users")

    @property
    def id(self) -> uuid.UUID:
        """Expose `user_id` as `id` for FastAPI Users compatibility."""
        return self.user_id