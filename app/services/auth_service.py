# app/services/auth_service.py

import uuid
from typing import AsyncGenerator
from fastapi import Depends
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

# ─── User DB Dependency ─────────────────────────────────────────────────────────
class PatchedUserDB(SQLModelUserDatabase[User, uuid.UUID]):
    """
    A wrapper around SQLModelUserDatabase that uses our SQLModel Session.
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

# ─── User Manager ───────────────────────────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    """
    Overrides create to hash passwords and uses our JWT secret for tokens.
    """
    reset_password_token_secret = settings.jwt_secret
    verification_token_secret = settings.jwt_secret

    async def create(self, user_create, safe: bool = False) -> User:
        user_data = user_create.model_dump()
        user_data["hashed_password"] = pwd_context.hash(user_data.pop("password"))
        user = User(**user_data)
        self.db.session.add(user)
        self.db.session.commit()
        self.db.session.refresh(user)
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
