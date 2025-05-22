# app/schemas.py

from typing import Optional
from uuid import UUID
from sqlmodel import SQLModel, Field

class WorkspaceBase(SQLModel):
    name: str
    slack_webhook: str
    timezone: str = "UTC"


class WorkspaceCreate(WorkspaceBase):
    """
    Required fields when creating a workspace.
    """
    pass


class WorkspaceRead(WorkspaceBase):
    """
    What we return to clients when reading a workspace.
    """
    id: UUID

    class Config:
        # Pydantic v2: use from_attributes instead of orm_mode
        from_attributes = True


class WorkspaceUpdate(SQLModel):
    """
    All fields optional for PATCH /workspaces/{id}.
    """
    name: Optional[str] = None
    slack_webhook: Optional[str] = None
    timezone: Optional[str] = None
