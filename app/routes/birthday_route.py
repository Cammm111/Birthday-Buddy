# app/routes/birthday_route.py

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.core.db import get_session
from app.models.birthday_model import Birthday
from app.schemas.birthday_schema import BirthdayRead, BirthdayCreate, BirthdayUpdate
from app.services.auth_service import current_active_user, current_superuser

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
    summary="Create a new birthday  (Auth: any active user)",
    description="Adds a birthday under the authenticated user's workspace."
)
def create_birthday(
    payload: BirthdayCreate,
    session: Session = Depends(get_session),
    user=Depends(current_active_user),
):
    birthday = Birthday.from_orm(payload)
    birthday.workspace_id = user.workspace_id
    session.add(birthday)
    session.commit()
    session.refresh(birthday)
    return birthday

@router.patch(
    "/{birthday_id}",
    response_model=BirthdayRead,
    summary="Update a birthday  (Auth: any active user)",
    description=(
        "Modify one of your birthdays. General users may only update birthdays in their workspace; "
        "superusers may update any."
    )
)
def update_birthday(
    birthday_id: UUID,
    payload: BirthdayUpdate,
    session: Session = Depends(get_session),
    user=Depends(current_active_user),
):
    birthday = session.get(Birthday, birthday_id)
    if not birthday:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Birthday not found")
    if not (user.is_superuser or birthday.workspace_id == user.workspace_id):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not allowed to update this birthday")

    update_data = payload.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(birthday, field, value)

    session.add(birthday)
    session.commit()
    session.refresh(birthday)
    return birthday

@router.delete(
    "/{birthday_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a birthday  (Auth: any active user)",
    description=(
        "Remove one of your birthdays. General users may only delete birthdays in their workspace; "
        "superusers may delete any."
    )
)
def delete_birthday(
    birthday_id: UUID,
    session: Session = Depends(get_session),
    user=Depends(current_active_user),
):
    birthday = session.get(Birthday, birthday_id)
    if not birthday:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Birthday not found")
    if not (user.is_superuser or birthday.workspace_id == user.workspace_id):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not allowed to delete this birthday")

    session.delete(birthday)
    session.commit()
    return
