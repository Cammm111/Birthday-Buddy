# app/models/workspace_model.py

import uuid
from typing import List
from sqlmodel import SQLModel, Field, Relationship

class Workspace(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str
    slack_webhook: str
    timezone: str = Field(
        default="America/New_York", # Default timezone to New York
        nullable=False,
        description="IANA timezone name; defaults to New York"
    )

    # Establish foreign key relationships in database
    users: List["User"] = Relationship(back_populates="workspace") # One workspace can contain many users
    birthdays: List["Birthday"] = Relationship(back_populates="workspace") # One workspace can host many birthday entries