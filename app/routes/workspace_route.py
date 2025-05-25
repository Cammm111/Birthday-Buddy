# app/routes/workspace_route.py

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.core.db import get_session
from app.models.workspace_model import Workspace
from app.schemas.workspace_schema import WorkspaceRead, WorkspaceCreate, WorkspaceUpdate
from app.services.auth_service import current_superuser

router = APIRouter(prefix="/workspaces", tags=["workspaces"])

@router.get(
    "/",
    response_model=List[WorkspaceRead],
    summary="List all workspaces  (Auth: public)",
    description="Anyone (no authentication required) can list all workspaces."
)
def list_workspaces(
    session: Session = Depends(get_session),
):
    return session.exec(select(Workspace)).all()

@router.post(
    "/",
    response_model=WorkspaceRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(current_superuser)],
    summary="Create a workspace  (Auth: superuser)",
    description="Only superusers may create new workspaces."
)
def create_workspace(
    payload: WorkspaceCreate,
    session: Session = Depends(get_session),
):
    ws = Workspace.from_orm(payload)
    session.add(ws)
    session.commit()
    session.refresh(ws)
    return ws

@router.patch(
    "/{workspace_id}",
    response_model=WorkspaceRead,
    dependencies=[Depends(current_superuser)],
    summary="Partially update a workspace  (Auth: superuser)",
    description="Only superusers may modify existing workspaces."
)
def patch_workspace(
    workspace_id: UUID,
    payload: WorkspaceUpdate,
    session: Session = Depends(get_session),
):
    ws = session.get(Workspace, workspace_id)
    if not ws:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Workspace not found")
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(ws, k, v)
    session.add(ws)
    session.commit()
    session.refresh(ws)
    return ws

@router.delete(
    "/{workspace_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(current_superuser)],
    summary="Delete a workspace  (Auth: superuser)",
    description="Only superusers may delete a workspace."
)
def delete_workspace(
    workspace_id: UUID,
    session: Session = Depends(get_session),
):
    ws = session.get(Workspace, workspace_id)
    if not ws:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Workspace not found")
    session.delete(ws)
    session.commit()
    return
