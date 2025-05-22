# app/routers/utils.py
print("DEBUG – imported utils.py from:", __file__)

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session, select

from app.db import get_session
from app.models import Workspace
from app.services.slack import post_birthday_message
from app.services.scheduler import birthday_job

router = APIRouter(prefix="/utils", tags=["utils"])


# ── Workspace partial‐update schema ───────────────────────────────────
class WorkspaceUpdate(BaseModel):
    name: Optional[str] = None
    slack_webhook: Optional[str] = None
    timezone: Optional[str] = None

    class Config:
        orm_mode = True


# ── 1. Slack connectivity test ───────────────────────────────────────
@router.post("/ping-slack", status_code=202)
def ping_slack():
    """
    Send a quick test message to the workspace Slack channel.
    """
    post_birthday_message("👋 Birthday Buddy is connected and ready to party! 🎂")
    return {"detail": "Sent"}


# ── 2. Manual trigger for today's-birthday job ───────────────────────
@router.post("/run-birthday-job", status_code=202)
def run_job_now():
    """
    Force-run the daily birthday job (dev utility).
    """
    print("DEBUG – run-birthday-job was called")
    birthday_job()
    return {"detail": "Job executed"}


# ── 3. Create a workspace with webhook & timezone ────────────────────
@router.post("/workspaces", response_model=Workspace, status_code=201)
def create_workspace(
    ws: Workspace, session: Session = Depends(get_session)
):
    """
    Register a new workspace. Provide:
        {
          "name": "Demo Team",
          "slack_webhook": "...",
          "timezone": "America/New_York"
        }
    """
    session.add(ws)
    session.commit()
    session.refresh(ws)
    return ws


# ── 4. List all workspaces ───────────────────────────────────────────
@router.get("/workspaces", response_model=List[Workspace])
def list_workspaces(session: Session = Depends(get_session)):
    """
    Return all registered workspaces.
    """
    return session.exec(select(Workspace)).all()


# ── 5. Partial‐update a workspace ────────────────────────────────────
@router.patch("/workspaces/{workspace_id}", response_model=Workspace)
def update_workspace(
    workspace_id: uuid.UUID,
    ws_update: WorkspaceUpdate,
    session: Session = Depends(get_session),
):
    """
    Update one or more fields of a workspace.
    """
    workspace = session.get(Workspace, workspace_id)
    if not workspace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")

    update_data = ws_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(workspace, field, value)

    session.add(workspace)
    session.commit()
    session.refresh(workspace)
    return workspace


# ── 6. Delete a workspace ────────────────────────────────────────────
@router.delete("/workspaces/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workspace(
    workspace_id: uuid.UUID,
    session: Session = Depends(get_session),
):
    """
    Permanently remove a workspace.
    """
    workspace = session.get(Workspace, workspace_id)
    if not workspace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")

    session.delete(workspace)
    session.commit()
    # 204 No Content
    return
