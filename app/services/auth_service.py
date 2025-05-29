# app/services/auth_service.py

import uuid
from typing import AsyncGenerator
from fastapi import Depends, HTTPException
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import (AuthenticationBackend, BearerTransport, JWTStrategy,)
from fastapi_users.manager import BaseUserManager, UUIDIDMixin
from fastapi_users_db_sqlmodel import SQLModelUserDatabase
from passlib.context import CryptContext
from sqlmodel import Session
from app.core.config import settings
from app.core.db import engine
from app.models.user_model import User
from app.models.workspace_model import Workspace
from app.models.birthday_model import Birthday

# ─────────────────────────────User DB Dependency─────────────────────────────
class PatchedUserDB(SQLModelUserDatabase[User, uuid.UUID]): # Wrapper around SQLModelUserDatabase that uses the SQLModel Session
    def __init__(self, session: Session): 
        super().__init__(session, User) # Initialize base class with the Session and the User model
    async def __call__(self) -> AsyncGenerator["PatchedUserDB", None]: # Allows FastAPI to use PatchedUserDB as a dependency
        yield self

def get_user_db() -> PatchedUserDB: # Dependency that yields a PatchedUserDB instance and ensures the SQLModel session is closed afterwards
    session = Session(engine)
    try:
        yield PatchedUserDB(session)
    finally:
        session.close()

# ─────────────────────────────Password Hasher─────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ─────────────────────────────User Manager─────────────────────────────
class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = settings.jwt_secret
    verification_token_secret   = settings.jwt_secret

    async def create(self,
                     user_create,
                     safe: bool = False,
                    request=None) -> User:
        data = user_create.model_dump()
        workspace_id = data.get("workspace_id") 
        if workspace_id is not None: # If provided a workspace_id, ensure it exists
            db: Session = self.user_db.session
            if not db.get(Workspace, workspace_id):
                raise HTTPException(
                    status_code=400,
                    detail=f"No workspace found with id={workspace_id}"
                ) 
        raw_password = data.pop("password") # Hash password
        hashed       = pwd_context.hash(raw_password)

        user         = User(**data, hashed_password=hashed) # Build/save user model
        db: Session = self.user_db.session  # Persist User
        db.add(user)
        db.commit()
        db.refresh(user)

        birthday = Birthday( # Create a Birthday record for the newly-registered user
            user_id=user.id,
            name=user.email,
            date_of_birth=user.date_of_birth
        )
        db.add(birthday)
        db.commit()
        return user

async def get_user_manager(user_db=Depends(get_user_db)): # Allows FastAPI to inject custom UserManager into authentication endpoints
    yield UserManager(user_db)

# ─────────────────────────────Auth Backend & JWT─────────────────────────────
bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")
def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=settings.jwt_secret, lifetime_seconds=3600)
auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

# ─────────────────────────────FastAPI-Users Setup─────────────────────────────
fastapi_users = FastAPIUsers[User, uuid.UUID](
    get_user_manager,
    [auth_backend],
)

# ─────────────────────────────Create callouts for the future─────────────────────────────
current_active_user = fastapi_users.current_user(active=True) # Active user dependency 
current_superuser   = fastapi_users.current_user(superuser=True) # Admin user dependency