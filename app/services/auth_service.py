# app/services/auth_service.py

import uuid
from typing import AsyncGenerator
from fastapi import Depends, HTTPException
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from fastapi_users.manager import BaseUserManager, UUIDIDMixin
from fastapi_users_db_sqlmodel import SQLModelUserDatabase
from passlib.context import CryptContext
from sqlmodel import Session

from app.core.config import settings
from app.core.db import engine
from app.models.user_model import User
from app.models.workspace_model import Workspace

# ─── User DB Dependency ─────────────────────────────────────────────────────────

class PatchedUserDB(SQLModelUserDatabase[User, uuid.UUID]):
    """
    Wrapper around SQLModelUserDatabase that uses our SQLModel Session.
    """
    def __init__(self, session: Session):
        super().__init__(session, User)

    async def __call__(self) -> AsyncGenerator["PatchedUserDB", None]:
        yield self

def get_user_db() -> PatchedUserDB:
    session = Session(engine)
    try:
        yield PatchedUserDB(session)
    finally:
        session.close()

# ─── Password Hasher ─────────────────────────────────────────────────────────────

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ─── User Manager ───────────────────────────────────────────────────────────────

class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = settings.jwt_secret
    verification_token_secret   = settings.jwt_secret

    async def create(self, user_create, safe: bool = False, request=None) -> User:
        """
        Overrides FastAPI-Users create: first validate workspace_id (if any),
        then hash password and persist.
        """
        data = user_create.model_dump()

        # 1) If they provided a workspace_id, ensure it exists
        workspace_id = data.get("workspace_id")
        if workspace_id is not None:
            db: Session = self.user_db.session  # type: ignore[attr-defined]
            if not db.get(Workspace, workspace_id):
                raise HTTPException(
                    status_code=400,
                    detail=f"No workspace found with id={workspace_id}"
                )

        # 2) Hash their password and build our User model
        raw_password = data.pop("password")
        hashed      = pwd_context.hash(raw_password)
        user        = User(**data, hashed_password=hashed)

        # 3) Persist
        db: Session = self.user_db.session  # type: ignore[attr-defined]
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

async def get_user_manager(user_db=Depends(get_user_db)):
    yield UserManager(user_db)

# ─── Auth Backend & JWT ─────────────────────────────────────────────────────────

bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")

def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=settings.jwt_secret, lifetime_seconds=3600)

auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

# ─── FastAPI-Users Setup ────────────────────────────────────────────────────────

fastapi_users = FastAPIUsers[User, uuid.UUID](
    get_user_manager,
    [auth_backend],
)

current_active_user = fastapi_users.current_user(active=True)
current_superuser   = fastapi_users.current_user(superuser=True)
