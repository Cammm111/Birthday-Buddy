import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from app.db import get_session
from app.models import User, UserRead, UserUpdate
from app.auth import current_active_user, current_superuser

router = APIRouter(prefix="/users", tags=["users"])

# 1. List users in the current user's workspace
@router.get(
    "/",
    response_model=List[UserRead],
    summary="List all users in your workspace",
)
def read_workspace_users(
    current_user: User = Depends(current_active_user),
    session: Session = Depends(get_session),
):
    stmt = select(User).where(User.workspace_id == current_user.workspace_id)
    users = session.exec(stmt).all()
    return users

# 2. List ALL users (superuser-only)
@router.get(
    "/all",
    response_model=List[UserRead],
    summary="List all users (superuser only)",
    dependencies=[Depends(current_superuser)],
)
def read_all_users(session: Session = Depends(get_session)):
    users = session.exec(select(User)).all()
    return users

# 3. Update user in the workspace
@router.patch(
    "/{user_id}",
    response_model=UserRead,
    summary="Update a user in your workspace",
)
def update_user(
    user_id: uuid.UUID,
    user_update: UserUpdate,
    current_user: User = Depends(current_active_user),
    session: Session = Depends(get_session),
):
    user = session.get(User, user_id)
    if not user or user.workspace_id != current_user.workspace_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found or unauthorized")
    update_data = user_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

# 4. Delete user in the workspace
@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a user in your workspace",
)
def delete_user(
    user_id: uuid.UUID,
    current_user: User = Depends(current_active_user),
    session: Session = Depends(get_session),
):
    user = session.get(User, user_id)
    if not user or user.workspace_id != current_user.workspace_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found or unauthorized")
    session.delete(user)
    session.commit()
    return None  # Explicit for FastAPI/Swagger docs

# (Optional improvement) Superuser-only: create user in any workspace
@router.post(
    "/",
    response_model=UserRead,
    summary="Create a new user in your workspace",
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    user_data: UserUpdate,  # Change to UserCreate if you prefer
    current_user: User = Depends(current_active_user),
    session: Session = Depends(get_session),
):
    # Ensure email uniqueness in the workspace
    stmt = select(User).where(
        User.email == user_data.email,
        User.workspace_id == current_user.workspace_id
    )
    existing = session.exec(stmt).first()
    if existing:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Email already exists in workspace")
    user = User(
        email=user_data.email,
        hashed_password="PLACEHOLDER_HASH",  # Replace with actual password hashing
        workspace_id=current_user.workspace_id,
        is_active=True,
        is_superuser=False,
        is_verified=False,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user
