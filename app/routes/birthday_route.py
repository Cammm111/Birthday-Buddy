# app/routes/birthday_route.py

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.core.db import get_session
from app.models.birthday_model import Birthday
from app.schemas.birthday_schema import BirthdayRead, BirthdayCreate, BirthdayUpdate
from app.services.auth_service import current_active_user, current_superuser
from app.services import birthday_service 

router = APIRouter(
    prefix="/birthdays",
    tags=["birthdays"],
)

# ─── Authenticated (general user) ───────────────────────────────────────────────

@router.get(
    "/",
    response_model=List[BirthdayRead],
    summary="List birthdays in your workspace  (Auth: any active user)",
    description="Returns all birthdays belonging to the authenticated user's workspace."
)
def list_birthdays(
    session: Session = Depends(get_session),
    user=Depends(current_active_user),
):
    stmt = select(Birthday).where(Birthday.workspace_id == user.workspace_id)
    return session.exec(stmt).all()

# ─── Superuser endpoints ────────────────────────────────────────────────────────

@router.get(
    "/all",
    response_model=List[BirthdayRead],
    dependencies=[Depends(current_superuser)],
    summary="List all birthdays across all workspaces  (Auth: superuser)",
    description="Returns every birthday in the system, regardless of workspace."
)
def list_all_birthdays(
    session: Session = Depends(get_session),
):
    stmt = select(Birthday)
    return session.exec(stmt).all()

@router.post(
    "/",
    response_model=BirthdayRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(current_superuser)],
    summary="Create a new birthday (Auth: superuser only)",
)
def create_birthday(
    payload: BirthdayCreate,
    session: Session = Depends(get_session),
):
    return birthday_service.create_birthday(session, payload.user_id, payload)

@router.patch(
    "/{birthday_id}",
    response_model=BirthdayRead,
    summary="Update a birthday (Auth: any active user)",
    description=("Modify one of your birthdays. General users may only update birthdays in their workspace. Superusers may update any.")
)
def update_birthday(
    birthday_id: UUID,
    payload: BirthdayUpdate,
    session: Session = Depends(get_session),
    user=Depends(current_active_user),
):
    birthday = birthday_service.update_birthday(session, user.user_id, birthday_id, payload)
    if birthday is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Birthday not found or unauthorized")
    return birthday

@router.delete(
    "/{birthday_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a birthday  (Auth: any active user)",
    description=("Remove one of your birthdays. General users may only delete birthdays in their workspace. Superusers may delete any.")
)
def delete_birthday(
    birthday_id: UUID,
    session: Session = Depends(get_session),
    user=Depends(current_active_user),
):
    success = birthday_service.delete_birthday(session, user.user_id, birthday_id)
    if not success:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Birthday not found or unauthorized")
    return
