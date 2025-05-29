# app/schemas/workspace_schema.py

import re
import uuid
from typing import Optional
from sqlmodel import SQLModel, Field

_SLACK_URL_RE = re.compile(r"^https://hooks\.slack\.com/services/[A-Za-z0-9]+/[A-Za-z0-9]+/[A-Za-z0-9]+$") # Slack validation

# ─────────────────────────────Workspace base model─────────────────────────────
class WorkspaceBase(SQLModel):
    name: str
    slack_webhook: str = Field(..., regex=_SLACK_URL_RE.pattern, description="Slack Incoming Webhook URL",)
    timezone: Optional[str] = Field(
        default="America/New_York",
        description="IANA timezone name; defaults to New York"
    )

# ─────────────────────────────Workspace create model─────────────────────────────
class WorkspaceCreate(WorkspaceBase):
    pass

# ─────────────────────────────Workspace read model─────────────────────────────
class WorkspaceRead(WorkspaceBase):
    id: uuid.UUID
    model_config = {"from_attributes": True}

# ─────────────────────────────Workspace update model─────────────────────────────
class WorkspaceUpdate(SQLModel):
    name: Optional[str] = None
    slack_webhook: Optional[str] = None
    timezone: Optional[str] = None