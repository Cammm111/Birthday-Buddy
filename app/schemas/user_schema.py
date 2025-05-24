import uuid
from typing import Optional
from pydantic import BaseModel, EmailStr

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
