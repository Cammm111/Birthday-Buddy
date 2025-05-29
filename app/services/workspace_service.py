# app/services/workspace_service.py

from __future__ import annotations
import logging
from typing import List
from uuid import UUID
from fastapi import HTTPException, status
from sqlmodel import Session, select, update
from sqlalchemy.exc import IntegrityError
from app.models.birthday_model import Birthday
from app.models.user_model import User
from app.models.workspace_model import Workspace
from app.schemas.workspace_schema import WorkspaceCreate, WorkspaceUpdate
logger = logging.getLogger(__name__)

# ───────────────────────────List workspaces────────────────────────────
def list_workspaces(session: Session) -> List[Workspace]: # Return every workspace
    return session.exec(select(Workspace)).all()

# ─────────────────────────────Create workspace─────────────────────────────
def create_workspace(session: Session, # Insert and return a new workspace
                     payload: WorkspaceCreate,
                     current_user: User) -> Workspace:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create workspaces",)
    
    ws = Workspace.from_orm(payload)
    session.add(ws)
    try:
        session.commit()
        session.refresh(ws)
        logger.info("Workspace %s created", ws.id)
        return ws
    except IntegrityError:
        session.rollback()
        logger.exception("Integrity error creating workspace")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not create workspace (invalid data or conflict)",)

# ─────────────────────────────Update workspace─────────────────────────────
def update_workspace(session: Session, # Apply updates
                     workspace_id: UUID,
                     payload: WorkspaceUpdate,
                     current_user: User) -> Workspace:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update workspaces",)
    
    ws = session.get(Workspace, workspace_id)
    if not ws:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workspace with id={workspace_id} not found")

    for field, value in payload.dict(exclude_unset=True).items():
        setattr(ws, field, value)

    try:
        session.commit()
        session.refresh(ws)
        logger.info("Workspace %s updated", ws.id)
        return ws
    except IntegrityError:
        session.rollback()
        logger.exception("Integrity error updating workspace %s", workspace_id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not update workspace (invalid data or conflict)",)
    
# ─────────────────────────────Delete workspace─────────────────────────────
def delete_workspace(session: Session, # Delete a workspace, null out workspace_id in Birthday table
    workspace_id: UUID,
    current_user: User,) -> None:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete workspaces",)

    ws = session.get(Workspace, workspace_id)
    if not ws:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workspace with id={workspace_id} not found")

    
    try: # Null out workspace_id in Birthday table
        session.exec(
        update(Birthday)
        .where(Birthday.workspace_id == workspace_id)
        .values(workspace_id=None)
        )
        session.delete(ws)
        session.commit()
        logger.info("Workspace %s deleted; orphaned birthdays updated", workspace_id)
    except IntegrityError:
        session.rollback()
        logger.exception("Integrity error deleting workspace %s", workspace_id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not delete workspace (integrity error)",)