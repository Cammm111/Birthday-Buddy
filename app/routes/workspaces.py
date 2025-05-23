# app/routers/workspaces.py

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.db import engine
from app.models import Workspace
from app.schemas import WorkspaceCreate, WorkspaceRead, WorkspaceUpdate
from app.auth import current_superuser

router = APIRouter(
    prefix="/workspaces",
    tags=["workspaces"],
    dependencies=[Depends(current_superuser)],  # superuser only
)

@router.get("/", response_model=List[WorkspaceRead])
def read_workspaces():
    """
    List all workspaces. Superuser only.
    """
    with Session(engine) as session:
        workspaces = session.exec(select(Workspace)).all()
    return workspaces

@router.get("/{workspace_id}", response_model=WorkspaceRead)
def read_workspace(workspace_id: UUID):
    """
    Get a single workspace by ID. Superuser only.
    """
    with Session(engine) as session:
        ws = session.get(Workspace, workspace_id)
    if not ws:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )
    return ws

@router.post("/", response_model=WorkspaceRead, status_code=status.HTTP_201_CREATED)
def create_workspace(workspace: WorkspaceCreate):
    """
    Create a new workspace. Superuser only.
    """
    db_ws = Workspace.from_orm(workspace)
    with Session(engine) as session:
        session.add(db_ws)
        session.commit()
        session.refresh(db_ws)
    return db_ws

@router.patch("/{workspace_id}", response_model=WorkspaceRead)
def update_workspace(workspace_id: UUID, workspace_in: WorkspaceUpdate):
    """
    Update an existing workspace. Superuser only.
    """
    with Session(engine) as session:
        db_ws = session.get(Workspace, workspace_id)
        if not db_ws:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace not found"
            )
        updates = workspace_in.dict(exclude_unset=True)
        for field, value in updates.items():
            setattr(db_ws, field, value)
        session.add(db_ws)
        session.commit()
        session.refresh(db_ws)
    return db_ws

@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workspace(workspace_id: UUID):
    """
    Delete a workspace. Superuser only.
    """
    with Session(engine) as session:
        db_ws = session.get(Workspace, workspace_id)
        if not db_ws:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace not found"
            )
        session.delete(db_ws)
        session.commit()
    return None
