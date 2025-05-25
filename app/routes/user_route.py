# app/routes/user_route.py

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from passlib.context import CryptContext
from sqlmodel import Session, select

from app.core.db import get_session
from app.models.user_model import User
from app.models.birthday_model import Birthday
from app.schemas.user_schema import UserRead, UserUpdate
from app.services.auth_service import current_active_user, current_superuser

router = APIRouter(
    prefix="/users",
    tags=["users"],
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.get(
    "/",
    response_model=List[UserRead],
    summary="List users in your workspace  (Auth: any active user)",
    description="Returns all users belonging to the authenticated user's workspace."
)
def list_users(
    session: Session = Depends(get_session),
    user=Depends(current_active_user),
):
    stmt = select(User).where(User.workspace_id == user.workspace_id)
    return session.exec(stmt).all()

@router.get(
    "/all",
    response_model=List[UserRead],
    dependencies=[Depends(current_superuser)],
    summary="List all users  (Auth: superuser)",
    description="Returns every user in the system, regardless of workspace."
)
def list_all_users(
    session: Session = Depends(get_session),
):
    stmt = select(User)
    return session.exec(stmt).all()

@router.patch(
    "/{user_id}",
    response_model=UserRead,
    summary="Update a user  (Auth: self or superuser)",
    description=(
        "General users may only update their own account; superusers may update any user. "
        "Syncs all associated birthday fields from the updated user."
    ),
    openapi_extra={
        "requestBody": {
            "content": {
                "application/json": {
                    "example": {}
                }
            }
        }
    },
)
def patch_user(
    user_id: UUID,
    payload: UserUpdate,
    session: Session = Depends(get_session),
    user=Depends(current_active_user),
):
    target = session.get(User, user_id)
    if not target:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

    if not user.is_superuser and user.id != user_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Cannot modify other users")

    data = payload.dict(exclude_unset=True)

    # Update password if provided
    if "password" in data:
        raw_pw = data.pop("password")
        target.hashed_password = pwd_context.hash(raw_pw)

    # Apply all updatable fields (except password)
    for field, value in data.items():
        setattr(target, field, value)

    session.add(target)
    session.commit()
    session.refresh(target)

    # --- Sync ALL fields from User to Birthday for user-linked birthday ---
    birthday_entry = session.exec(
        select(Birthday).where(Birthday.user_id == user_id)
    ).first()
    if birthday_entry:
        # Always sync these fields:
        birthday_entry.name = target.email  # or target.name if you prefer
        birthday_entry.date_of_birth = target.date_of_birth
        birthday_entry.workspace_id = target.workspace_id
        # Add any other mirrored fields here if needed!
        session.add(birthday_entry)
        session.commit()

    # Optionally, if no birthday exists but DOB is present, create it:
    elif target.date_of_birth:
        birthday_entry = Birthday(
            user_id=target.id,
            name=target.email,  # or target.name if you add that
            date_of_birth=target.date_of_birth,
            workspace_id=target.workspace_id,
        )
        session.add(birthday_entry)
        session.commit()

    return target


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(current_superuser)],
    summary="Delete a user  (Auth: superuser)",
    description="Remove any user by ID. Superusers only."
)
def delete_user(
    user_id: UUID,
    session: Session = Depends(get_session),
):
    target = session.get(User, user_id)
    if not target:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    session.delete(target)
    session.commit()
    return
