# app/routes/utils_route.py

import logging
from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlmodel import Session
from app.core.db import get_session
from app.services import utils_service as svc
from app.services.auth_service import current_superuser
from app.schemas.utils_schema import (TimezoneList, JobResult, CountResult, CacheResult, CacheAllUsers,)
logger = logging.getLogger(__name__)

# ──────────────────────────────────Router definition──────────────────────────────────
router = APIRouter(prefix="/utils", tags=["utils"])

# ─────────────────────────────GET /timezones──────────────────────────────
@router.get(
    "/timezones",
    response_model=TimezoneList,
    summary="List all supported time-zones  (public)",
)
async def list_timezones() -> TimezoneList:
    return TimezoneList(timezones=svc.get_supported_timezones())

# ──────────────────────────────POST /run-birthday-job: Manually trigger today's birthday notifications──────────────────────────────
@router.post(
    "/run-birthday-job",
    response_model=JobResult,
    dependencies=[Depends(current_superuser)],
    summary="Trigger today's birthday notifications (Auth: Admin)",
)
async def run_birthday_job() -> JobResult:
    svc.run_birthday_job()
    return JobResult(detail="Birthday job executed successfully")

# ──────────────────────────────POST /refresh-birthday-table: Refresh birthday table from user profiles──────────────────────────────
@router.post(
    "/refresh-birthday-table",
    response_model=CountResult,
    dependencies=[Depends(current_superuser)],
    summary="Refresh birthday table using user records (Auth: Admin)",
)
async def refresh_birthday_table(
    session: Session = Depends(get_session),
) -> CountResult:
    updated = svc.refresh_birthday_table_from_users(session)
    return CountResult(count=updated)

# ──────────────────────────────POST /backfill-birthdays: Backfill missing birthday records for all users──────────────────────────────
@router.post(
    "/backfill-birthdays",
    response_model=CountResult,
    dependencies=[Depends(current_superuser)],
    summary="Create birthday's for users that have none (Auth: Admin)",
)
async def backfill_birthdays(
    session: Session = Depends(get_session),
) -> CountResult:
    created = svc.backfill_birthdays(session)
    return CountResult(count=created)

# ──────────────────────────────GET /cache/all: Gets caches for everyone──────────────────────────────
@router.get(
    "/cache/all",
    response_model=CacheAllUsers,
    dependencies=[Depends(current_superuser)],
    summary="Inspect Redis cache keys for all users (Auth: Admin)",
)
async def cache_all_users(include_values: bool = True) -> CacheAllUsers:
    data = svc.get_all_users_cache(include_values=include_values)
    return CacheAllUsers(users=data)

# ──────────────────────────────GET /cache/birthdays{user_id}: Gets cached birthday data for user──────────────────────────────
@router.get(
    "/cache/birthdays/{user_id}",
    response_model=CacheResult,
    dependencies=[Depends(current_superuser)],
    summary="Show cached birthday data for a user (Auth: Admin)",
)
async def get_birthday_cache(user_id: UUID) -> CacheResult:
    return CacheResult(**svc.inspect_birthday_cache(user_id))

# ──────────────────────────────DELETE /cache/birthdays{user_id}:Invalidate a user's cache──────────────────────────────
@router.delete(
    "/cache/birthdays/{user_id}",
    response_model=JobResult,
    dependencies=[Depends(current_superuser)],
    summary="Clear cached birthday data for a user (Auth: Admin)",
)
async def delete_birthday_cache(user_id: UUID) -> JobResult:
    svc.clear_birthday_cache(user_id)
    return JobResult(detail="Cache invalidated")