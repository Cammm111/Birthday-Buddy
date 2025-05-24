import uuid
from typing import Optional
from pydantic import EmailStr
from sqlalchemy import Column, String
from sqlmodel import SQLModel, Field

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
