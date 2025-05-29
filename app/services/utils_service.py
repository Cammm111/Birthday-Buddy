# app/services/utils_service.py

from __future__ import annotations
from app.services import redis_cache_service as cache
import logging
from typing import List
from zoneinfo import available_timezones
from sqlmodel import Session, select
from app.models.user_model import User
from app.models.birthday_model import Birthday
from app.services.scheduler_service import birthday_job
from app.schemas.utils_schema import (JobResult, CountResult,CacheResult,)
logger = logging.getLogger(__name__)

# ─────────────────────────────Get Timezones──────────────────────────────
def get_supported_timezones() -> List[str]:
    return sorted(available_timezones())

# ─────────────────────Sync birthday from user────────────────────────
def sync_birthday_from_user(session: Session, # Build birthday if info exists in user
                            user: User) -> None:
    birthday = session.exec(select(Birthday).where(Birthday.user_id == user.user_id)).first()
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
                workspace_id=user.workspace_id,))
    session.commit()

# ─────────────────────Refresh birthday db from user────────────────────────
def refresh_birthday_table_from_users(session: Session) -> CountResult: # Return # of rows updated
    updated = 0
    for bd in session.exec(select(Birthday)).all():
        user = session.get(User, bd.user_id)
        if user:
            sync_birthday_from_user(session, user)
            updated += 1
    return CountResult(count=updated) 

# ─────────────────────Backfill birthday────────────────────────
def backfill_birthdays(session: Session) -> CountResult: # Return # of new rows created.
    created = 0
    for user in session.exec(select(User)): # Pull all users
        exists = session.exec(select(Birthday).where(Birthday.user_id == user.user_id)).first()
        if not exists:
            sync_birthday_from_user(session, user)
            created += 1
    return CountResult(count=created)  

# ────────────────────────Run birthday job manually────────────────────────
def run_birthday_job() -> JobResult:
    birthday_job()
    logger.info("Triggered manual birthday job")
    return JobResult(detail="Birthday job triggered")

# ──────────────────────── Job Cache helpers ────────────────────────
def get_entire_cache() -> CacheResult: # Return the whole cache blob (users, birthdays, workspaces)
    return CacheResult(
        data={
            "users":      cache.get_cached_users_all(),
            "birthdays":  cache.get_cached_birthdays_all(),
            "workspaces": cache.get_cached_workspaces(),
        }
    )

def get_cached_birthdays() -> CacheResult:
    return CacheResult(data=cache.get_cached_birthdays_all())

def get_cached_users() -> CacheResult:
    return CacheResult(data=cache.get_cached_users_all())

def get_cached_workspaces() -> CacheResult:
    return CacheResult(data=cache.get_cached_workspaces())