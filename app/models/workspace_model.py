# app/models/workspace_model.py

import uuid
from typing import List
from sqlmodel import SQLModel, Field, Relationship

class Workspace(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str
    slack_webhook: str
    timezone: str

    # a workspace can have many users
    users: List["User"] = Relationship(back_populates="workspace")
