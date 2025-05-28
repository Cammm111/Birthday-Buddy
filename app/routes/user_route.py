# app/route/user_route.py

from uuid import UUID
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from app.core.db import get_session
from app.models.user_model import User
from app.schemas.user_schema import UserRead, UserUpdate
from app.services import user_service
from app.services.auth_service import current_active_user, current_superuser

# ──────────────────────────────────Router definition──────────────────────────────────
router = APIRouter(prefix="/users", tags=["users"]) # Router prefix "/users". Group under "users" in the OpenAPI docs

# ──────────────────────────────────GET /users──────────────────────────────────
@router.get("/",
    response_model=List[UserRead]# Response models defined in user_schema.py
) 
def list_users(session: Session = Depends(get_session),
    user=Depends(current_active_user)):
    stmt = select(User).where(User.workspace_id == user.workspace_id) # Only return users belonging to the current user’s workspace
    return session.exec(stmt).all()

# ──────────────────────────────────GET /users/all──────────────────────────────────
@router.get("/all",
     response_model=List[UserRead],
     dependencies=[Depends(current_superuser)] # Admins only!
)
def list_all_users(session: Session = Depends(get_session)):
    stmt = select(User)
    return session.exec(stmt).all()

# ──────────────────────────────────PATCH /users/{user_id}──────────────────────────────────
@router.patch("/{user_id}",
    response_model=UserRead)
def patch_user(
    user_id: UUID,
    payload: UserUpdate,
    session: Session = Depends(get_session),
    user=Depends(current_active_user),
):
    updated = user_service.update_user(session, user, user_id, payload)
    if not updated:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found or unauthorized")
    return updated

# ──────────────────────────────────DELETE /users/{user_id}──────────────────────────────────
@router.delete("/{user_id}",
     status_code=status.HTTP_204_NO_CONTENT, # No response for deletion
     dependencies=[Depends(current_superuser)] # Admins only!
)
def delete_user(user_id: UUID,
     session: Session = Depends(get_session)
):
    success = user_service.delete_user(session, user_id)
    if not success:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")