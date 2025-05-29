# app/services/birthday_service.py

import logging
import uuid
from typing import List, Optional
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from app.models.birthday_model import Birthday
from app.models.user_model import User
from app.schemas.birthday_schema import BirthdayCreate, BirthdayUpdate
from app.services.redis_cache_service import (get_cached_birthdays, set_cached_birthdays, invalidate_birthdays_cache,)
logger = logging.getLogger(__name__)

# ─────────────────────────────List birthdays─────────────────────────────
def list_birthdays_by_workspace( # Return all birthdays in workspace_id
    session: Session,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID) -> List[Birthday]:
    cached = get_cached_birthdays(user_id) # Check user‐scoped cache
    if cached is not None:
        return cached

    results = session.exec(select(Birthday).where(Birthday.workspace_id == workspace_id)).all() # Cache miss. Query DB

    set_cached_birthdays(user_id, results) # Store in cache for next time
    return results

# ─────────────────────────────List all birthdays──────────────────────────────
def list_all_birthdays(session: Session) -> List[Birthday]: # Returns every birthday in the database
    
    return session.exec(select(Birthday)).all()

# ─────────────────────────────Create birthday─────────────────────────────
def create_birthday(session: Session, # Create a new Birthday record for a given user
                    user_id: uuid.UUID,
                    payload: BirthdayCreate) -> Birthday:
    
    bday = Birthday(**payload.dict(), user_id=user_id)
    session.add(bday)

    try:
        session.commit()
        session.refresh(bday)
        logger.info("Created birthday id=%s for user_id=%s", bday.id, user_id)
    except IntegrityError:
        session.rollback()
        logger.warning("IntegrityError creating birthday for user_id=%s, payload=%s", user_id, payload.json())
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not create birthday (duplicate or invalid user/workspace)"
        )

    invalidate_birthdays_cache(user_id)
    return bday

# ─────────────────────────────Get birthday─────────────────────────────
def get_birthday(session: Session,
                 user_id: uuid.UUID,
                 bday_id: uuid.UUID) -> Optional[Birthday]:
    
    bday = session.get(Birthday, bday_id) # Retrieve single Birthday by its ID
    if not bday or bday.user_id != user_id: # Verify birthday belongs to the given user
        return None
    return bday

# ─────────────────────────────Update birthdays─────────────────────────────
def update_birthday(session: Session, # Apply updates to a Birthday record
                    user_id: uuid.UUID,
                    bday_id: uuid.UUID,
                    payload: BirthdayUpdate) -> Optional[Birthday]: 

    bday = session.get(Birthday, bday_id)
    if not bday or bday.user_id != user_id: # Returns None if record not found or not owned by user.
        return None

    for field, value in payload.dict(exclude_unset=True).items(): # Only fields set in the payload are updated.
        setattr(bday, field, value)

    try:
        session.commit()
        session.refresh(bday)
        logger.info("Updated birthday id=%s for user_id=%s", bday_id, user_id)
    except Exception:
        session.rollback()
        logger.error("Failed to update birthday id=%s for user_id=%s", bday_id, user_id, exc_info=True)
        raise

    invalidate_birthdays_cache(user_id) # Clears cache on success
    return bday

# ─────────────────────────────Delete birthdays─────────────────────────────
def delete_birthday(session: Session, # Delete a Birthday record
                    user: User,
                    bday_id: uuid.UUID) -> bool:
    
    bday = session.get(Birthday, bday_id)
    if not bday:
        return False
    
    if not user.is_superuser and bday.user_id != user.user_id: # If not an admin, only allow deleting your own record
        return False 

    session.delete(bday)
    try:
        session.commit()
        logger.info("Deleted birthday id=%s by user_id=%s", bday_id, user.user_id)
    except Exception:
        session.rollback()
        logger.error("Failed to delete birthday id=%s by user_id=%s", bday_id, user.user_id, exc_info=True)
        raise
    finally:
        invalidate_birthdays_cache(user.user_id)
    return True

# ─────────────────────────────Sync birthday from user─────────────────────────────
def sync_birthday_from_user(session: Session,
                            user: User) -> None: # Ensure Birthday table stays in sync with User records. If a birthday exists for a user, update its fields. Otherwise, create a new Birthday entry.
    birthday = session.exec(select(Birthday).where(Birthday.user_id == user.user_id)).first()
    if birthday: # Update existing Birthday fields to match the User
        birthday.name = user.email  
        birthday.date_of_birth = user.date_of_birth
        birthday.workspace_id = user.workspace_id
        logger.info("Updating birthday for user_id=%s", user.user_id)

    else:
        birthday = Birthday( # No existing records. Create a fresh one
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
        logger.error(
            "Failed to sync birthday for user_id=%s", user.user_id, exc_info=True)
        raise