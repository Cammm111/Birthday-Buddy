# app/services/user_service.py

from typing import Optional, List
from uuid import UUID
from sqlmodel import Session, select
from passlib.context import CryptContext
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.models.user_model import User
from app.models.birthday_model import Birthday
from app.schemas.user_schema import UserCreate, UserUpdate
from app.services.redis_cache_service import invalidate_birthdays_cache

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_user(session: Session, payload: UserCreate) -> User:
    if payload.date_of_birth is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="date_of_birth is required",
        )

    user = User(
        email=payload.email,
        hashed_password=pwd_context.hash(payload.password),
        date_of_birth=payload.date_of_birth,
        workspace_id=payload.workspace_id,
    )
    session.add(user)
    try:
        session.commit()
        session.refresh(user)
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not create user (email may exist or workspace invalid)",
        )
    return user

def list_users(session: Session) -> List[User]:
    stmt = select(User)
    return session.exec(stmt).all()

def get_user(session: Session, user_id: UUID) -> Optional[User]:
    return session.get(User, user_id)

def update_user(
    session: Session,
    current_user: User,
    target_user_id: UUID,
    payload: UserUpdate
) -> Optional[User]:
    # Fetch the target user record
    user_obj = session.get(User, target_user_id)
    if not user_obj:
        return None

    # Permission check: either the user themself or a superuser
    if not current_user.is_superuser and current_user.user_id != target_user_id:
        return None

    # Determine which fields have changed for birthday sync
    update_data = payload.dict(exclude_unset=True)
    birthday_fields_updated = any(
        f in update_data for f in ("email", "name", "date_of_birth", "workspace_id")
    )

    # Handle password hashing if password is being updated
    if "password" in update_data:
        update_data["hashed_password"] = pwd_context.hash(update_data.pop("password"))

    # Apply all updates to the user object
    for field, val in update_data.items():
        setattr(user_obj, field, val)

    session.add(user_obj)
    session.commit()
    session.refresh(user_obj)

    # Sync or create the corresponding Birthday record if relevant fields changed
    if birthday_fields_updated:
        bday = session.exec(
            select(Birthday).where(Birthday.user_id == target_user_id)
        ).first()
        if bday:
            bday.name = user_obj.email
            bday.date_of_birth = user_obj.date_of_birth
            bday.workspace_id = user_obj.workspace_id
            session.add(bday)
            session.commit()
        else:
            bday = Birthday(
                user_id=target_user_id,
                name=user_obj.email,
                date_of_birth=user_obj.date_of_birth,
                workspace_id=user_obj.workspace_id
            )
            session.add(bday)
            session.commit()

        # Invalidate Redis cache for this user's birthdays
        invalidate_birthdays_cache(target_user_id)

    return user_obj

def delete_user(session: Session, user_id: UUID) -> bool:
    user = session.get(User, user_id)
    if not user:
        return False
    session.delete(user)
    session.commit()
    return True
