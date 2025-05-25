# app/schemas/user_schema.py

import uuid
from datetime import date
from typing import Optional
from fastapi_users import schemas

class UserRead(schemas.BaseUser[uuid.UUID]):
    date_of_birth: date
    workspace_id: Optional[uuid.UUID] = None

    model_config = {
        "from_attributes": True  # for Pydantic V2 -> allow reading from ORM
    }

class UserCreate(schemas.BaseUserCreate):
    date_of_birth: date
    workspace_id: Optional[uuid.UUID] = None

class UserUpdate(schemas.BaseUserUpdate):
    date_of_birth: Optional[date] = None
    workspace_id: Optional[uuid.UUID] = None
