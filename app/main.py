# app/main.py
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from app.db import init_db
from app.routers import birthdays, utils, users as users_router
from app.auth import fastapi_users, auth_backend, current_active_user, current_superuser
from app.models import UserRead, UserCreate

app = FastAPI(title="Birthday Buddy")

# Allow CORS (for local testing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create all tables
init_db()

# ─── Authentication routes ────────────────────────────────────────────
app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)
app.include_router(
    # NOTE: here we import UserRead/UserCreate from app.models
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/auth",
    tags=["auth"],
)

# ─── Application routes ───────────────────────────────────────────────
app.include_router(utils.router)
app.include_router(
    birthdays.router,
    dependencies=[Depends(current_active_user)],
)
app.include_router(
    users_router.router,
    dependencies=[Depends(current_active_user)],
)
