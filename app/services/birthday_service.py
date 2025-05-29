# app/services/birthday_service.py

from __future__ import annotations
import logging
from typing import List
from uuid import UUID
from fastapi import HTTPException, status
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError
from redis.exceptions import RedisError
from app.models.user_model import User
from app.models.birthday_model import Birthday
from app.services.redis_cache_service import (get_cached_birthdays_all, set_cached_birthdays_all, invalidate_birthdays_all, get_cached_birthdays_by_workspace, set_cached_birthdays_by_workspace, invalidate_birthdays_by_workspace,)
logger = logging.getLogger(__name__)


# ─────────────────────────────List birthdays─────────────────────────────
def list_birthdays_by_workspace(session: Session, # Return birthdays for single workspace
                                workspace_id: UUID) -> List[Birthday]:
    try:
        cached = get_cached_birthdays_by_workspace(workspace_id) # Try cache
    except RedisError as e:
        logger.warning("Redis GET error for birthdays by workspace %s, skipping cache: %s", workspace_id, e,)
        cached = None

    if cached is not None:
        logger.debug("list_birthdays_by_workspace: cache hit for %s", workspace_id)
        return [Birthday.parse_obj(d) for d in cached]

    birthdays = session.exec(select(Birthday).where(Birthday.workspace_id == workspace_id)).all() # Hit database

    try:
        set_cached_birthdays_by_workspace(workspace_id, birthdays) # Populate cache
    except RedisError as e:
        logger.warning("Redis SET error for birthdays by workspace %s: %s", workspace_id, e)

    return birthdays

# ─────────────────────────────List all birthdays──────────────────────────────
def list_all_birthdays(session: Session) -> List[Birthday]: # Returns every birthday in the database
    try:
        cached = get_cached_birthdays_all() # Try cache
    except RedisError as e:
        logger.warning("Redis GET error for all birthdays, skipping cache: %s", e)
        cached = None

    if cached is not None:
        logger.debug("list_birthdays: cache hit")
        return [Birthday.parse_obj(d) for d in cached]

    birthdays = session.exec(select(Birthday)).all() # Hit database

    try:
        set_cached_birthdays_all(birthdays)  # Populate cache
    except RedisError as e:
        logger.warning("Redis SET error for all birthdays: %s", e)

    return birthdays

# ─────────────────────────────Get birthday─────────────────────────────
def get_birthday(session: Session, # Fetch a single Birthday by ID directly from the DB (no cache)
                 birthday_id: UUID) -> Birthday:
    birthday = session.get(Birthday, birthday_id)
    if not birthday:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Birthday not found")
    return birthday

# ─────────────────────────────Create birthday─────────────────────────────
def create_birthday(session: Session, # Create a new birthday
                    birthday: Birthday) -> Birthday:
    session.add(birthday)
    try:
        session.commit()
        session.refresh(birthday)
        logger.info("Created birthday %s", birthday.id)

        try:
            invalidate_birthdays_all() # Invalidate both caches
            if birthday.workspace_id:
                invalidate_birthdays_by_workspace(birthday.workspace_id)
        except RedisError as e:
            logger.warning("Redis invalidate error after create_birthday: %s", e)

        return birthday

    except IntegrityError:
        session.rollback()
        logger.exception("Integrity error creating birthday")
        raise HTTPException(status.HTTP_400_BAD_REQUEST,"Could not create birthday (invalid data or conflict)",)

# ─────────────────────────────Update birthdays─────────────────────────────
def update_birthday(session: Session, # Update an existing birthday
                    birthday_id: UUID,
                    data: dict) -> Birthday:
    birthday = session.get(Birthday, birthday_id)
    if not birthday:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Birthday not found")

    for field, value in data.items():
        setattr(birthday, field, value)

    try:
        session.commit()
        session.refresh(birthday)
        logger.info("Updated birthday %s", birthday.id)

        try:
            invalidate_birthdays_all()
            if birthday.workspace_id:
                invalidate_birthdays_by_workspace(birthday.workspace_id)
        except RedisError as e:
            logger.warning("Redis invalidate error after update_birthday: %s", e)

        return birthday

    except IntegrityError:
        session.rollback()
        logger.exception("Integrity error updating birthday %s", birthday_id)
        raise HTTPException(status.HTTP_400_BAD_REQUEST,"Could not update birthday (invalid data or conflict)",)

# ─────────────────────────────Delete birthdays─────────────────────────────
def delete_birthday(session: Session, # Delete a birthday
                    birthday_id: UUID) -> None:
    birthday = session.get(Birthday, birthday_id)
    if not birthday:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Birthday not found")

    workspace_id = birthday.workspace_id

    try:
        session.delete(birthday)
        session.commit()
        logger.info("Deleted birthday %s", birthday_id)

        try:
            invalidate_birthdays_all()
            if workspace_id:
                invalidate_birthdays_by_workspace(workspace_id)
        except RedisError as e:
            logger.warning("Redis invalidate error after delete_birthday: %s", e)

    except IntegrityError:
        session.rollback()
        logger.exception("Integrity error deleting birthday %s", birthday_id)
        raise HTTPException(status.HTTP_400_BAD_REQUEST,"Could not delete birthday (integrity error)",)

# ─────────────────────────────Sync birthday from user─────────────────────────────
def sync_birthday_from_user(session: Session, # Ensure Birthday table mirrors the User record
                            user: User) -> None:
    birthday = session.exec(select(Birthday).where(Birthday.user_id == user.user_id)).first()

    if birthday:
        birthday.name = user.email
        birthday.date_of_birth = user.date_of_birth
        birthday.workspace_id = user.workspace_id
        logger.info("Updating birthday for user_id=%s", user.user_id)
    else:
        birthday = Birthday(
            user_id=user.user_id,
            name=user.email,
            date_of_birth=user.date_of_birth,
            workspace_id=user.workspace_id,
        )
        session.add(birthday)
        logger.info("Creating birthday for user_id=%s", user.user_id)

    try:
        session.commit()
    except Exception:
        session.rollback()
        logger.error("Failed to sync birthday for user_id=%s", user.user_id, exc_info=True)
        raise

    try:
        invalidate_birthdays_all() # Invalidate caches so next list_all_birthdays calls repopulate
    except RedisError as e:
        logger.warning("Redis DELETE error invalidating all-birthdays cache: %s", e)

    if user.workspace_id:
        try:
            invalidate_birthdays_by_workspace(user.workspace_id)  #Only invalidate the per-workspace cache if the user has one
        except RedisError as e:
            logger.warning("Redis DELETE error invalidating birthdays-by-workspace cache for %s: %s",user.workspace_id,e,)