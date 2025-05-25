# app/schemas/workspace_schema.py

import uuid
from typing import List, Optional
from sqlmodel import SQLModel, Field

class WorkspaceBase(SQLModel):
    name: str
    slack_webhook: str

    # mark timezone optional and default it in the schema too
    timezone: Optional[str] = Field(
        default="America/New_York",
        description="IANA timezone name; defaults to New York"
    )

class WorkspaceCreate(WorkspaceBase):
    pass

class WorkspaceRead(WorkspaceBase):
    id: uuid.UUID

    class Config:
        orm_mode = True

class WorkspaceUpdate(SQLModel):
    name: Optional[str] = None
    slack_webhook: Optional[str] = None
    timezone: Optional[str] = None
