# app/routes/workspace_route.py

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.core.db import get_session
from app.models.workspace_model import Workspace
from app.schemas.workspace_schema import WorkspaceRead, WorkspaceCreate, WorkspaceUpdate
from app.services.auth_service import current_superuser

router = APIRouter(
    prefix="/workspaces",
    tags=["workspaces"],
)

# ─── Public endpoints ──────────────────────────────────────────────────────────

@router.get(
    "/",
    response_model=List[WorkspaceRead],
    summary="List all workspaces",
)
def list_workspaces(
    session: Session = Depends(get_session),
):
    """
    Anyone (no auth required) can list all workspaces.
    """
    stmt = select(Workspace)
    return session.exec(stmt).all()


@router.get(
    "/{workspace_id}",
    response_model=WorkspaceRead,
    summary="Get a single workspace",
)
def get_workspace(
    workspace_id: UUID,
    session: Session = Depends(get_session),
):
    """
    Anyone (no auth required) can fetch details of a single workspace.
    """
    ws = session.get(Workspace, workspace_id)
    if not ws:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Workspace not found")
    return ws


# ─── Superuser-only endpoints ─────────────────────────────────────────────────

@router.post(
    "/",
    response_model=WorkspaceRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new workspace",
    dependencies=[Depends(current_superuser)],
)
def create_workspace(
    payload: WorkspaceCreate,
    session: Session = Depends(get_session),
):
    """
    Only superusers can create a workspace.
    """
    ws = Workspace.from_orm(payload)
    session.add(ws)
    session.commit()
    session.refresh(ws)
    return ws


@router.put(
    "/{workspace_id}",
    response_model=WorkspaceRead,
    summary="Update a workspace",
    dependencies=[Depends(current_superuser)],
)
def update_workspace(
    workspace_id: UUID,
    payload: WorkspaceUpdate,
    session: Session = Depends(get_session),
):
    """
    Only superusers can update a workspace.
    """
    ws = session.get(Workspace, workspace_id)
    if not ws:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Workspace not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(ws, k, v)
    session.add(ws)
    session.commit()
    session.refresh(ws)
    return ws


@router.delete(
    "/{workspace_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a workspace",
    dependencies=[Depends(current_superuser)],
)
def delete_workspace(
    workspace_id: UUID,
    session: Session = Depends(get_session),
):
    """
    Only superusers can delete a workspace.
    """
    ws = session.get(Workspace, workspace_id)
    if not ws:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Workspace not found")
    session.delete(ws)
    session.commit()
    return
