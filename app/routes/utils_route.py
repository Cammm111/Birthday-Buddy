# app/routes/utils_route.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import pytz

from app.services.scheduler_service import birthday_job
from app.services.auth_service import current_superuser

router = APIRouter(prefix="/utils", tags=["utils"])

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

@router.get(
    "/health",
    summary="Health check endpoint  (Auth: public)",
    description="Simple liveness check. No authentication required."
)
def health_check():
    return {"status": "ok"}

@router.post(
    "/run-birthday-job",
    dependencies=[Depends(current_superuser)],
    summary="Manually trigger today's birthday notifications  (Auth: superuser)",
    description="Only superusers may invoke this to immediately run the birthday notification job.",
    status_code=status.HTTP_200_OK,
)
def run_birthday_job() -> JSONResponse:
    birthday_job()
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"detail": "birthday_job executed successfully"},
    )
