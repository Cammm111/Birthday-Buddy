# app/services/user_service.py

from typing import List, Optional
from uuid import UUID
from sqlmodel import Session, select
from passlib.context import CryptContext

from app.models.user_model import User
from app.schemas.user_schema import UserCreate, UserRead, UserUpdate

# Password hasher for user creation and updates
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_user(
    session: Session,
    payload: UserCreate
) -> User:
    """
    Create a new user with a hashed password.
    """
    hashed_password = pwd_context.hash(payload.password)
    user = User(
        email=payload.email,
        hashed_password=hashed_password,
        is_active=True,
        is_superuser=False,
        is_verified=False,
        workspace_id=payload.workspace_id
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

def list_users(
    session: Session
) -> List[User]:
    """
    Return all users.
    """
    stmt = select(User)
    return session.exec(stmt).all()

def get_user(
    session: Session,
    user_id: UUID
) -> Optional[User]:
    """
    Retrieve a single user by ID.
    """
    return session.get(User, user_id)

def update_user(
    session: Session,
    user_id: UUID,
    payload: UserUpdate
) -> Optional[User]:
    """
    Update fields of an existing user.
    """
    user = session.get(User, user_id)
    if not user:
        return None
    update_data = payload.dict(exclude_unset=True)
    # Handle password change
    if "password" in update_data:
        update_data["hashed_password"] = pwd_context.hash(update_data.pop("password"))
    for field, value in update_data.items():
        setattr(user, field, value)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

def delete_user(
    session: Session,
    user_id: UUID
) -> bool:
    """
    Delete a user by ID.
    Returns True if deleted, False otherwise.
    """
    user = session.get(User, user_id)
    if not user:
        return False
    session.delete(user)
    session.commit()
    return True
