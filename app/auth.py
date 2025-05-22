# app/auth.py
import uuid
import secrets
from typing import AsyncGenerator

from fastapi import Depends                       # ← add this
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from fastapi_users.manager import BaseUserManager, UUIDIDMixin
from fastapi_users_db_sqlmodel import SQLModelUserDatabase as _OrigDB
from passlib.context import CryptContext
from sqlmodel import Session

from app.db import engine
from app.models import User

# ──────────────────────────────────────────────────────────────────────
# 1. User database (patched to accept our Session-based DB)
# ──────────────────────────────────────────────────────────────────────
class PatchedDB(_OrigDB):
    def __init__(self, session: Session):
        super().__init__(session, User)

    async def __call__(self) -> AsyncGenerator[_OrigDB, None]:
        yield self

def get_user_db() -> PatchedDB:
    session = Session(engine)
    try:
        yield PatchedDB(session)
    finally:
        session.close()

# ──────────────────────────────────────────────────────────────────────
# 2. User manager (overrides create to hash passwords)
# ──────────────────────────────────────────────────────────────────────
SECRET = secrets.token_urlsafe(32)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    async def create(self, user_create, safe: bool = False):
        user_dict = user_create.create_update_dict()
        user_dict["hashed_password"] = pwd_context.hash(user_dict.pop("password"))
        user = User(**user_dict)
        self.db.session.add(user)
        self.db.session.commit()
        self.db.session.refresh(user)
        return user

async def get_user_manager(user_db=Depends(get_user_db)):
    yield UserManager(user_db)

# ──────────────────────────────────────────────────────────────────────
# 3. Authentication backend & JWT strategy
# ──────────────────────────────────────────────────────────────────────
bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")

def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=SECRET, lifetime_seconds=3600)

auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

# ──────────────────────────────────────────────────────────────────────
# 4. FastAPI-Users instance & dependencies
# ──────────────────────────────────────────────────────────────────────
fastapi_users = FastAPIUsers[User, uuid.UUID](
    get_user_manager,
    [auth_backend],
)

current_active_user = fastapi_users.current_user(active=True)
current_superuser   = fastapi_users.current_user(superuser=True)
