# app/routes/utils_route.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import pytz

from app.services.scheduler_service import birthday_job
from app.services.auth_service import current_superuser
from sqlmodel import Session, select
from app.core.db import get_session
from app.models.user_model import User
from app.models.birthday_model import Birthday

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
@router.post(
    "/refresh-birthday-table",
    dependencies=[Depends(current_superuser)],
    summary="Admin: Refresh birthday table from user information",
    description="Update birthdays for all user-linked entries to reflect current user information.",
    status_code=status.HTTP_200_OK,
)
def refresh_birthday_table_from_users(
    session: Session = Depends(get_session),
):
    updated = 0
    # Get all birthdays with a user_id
    stmt = select(Birthday).where(Birthday.user_id != None)
    birthdays = session.exec(stmt).all()
    for birthday in birthdays:
        user = session.get(User, birthday.user_id)
        if user:
            # Update fields from User as needed:
            birthday.name = user.email  # or user.name if you have a name field
            birthday.workspace_id = user.workspace_id
            birthday.date_of_birth = user.date_of_birth
            # Add more sync logic for future columns here
            session.add(birthday)
            updated += 1
    session.commit()
    return {"updated_birthdays": updated}

# app/routes/utils_route.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import pytz

from app.services.scheduler_service import birthday_job
from app.services.auth_service import current_superuser
from sqlmodel import Session, select
from app.core.db import get_session
from app.models.user_model import User
from app.models.birthday_model import Birthday

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
@router.post(
    "/refresh-birthday-table",
    dependencies=[Depends(current_superuser)],
    summary="Admin: Refresh birthday table from user information",
    description="Update birthdays for all user-linked entries to reflect current user information.",
    status_code=status.HTTP_200_OK,
)
def refresh_birthday_table_from_users(
    session: Session = Depends(get_session),
):
    updated = 0
    # Get all birthdays with a user_id
    stmt = select(Birthday).where(Birthday.user_id != None)
    birthdays = session.exec(stmt).all()
    for birthday in birthdays:
        user = session.get(User, birthday.user_id)
        if user:
            # Update fields from User as needed:
            birthday.name = user.email  # or user.name if you have a name field
            birthday.workspace_id = user.workspace_id
            birthday.date_of_birth = user.date_of_birth
            # Add more sync logic for future columns here
            session.add(birthday)
            updated += 1
    session.commit()
    return {"updated_birthdays": updated}

@router.post(
    "/backfill-birthdays",
    dependencies=[Depends(current_superuser)],
    summary="Admin: Backfill missing birthday records for all users",
    description="Create a birthday record for any user that does not already have one.",
    status_code=status.HTTP_200_OK,
)
def backfill_birthdays(session: Session = Depends(get_session)):
    created = 0
    users = session.exec(select(User)).all()
    for user in users:
        # Only add if user does NOT already have a birthday
        if not session.exec(select(Birthday).where(Birthday.user_id == user.id)).first():
            b = Birthday(
                name=user.email,  # or user.name if you add a name field
                date_of_birth=user.date_of_birth,
                user_id=user.id,
                workspace_id=user.workspace_id,
            )
            session.add(b)
            created += 1
    session.commit()
    return {"birthdays_created": created}