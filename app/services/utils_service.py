# app/services/utils_service.py

from typing import List, Dict
import logging
from zoneinfo import available_timezones
from sqlmodel import Session, select
from uuid import UUID
from app.models.user_model import User
from app.models.birthday_model import Birthday
from app.services.scheduler_service import birthday_job
from app.services.redis_cache_service import (get_cached_birthdays,invalidate_birthdays_cache,)
from app.services.redis_cache_service import list_all_users_cache

logger = logging.getLogger(__name__)

# ───────────────────────────── Timezones ──────────────────────────────
def get_supported_timezones() -> List[str]:
    return sorted(available_timezones())

# ───────────────────── Sync / Backfill helpers ────────────────────────
def sync_birthday_from_user(session: Session, user: User) -> None:
    birthday = session.exec(
        select(Birthday).where(Birthday.user_id == user.user_id)
    ).first()
    if birthday:
        birthday.name = user.email
        birthday.date_of_birth = user.date_of_birth
        birthday.workspace_id = user.workspace_id
    else:
        session.add(
            Birthday(
                user_id=user.user_id,
                name=user.email,
                date_of_birth=user.date_of_birth,
                workspace_id=user.workspace_id,
            )
        )
    session.commit()

def refresh_birthday_table_from_users(session: Session) -> int:
    """Return # of rows updated."""
    updated = 0
    birthdays = session.exec(select(Birthday)).all()
    for bd in birthdays:
        user = session.get(User, bd.user_id)
        if user:
            sync_birthday_from_user(session, user)
            updated += 1
    return updated

def backfill_birthdays(session: Session) -> int:
    """Return # of new rows created."""
    created = 0
    for user in session.exec(select(User)):          # pull all users
        exists = session.exec(
            select(Birthday).where(Birthday.user_id == user.user_id)
        ).first()
        if not exists:
            sync_birthday_from_user(session, user)
            created += 1
    return created

# ──────────────────────── Job & Cache helpers ────────────────────────
def run_birthday_job() -> None:
    birthday_job()
    logger.info("Triggered on-demand birthday job")

def inspect_birthday_cache(user_id: UUID) -> Dict:
    cached = get_cached_birthdays(user_id)
    return {"user_id": str(user_id), "cached": cached or None}

def clear_birthday_cache(user_id: UUID) -> None:
    invalidate_birthdays_cache(user_id)

def get_all_users_cache(include_values: bool = True):
    return list_all_users_cache(include_values=include_values)