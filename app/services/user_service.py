# app/services/user_service.py

import logging
from typing import Optional, List
from uuid import UUID
from sqlmodel import Session, select
from passlib.context import CryptContext
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from redis.exceptions import RedisError
from app.models.user_model import User
from app.models.birthday_model import Birthday
from app.schemas.user_schema import UserCreate, UserUpdate
from app.services.redis_cache_service import ( get_cached_users_all, set_cached_users_all, invalidate_users_cache_all,)
logger = logging.getLogger(__name__)

# ─────────────────────────────Password hasher─────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ─────────────────────────────Birthday Sync Helper─────────────────────────────
def _sync_user_birthday(session: Session, # Ensure there's a birthday record matching this User. Creates/updates the record
                        user_obj: User) -> None: 
    b = session.exec(
        select(Birthday).where(Birthday.user_id == user_obj.user_id)
    ).first()
    if b:
        b.name = user_obj.email
        b.date_of_birth = user_obj.date_of_birth
        b.workspace_id = user_obj.workspace_id
    else:
        b = Birthday(
            user_id=user_obj.user_id,
            name=user_obj.email,
            date_of_birth=user_obj.date_of_birth,
            workspace_id=user_obj.workspace_id,
        )
        session.add(b)
    try:
        session.commit()
    except Exception:
        session.rollback()
        logger.exception("Failed to sync birthday for user %s", user_obj.user_id)

# ─────────────────────────────Return all users─────────────────────────────
def list_users(session: Session) -> List[User]: # Return every user in the system
    try:
        cached = get_cached_users_all() # Try cache
    except RedisError as e:
        logger.warning("Redis GET error in list_users, skipping cache: %s", e)
        cached = None

    if cached is not None:
        logger.debug("list_users: cache hit")
        return [User.parse_obj(d) for d in cached]

    users = session.exec(select(User)).all()  # Hit the database if no cache

    try:
        set_cached_users_all(users) # Populate cache
    except RedisError as e:
        logger.warning("Redis SET error in list_users: %s", e)

    return users

# ─────────────────────────────Get user by id─────────────────────────────
def get_user(session: Session, # Fetch single user by ID directly from the database
             user_id: UUID) -> User:
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    return user

# ─────────────────────────────Create user─────────────────────────────
def create_user(session: Session,
                payload: UserCreate) -> User: # Create a new user. Raises HTTP 422 if date_of_birth is missing, or HTTP 400 on integrity errors
    if payload.date_of_birth is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Date of birth is required",
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
        logger.info("Created user %s", user.user_id)
        try:
            invalidate_users_cache_all()  # Invalidate cache so next list_users() is fresh
        except RedisError as e:
            logger.warning("Redis DELETE error invalidating users cache: %s", e)
        return user
    except IntegrityError:
        session.rollback()
        logger.exception("Integrity error creating user")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not create user (email may exist or workspace invalid)",)



# ─────────────────────────────Update user─────────────────────────────
def update_user(session: Session,
    current_user: User,
    target_user_id: UUID,
    payload: UserUpdate) -> Optional[User]:
    user_obj = session.get(User, target_user_id)
    if not user_obj: # Is a user?
        return None
    if not (current_user.is_superuser or current_user.user_id == target_user_id): # Self or admin
        return None

    data = payload.dict(exclude_unset=True)

    if "password" in data: 
        data["hashed_password"] = pwd_context.hash(data.pop("password")) # Hash new password if provided

    needs_bday_sync = any(f in data for f in ("email", "name", "date_of_birth", "workspace_id"))

    for field, val in data.items(): 
        setattr(user_obj, field, val)  # Apply updates to user

    try:
        session.add(user_obj)
        session.commit()
        session.refresh(user_obj)
        logger.info("Updated user %s", target_user_id)

        try:
            invalidate_users_cache_all() # Invalidate the all-users cache
        except RedisError as e:
            logger.warning("Redis DELETE error invalidating users cache: %s", e)

    except IntegrityError:
        session.rollback()
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Could not update user (invalid data or email conflict)",)

    if needs_bday_sync:
        _sync_user_birthday(session, user_obj)

    return user_obj

# ─────────────────────────────Delete user─────────────────────────────
def delete_user(session: Session, # Delete a user
                user_id: UUID) -> bool:
    user = session.get(User, user_id)
    if not user:
        return False

    session.delete(user)
    try:
        session.commit()
        logger.info("Deleted user %s", user_id)

        try:
            invalidate_users_cache_all() # Invalidate the all-users cache
        except RedisError as e:
            logger.warning("Redis DELETE error invalidating users cache: %s", e)

        return True

    except IntegrityError:
        session.rollback()
        logger.exception("Integrity error deleting user %s", user_id)
        return False
    except Exception:
        session.rollback()
        logger.exception("Unexpected error deleting user %s", user_id)
        return False