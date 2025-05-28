# app/models/user_model.py

import uuid
from datetime import date
from typing import Optional
from pydantic import EmailStr
from sqlalchemy import Column, String
from sqlmodel import SQLModel, Field, Relationship

# ──────────────────────────Define user model──────────────────────────────────────────
class User(SQLModel, table=True):
    user_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    email: EmailStr = Field(sa_column=Column("email", String, unique=True, index=True, nullable=False))
    name: str = Field(default="Unknown") # Need to have a value for name 
    hashed_password: str
    date_of_birth: date = Field(nullable=False)
    workspace_id: Optional[uuid.UUID] = Field(default=None, foreign_key="workspace.id")
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)
    is_verified: bool = Field(default=False)

    # Establish foreign key relationships in database
    birthday: Optional["Birthday"] = Relationship(back_populates="user") # Each user has zero or one birthday record
    workspace: Optional["Workspace"] = Relationship(back_populates="users") # Each user belongs to exactly one workspace (or none)

    # Exposes "user_id" as "id" for FastAPI Users compatibility (this took a while to figure out...)
    @property
    def id(self) -> uuid.UUID: 
        return self.user_id