from typing import Optional, List
from uuid import UUID
from sqlmodel import Session, select
from passlib.context import CryptContext
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.models.user_model import User
from app.models.birthday_model import Birthday
from app.schemas.user_schema import UserCreate, UserUpdate

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

def update_user(session: Session, user_id: UUID, payload: UserUpdate) -> Optional[User]:
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

    update_data = payload.dict(exclude_unset=True)

    if "password" in update_data:
        update_data["hashed_password"] = pwd_context.hash(update_data.pop("password"))

    birthday_fields_updated = any(field in update_data for field in ["email", "name", "date_of_birth", "workspace_id"])

    for field, value in update_data.items():
        setattr(user, field, value)

    session.add(user)
    session.commit()
    session.refresh(user)

    if birthday_fields_updated:
        birthday = session.exec(select(Birthday).where(Birthday.user_id == user_id)).first()
        if birthday:
            birthday.name = user.email
            birthday.date_of_birth = user.date_of_birth
            birthday.workspace_id = user.workspace_id
            session.add(birthday)
            session.commit()
        elif user.date_of_birth:
            birthday = Birthday(
                user_id=user.user_id,
                name=user.email,
                date_of_birth=user.date_of_birth,
                workspace_id=user.workspace_id
            )
            session.add(birthday)
            session.commit()

    return user

def delete_user(session: Session, user_id: UUID) -> bool:
    user = session.get(User, user_id)
    if not user:
        return False
    session.delete(user)
    session.commit()
    return True
