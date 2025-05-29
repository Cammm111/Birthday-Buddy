# app/routes/workspace_route.py

from __future__ import annotations
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlmodel import Session
from app.core.db import get_session
from app.schemas.workspace_schema import WorkspaceCreate, WorkspaceRead, WorkspaceUpdate
from app.services import workspace_service as wsvc
from app.services.auth_service import current_superuser

# ─────────────────────────────Define router─────────────────────────────
router = APIRouter(prefix="/workspaces", tags=["workspaces"])

# ──────────────────────────────GET /workspaces──────────────────────────────
@router.get(
    "/",
    response_model=List[WorkspaceRead],
    status_code=status.HTTP_200_OK,
    summary="List all workspaces (Auth: Public)",
)
def list_workspaces(session: Session = Depends(get_session)) -> List[WorkspaceRead]:
    return wsvc.list_workspaces(session)

# ──────────────────────────────POST /workspaces──────────────────────────────
@router.post(
    "/",
    response_model=WorkspaceRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(current_superuser)],
    summary="Create a workspace (Auth: Admin)",
)
def create_workspace(
    payload: WorkspaceCreate,
    session: Session = Depends(get_session),) -> WorkspaceRead:
    return wsvc.create_workspace(session, payload)

# ──────────────────────────────PATCH /workspaces/{workspace_id}──────────────────────────────
@router.patch(
    "/{workspace_id}",
    response_model=WorkspaceRead,
    dependencies=[Depends(current_superuser)],
    summary="Update a workspace (Auth: Admin)",
)
def patch_workspace(
    workspace_id: UUID,
    payload: WorkspaceUpdate,
    session: Session = Depends(get_session),) -> WorkspaceRead:
    try:
        return wsvc.update_workspace(session, workspace_id, payload)
    except KeyError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Workspace not found")

# ──────────────────────────────DELETE /workspaces{workspace_id}──────────────────────────────
@router.delete(
    "/{workspace_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,            
    dependencies=[Depends(current_superuser)],
    summary="Delete a workspace (Auth: Admin)",
)
def delete_workspace(
    workspace_id: UUID,
    session: Session = Depends(get_session),
) -> Response: 
    try:
        wsvc.delete_workspace(session, workspace_id)
    except KeyError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)