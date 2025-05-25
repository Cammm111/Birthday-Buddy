# app/routes/utils_route.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlmodel import Session, select
import pytz

from app.core.db import get_session
from app.models.user_model import User
from app.models.birthday_model import Birthday
from app.services.scheduler_service import birthday_job
from app.services.auth_service import current_superuser
from uuid import UUID
from app.services.redis_cache_service import get_cached_birthdays, invalidate_birthdays_cache

import logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/utils", tags=["utils"])

# ─── Utility: Sync Birthday from User ──────────────────────────────────────────

def sync_birthday_from_user(session: Session, user: User):
    """
    Syncs a user's birthday record from their profile.
    If a birthday exists, updates it.
    If not, creates a new record.
    """
    birthday = session.exec(select(Birthday).where(Birthday.user_id == user.user_id)).first()
    if birthday:
        birthday.name = user.email  # or user.name if desired
        birthday.date_of_birth = user.date_of_birth
        birthday.workspace_id = user.workspace_id
    else:
        birthday = Birthday(
            user_id=user.user_id,
            name=user.email,
            date_of_birth=user.date_of_birth,
            workspace_id=user.workspace_id
        )
        session.add(birthday)
    session.commit()

# ─── Public: List Timezones ────────────────────────────────────────────────────

class TimezoneList(BaseModel):
    timezones: list[str]

@router.get(
    "/timezones",
    response_model=TimezoneList,
    summary="List all supported timezones  (Auth: public)",
    description="Returns a list of all IANA timezones. No authentication required."
)
def list_timezones():
    try:
        return {"timezones": pytz.all_timezones}
    except Exception as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, str(e))

# ─── Admin: Manually Run Birthday Job ──────────────────────────────────────────

@router.post(
    "/run-birthday-job",
    dependencies=[Depends(current_superuser)],
    summary="Manually trigger today's birthday notifications (Auth: superuser)",
    status_code=status.HTTP_200_OK,
)
def run_birthday_job() -> JSONResponse:
    birthday_job()
    logger.info("Admin triggered run-birthday-job")

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"detail": "birthday_job executed successfully"},
    )

# ─── Admin: Refresh Birthday Table from Users ──────────────────────────────────

@router.post(
    "/refresh-birthday-table",
    dependencies=[Depends(current_superuser)],
    summary="Admin: Refresh birthday table from user information",
    status_code=status.HTTP_200_OK,
)
def refresh_birthday_table_from_users(session: Session = Depends(get_session)):
    logger.info("Admin triggered birthday refresh from users")
    updated = 0
    birthdays = session.exec(select(Birthday).where(Birthday.user_id != None)).all()
    for birthday in birthdays:
        user = session.get(User, birthday.user_id)
        if user:
            sync_birthday_from_user(session, user)
            updated += 1
    logger.info(f"Updated {updated} birthday records")
    return {"updated_birthdays": updated}

# ─── Admin: Backfill Missing Birthday Records ──────────────────────────────────

@router.post(
    "/backfill-birthdays",
    dependencies=[Depends(current_superuser)],
    summary="Admin: Backfill missing birthday records for all users",
    status_code=status.HTTP_200_OK,
)
def backfill_birthdays(session: Session = Depends(get_session)):
    logger.info("Admin triggered backfill birthdays")
    created = 0
    users = session.exec(select(User)).all()
    for user in users:
        existing = session.exec(select(Birthday).where(Birthday.user_id == user.user_id)).first()
        if not existing:
            sync_birthday_from_user(session, user)
            created += 1
    logger.info(f"created {created} birthday records")
    return {"birthdays_created": created}

# ─── Admin: Inspect Redis Cache ──────────────────────────────────

@router.get(
    "/cache/birthdays/{user_id}",
    summary="Inspect Redis cache for a user's birthdays (Auth: superuser)",
    dependencies=[Depends(current_superuser)]
)
def inspect_birthday_cache(user_id: UUID):
    cached = get_cached_birthdays(user_id)
    if cached:
        return {"user_id": user_id, "cached_birthdays": cached}
    return {"user_id": user_id, "cached_birthdays": None, "status": "Cache miss"}

# ─── Admin: Invalidate Redis Cache ──────────────────────────────────

@router.delete(
    "/cache/birthdays/{user_id}",
    summary="Manually invalidate a user's birthday cache (Auth: superuser)",
    dependencies=[Depends(current_superuser)]
)
def clear_birthday_cache(user_id: UUID):
    invalidate_birthdays_cache(user_id)
    return {"user_id": user_id, "status": "Cache invalidated"}