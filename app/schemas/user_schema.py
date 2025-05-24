# app/schemas/user_schema.py

import uuid
from datetime import date
from typing import Optional
from pydantic import BaseModel, EmailStr

class UserRead(BaseModel):
    id: uuid.UUID
    email: EmailStr
    date_of_birth: date
    is_active: bool
    is_superuser: bool
    is_verified: bool
    workspace_id: Optional[uuid.UUID] = None

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    date_of_birth: date              # ← now required
    workspace_id: Optional[uuid.UUID] = None

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    date_of_birth: Optional[date] = None  # ← optional on update
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    is_verified: Optional[bool] = None
    workspace_id: Optional[uuid.UUID] = None
