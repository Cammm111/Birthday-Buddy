# app/routes/birthday_route.py

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from app.core.db import get_session
from app.models.birthday_model import Birthday
from app.schemas.birthday_schema import BirthdayRead, BirthdayCreate, BirthdayUpdate
from app.services.auth_service import current_active_user, current_superuser
from app.services import birthday_service 

# ──────────────────────────────────Router definition──────────────────────────────────
router = APIRouter(prefix="/birthdays", tags=["Birthdays"],) # Router prefix "/birthdays". Group these bad boys under "birthdays" in the OpenAPI docs

# ──────────────────────────────────GET /birthdays──────────────────────────────────
# GET /birthdays
@router.get("/",
    response_model=List[BirthdayRead],
    summary="List birthdays in your workspace (Auth: Any active user)",
    description="Returns all birthdays belonging to the authenticated user's workspace."
)
def list_birthdays_by_workspace(
    session: Session = Depends(get_session),
    user=Depends(current_active_user),
):
    return birthday_service.list_birthdays_by_workspace( # Delegate to service (which handles user-scoped caching)
        session,
        workspace_id=user.workspace_id,
        user_id=user.user_id,
    )

# ──────────────────────────────────GET /birthdays/all──────────────────────────────────
@router.get("/all",
    response_model=List[BirthdayRead], # Response models defined in birthday_schema.py
    dependencies=[Depends(current_superuser)], # Needs to be an admin!
    summary="List all birthdays across all workspaces (Auth: Admin)",
    description="Returns every birthday in the system, regardless of workspace."
)
def list_all_birthdays(
    session: Session = Depends(get_session),
):
    return birthday_service.list_all_birthdays(session)

# ──────────────────────────────────POST /birthdays──────────────────────────────────
@router.post("/",
    response_model=BirthdayRead, # Response models defined in birthday_schema.py
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(current_superuser)],
    summary="Create a new birthday (Auth: Admin)",
)
def create_birthday(
    payload: BirthdayCreate,
    session: Session = Depends(get_session),
):
    return birthday_service.create_birthday(session, payload.user_id, payload) # Delegate creation to the service layer. Separation of church and state right?

# ──────────────────────────────────PATCH /birthdays/{birthday_id}──────────────────────────────────
@router.patch("/{birthday_id}",
    response_model=BirthdayRead, # Response models defined in birthday_schema.py
    summary="Update a birthday (Auth: Any active user (self))",
    description=("Modify your birthday! General users may only update their own birthdays. Admins may update any.")
)
def update_birthday(
    birthday_id: UUID,
    payload: BirthdayUpdate,
    session: Session = Depends(get_session),
    user=Depends(current_active_user),
):
    birthday = birthday_service.update_birthday(session, user.user_id, birthday_id, payload) # Delegate creation to the service layer
    if birthday is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Birthday not found or unauthorized")
    return birthday

# ──────────────────────────────────DELETE /birthdays/{birthday_id}──────────────────────────────────
@router.delete("/{birthday_id}",
    status_code=status.HTTP_204_NO_CONTENT, # No response for deletion, sorry...
    summary="Delete your birthday record (Auth: any active user)",
    description=("Remove your birthday. General users may only delete their own birthdays. Admins may delete any.")
)
def delete_birthday(
    birthday_id: UUID,
    session: Session = Depends(get_session),
    user=Depends(current_active_user),
):
    success = birthday_service.delete_birthday(session, user, birthday_id)
    if not success:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Birthday not found or unauthorized")
    return