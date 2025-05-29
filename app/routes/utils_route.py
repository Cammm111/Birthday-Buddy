# app/routes/utils_route.py

import logging
from fastapi import APIRouter, Depends, status
from sqlmodel import Session
from app.core.db import get_session
from app.services import utils_service as svc
from app.services.auth_service import current_superuser
from app.schemas.utils_schema import (TimezoneList, JobResult, CountResult, CacheResult,)
logger = logging.getLogger(__name__)

# ──────────────────────────────────Router definition──────────────────────────────────
router = APIRouter(prefix="/utils", tags=["utils"])

# ─────────────────────────────GET /timezones──────────────────────────────
@router.get("/timezones",
    response_model=TimezoneList,
    summary="List all supported time-zones (Auth: Public)",
)
async def list_timezones() -> TimezoneList:
    return TimezoneList(timezones=svc.get_supported_timezones())

# ──────────────────────────────POST /run-birthday-job──────────────────────────────
@router.post("/run-birthday-job",
    response_model=JobResult,
    dependencies=[Depends(current_superuser)],
    summary="Trigger today's birthday notifications (Auth: Admin)",
    status_code=status.HTTP_202_ACCEPTED,
)
async def run_birthday_job() -> JobResult:
    return svc.run_birthday_job()

# ──────────────────────────────POST /refresh-birthday-table──────────────────────────────
@router.post("/refresh-birthday-table",
    response_model=CountResult,
    dependencies=[Depends(current_superuser)],
    summary="Sync birthdays table from current User records (Auth: Admin)",
)
async def refresh_birthdays(session: Session = Depends(get_session)) -> CountResult:
    return svc.refresh_birthday_table_from_users(session)

# ──────────────────────────────POST /backfill-birthdays──────────────────────────────
@router.post("/backfill-birthdays",
    response_model=CountResult,
    dependencies=[Depends(current_superuser)],
    summary="Insert birthdays only for users who lack one (Auth: Admin)",
)
async def backfill_birthdays(session: Session = Depends(get_session)) -> CountResult:
    return svc.backfill_birthdays(session)

# ──────────────────────────────GET /cache/all: ──────────────────────────────
@router.get("/cache/all",
    response_model=CacheResult,
    dependencies=[Depends(current_superuser)],
    summary="Return the full cache blob: users, birthdays, workspaces (Auth: Admin)",
)
async def cache_all() -> CacheResult:
    return svc.get_entire_cache()

# ──────────────────────────────GET /cache/birthdays/all──────────────────────────────
@router.get("/cache/birthdays/all",
    response_model=CacheResult,
    dependencies=[Depends(current_superuser)],
    summary="Return cached birthdays only (Auth: Admin)",
)
async def cache_birthdays() -> CacheResult:
    return svc.get_cached_birthdays()

# ──────────────────────────────GET /cache/users/all──────────────────────────────
@router.get("/cache/users/all",
    response_model=CacheResult,
    dependencies=[Depends(current_superuser)],
    summary="Return cached users only (Auth: Admin)",
)
async def cache_users() -> CacheResult:
    return svc.get_cached_users()

# ──────────────────────────────GET /cache/workspaces/all──────────────────────────────
@router.get("/cache/workspaces/all",
    response_model=CacheResult,
    dependencies=[Depends(current_superuser)],
    summary="Return cached workspaces only (Auth: Admin)",
)
async def cache_workspaces() -> CacheResult:
    return svc.get_cached_workspaces()