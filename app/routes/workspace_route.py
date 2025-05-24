# app/routes/workspace_route.py

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.core.db import get_session
from app.schemas.workspace_schema import WorkspaceCreate, WorkspaceRead, WorkspaceUpdate
from app.services.workspace_service import (
    list_workspaces,    # <-- use the plural name
    get_workspace,
    create_workspace,
    update_workspace,
    delete_workspace,
)
from app.services.auth_service import current_superuser

router = APIRouter(
    prefix="/workspaces",
    tags=["workspaces"],
    dependencies=[Depends(current_superuser)],  # superuser only
)

@router.get("/", response_model=List[WorkspaceRead])
def list_workspaces_endpoint(
    session: Session = Depends(get_session),
):
    return list_workspaces(session)

@router.get("/{workspace_id}", response_model=WorkspaceRead)
def get_workspace_endpoint(
    workspace_id: UUID,
    session: Session = Depends(get_session),
):
    ws = get_workspace(session, workspace_id)
    if not ws:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Workspace not found")
    return ws

@router.post("/", response_model=WorkspaceRead, status_code=status.HTTP_201_CREATED)
def create_workspace_endpoint(
    payload: WorkspaceCreate,
    session: Session = Depends(get_session),
):
    return create_workspace(session, payload)

@router.patch("/{workspace_id}", response_model=WorkspaceRead)
def update_workspace_endpoint(
    workspace_id: UUID,
    payload: WorkspaceUpdate,
    session: Session = Depends(get_session),
):
    ws = update_workspace(session, workspace_id, payload)
    if not ws:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Workspace not found")
    return ws

@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workspace_endpoint(
    workspace_id: UUID,
    session: Session = Depends(get_session),
):
    success = delete_workspace(session, workspace_id)
    if not success:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Workspace not found")
    return
