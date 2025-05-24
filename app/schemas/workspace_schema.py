# app/schemas/workspace_schema.py

import uuid
from typing import Optional
from pydantic import BaseModel

class WorkspaceBase(BaseModel):
    name: str
    slack_webhook: str
    timezone: str

class WorkspaceCreate(WorkspaceBase):
    """
    Fields required to create a Workspace.
    """
    pass

class WorkspaceRead(WorkspaceBase):
    """
    Fields returned when reading a Workspace.
    """
    id: uuid.UUID

class WorkspaceUpdate(BaseModel):
    """
    All fields optional; only provided ones will be updated.
    """
    name: Optional[str] = None
    slack_webhook: Optional[str] = None
    timezone: Optional[str] = None
