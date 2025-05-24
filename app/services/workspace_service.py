# app/services/workspace_service.py

from typing import List, Optional
from uuid import UUID
from sqlmodel import Session, select

from app.models.workspace_model import Workspace
from app.schemas.workspace_schema import WorkspaceCreate, WorkspaceUpdate

def list_workspaces(session: Session) -> List[Workspace]:
    """
    Return all workspaces.
    """
    stmt = select(Workspace)
    return session.exec(stmt).all()

def get_workspace(
    session: Session,
    workspace_id: UUID
) -> Optional[Workspace]:
    """
    Retrieve a single workspace by its ID.
    """
    return session.get(Workspace, workspace_id)

def create_workspace(
    session: Session,
    payload: WorkspaceCreate
) -> Workspace:
    """
    Create a new workspace.
    """
    ws = Workspace.from_orm(payload)
    session.add(ws)
    session.commit()
    session.refresh(ws)
    return ws

def update_workspace(
    session: Session,
    workspace_id: UUID,
    payload: WorkspaceUpdate
) -> Optional[Workspace]:
    """
    Update fields of an existing workspace.
    """
    ws = session.get(Workspace, workspace_id)
    if not ws:
        return None
    update_data = payload.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(ws, field, value)
    session.add(ws)
    session.commit()
    session.refresh(ws)
    return ws

def delete_workspace(
    session: Session,
    workspace_id: UUID
) -> bool:
    """
    Delete a workspace by ID.
    Returns True if deleted, False otherwise.
    """
    ws = session.get(Workspace, workspace_id)
    if not ws:
        return False
    session.delete(ws)
    session.commit()
    return True
