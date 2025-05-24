# app/models/user_model.py

import uuid
from datetime import date
from typing import List, Optional

from pydantic import EmailStr
from sqlalchemy import Column, String
from sqlmodel import SQLModel, Field, Relationship

class User(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    email: EmailStr = Field(
        sa_column=Column("email", String, unique=True, index=True, nullable=False)
    )
    hashed_password: str
    date_of_birth: date = Field(nullable=False)
    workspace_id: Optional[uuid.UUID] = Field(default=None, foreign_key="workspace.id")
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)
    is_verified: bool = Field(default=False)

    # a user has many birthdays
    birthdays: List["Birthday"] = Relationship(back_populates="user")
    # a user belongs to at most one workspace
    workspace: Optional["Workspace"] = Relationship(back_populates="users")
