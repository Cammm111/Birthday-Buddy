# app/services/workspace_service.py

from __future__ import annotations
import logging
from typing import List
from uuid import UUID
from fastapi import HTTPException, status
from sqlmodel import Session, select, update
from sqlalchemy.exc import IntegrityError
from redis.exceptions import RedisError
from app.models.birthday_model import Birthday
from app.models.user_model import User
from app.models.workspace_model import Workspace
from app.schemas.workspace_schema import WorkspaceCreate, WorkspaceUpdate
from app.services.redis_cache_service import (get_cached_workspaces, set_cached_workspaces, invalidate_workspaces_cache,)
logger = logging.getLogger(__name__)

# ───────────────────────────List workspaces────────────────────────────
def list_workspaces(session: Session) -> List[Workspace]: # Return every workspace
    try:
        cached = get_cached_workspaces() # Get workspaces cache
    except RedisError as e:
        logger.warning("Redis GET error in list_workspaces, skipping cache: %s", e)
        cached = None

    if cached is not None:
        logger.debug("list_workspaces: cache hit")
        return [Workspace.parse_obj(d) for d in cached] # Deserialize into instances

    workspaces = session.exec(select(Workspace)).all() # Hit database if nothing in cache

    try:
        set_cached_workspaces(workspaces) # Populate Redis cache for next list
    except RedisError as e:
        logger.warning("Redis SET error in list_workspaces: %s", e)
    return workspaces

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
        
        try:
            invalidate_workspaces_cache() # Clear stale cache
        except RedisError as e:
            logger.warning("Redis DELETE error in create_workspace: %s", e)
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

    for field, value in payload.model_dump(exclude_unset=True, mode="json").items():
        setattr(ws, field, value)

    try:
        session.commit()
        session.refresh(ws)
        logger.info("Workspace %s updated", ws.id)
        try:
            invalidate_workspaces_cache()
        except RedisError as e:
            logger.warning("Redis DELETE error in update_workspace: %s", e)
        
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
        try:
            invalidate_workspaces_cache()
        except RedisError as e:
            logger.warning("Redis DELETE error in delete_workspace: %s", e)
        
    except IntegrityError:
        session.rollback()
        logger.exception("Integrity error deleting workspace %s", workspace_id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not delete workspace (integrity error)",)