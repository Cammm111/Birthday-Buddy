# app/main.py

from fastapi import FastAPI
from app.core.logging_config import setup_logging
from app.core.db import init_db
from app.services.scheduler_service import start_scheduler
from app.services.auth_service import fastapi_users, auth_backend
from app.routes.user_route import router as user_router
from app.routes.birthday_route import router as birthday_router
from app.routes.workspace_route import router as workspace_router
from app.routes.utils_route import router as utils_router

# Import your Pydantic schemas for auth
from app.schemas.user_schema import UserRead, UserCreate, UserUpdate

# 1) Configure logging first
setup_logging()

# 2) Initialize database (create tables & seed admin user)
init_db()

# 3) Start the background scheduler
start_scheduler()

# 4) Create FastAPI app
app = FastAPI(title="Birthday Buddy")

# 5) Wire up FastAPI-Users authentication routes

# JWT login/logout
app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)

# Registration (needs read & create schemas)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)

# Reset password
app.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["auth"],
)

# Email verification (needs read schema)
app.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/auth",
    tags=["auth"],
)

# Built-in users CRUD (needs read & update schemas)
app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/auth/users",
    tags=["auth"],
)

# 6) Include your custom routers
app.include_router(user_router)
app.include_router(birthday_router)
app.include_router(workspace_router)
app.include_router(utils_router)
