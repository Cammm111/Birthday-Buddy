# app/schemas/user_schema.py

import uuid
from datetime import date
from typing import Optional
from fastapi_users import schemas

# ─────────────────────────────Pydantic read model for users─────────────────────────────
class UserRead(schemas.BaseUser[uuid.UUID]):
    date_of_birth: date
    workspace_id: Optional[uuid.UUID] = None
    model_config = {"from_attributes": True }

# ─────────────────────────────Pydantic create model for users─────────────────────────────
class UserCreate(schemas.BaseUserCreate):
    date_of_birth: date
    workspace_id: Optional[uuid.UUID] = None

# ─────────────────────────────Pydantic update model for users─────────────────────────────
class UserUpdate(schemas.BaseUserUpdate):
    date_of_birth: Optional[date] = None
    workspace_id: Optional[uuid.UUID] = None