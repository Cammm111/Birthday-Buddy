# app/models.py

import uuid
from datetime import date, datetime, timezone
from typing import Optional, List
from pydantic import BaseModel, EmailStr
from sqlalchemy import Column, String
from sqlmodel import SQLModel, Field

# SQLModel DB table for users
class User(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    email: EmailStr = Field(
        sa_column=Column("email", String, unique=True, index=True, nullable=False)
    )
    hashed_password: str
    is_active: bool = True
    is_superuser: bool = False
    is_verified: bool = False
    workspace_id: Optional[uuid.UUID] = Field(default=None, foreign_key="workspace.id")

# Pydantic schemas for API (do NOT inherit from SQLModel here)
class UserRead(BaseModel):
    id: uuid.UUID
    email: EmailStr
    is_active: bool
    is_superuser: bool
    is_verified: bool
    workspace_id: Optional[uuid.UUID] = None

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    workspace_id: Optional[uuid.UUID] = None

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    is_verified: Optional[bool] = None
    workspace_id: Optional[uuid.UUID] = None

# Birthday SQLModel and Pydantic schemas
class BirthdayBase(SQLModel):
    name: str
    date_of_birth: date
    user_id: Optional[uuid.UUID] = Field(default=None, foreign_key="user.id")  

class BirthdayCreate(BirthdayBase):
    pass

class BirthdayRead(BirthdayBase):
    id: uuid.UUID
    created_at: datetime

class Birthday(BirthdayBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Workspace SQLModel
class Workspace(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str
    slack_webhook: str
    timezone: str
