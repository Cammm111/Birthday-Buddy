from uuid import UUID
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.core.db import get_session
from app.models.user_model import User
from app.schemas.user_schema import UserRead, UserUpdate
from app.services import user_service
from app.services.auth_service import current_active_user, current_superuser

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/", response_model=List[UserRead])
def list_users(session: Session = Depends(get_session), user=Depends(current_active_user)):
    stmt = select(User).where(User.workspace_id == user.workspace_id)
    return session.exec(stmt).all()

@router.get("/all", response_model=List[UserRead], dependencies=[Depends(current_superuser)])
def list_all_users(session: Session = Depends(get_session)):
    stmt = select(User)
    return session.exec(stmt).all()

@router.patch("/{user_id}", response_model=UserRead)
def patch_user(
    user_id: UUID,
    payload: UserUpdate,
    session: Session = Depends(get_session),
    user=Depends(current_active_user),
):
    if not user.is_superuser and user.user_id != user_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Cannot modify other users")
    return user_service.update_user(session, user_id, payload)

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(current_superuser)])
def delete_user(user_id: UUID, session: Session = Depends(get_session)):
    success = user_service.delete_user(session, user_id)
    if not success:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
