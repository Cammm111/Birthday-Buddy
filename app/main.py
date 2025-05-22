# app/main.py

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from app.db import init_db
from app.auth import (
    fastapi_users,
    auth_backend,
    current_active_user,
    current_superuser,
)
from app.models import UserRead, UserCreate
from app.routers import (
    birthdays,
    users as users_router,
    workspaces,
    utils,
)

app = FastAPI(title="Birthday Buddy")

# ─── CORS (for local testing) ────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Init database ────────────────────────────────────────────────────────
init_db()

# ─── Authentication routes ────────────────────────────────────────────────
app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)
app.include_router(
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

# ─── Application routes ───────────────────────────────────────────────────

# Birthday endpoints (requires any authenticated user)
app.include_router(
    birthdays.router,
    prefix="/birthdays",
    tags=["birthdays"],
    dependencies=[Depends(current_active_user)],
)

# User endpoints (e.g. profile, self‐service) (requires auth)
app.include_router(
    users_router.router,
    prefix="/users",
    tags=["users"],
    dependencies=[Depends(current_active_user)],
)

# Workspace CRUD (superuser only)
app.include_router(
    workspaces.router,
    prefix="/workspaces",
    tags=["workspaces"],
    dependencies=[Depends(current_superuser)],
)

# Utility endpoints (run job, ping Slack) (superuser only)
app.include_router(
    utils.router,
    prefix="/utils",
    tags=["utils"],
    dependencies=[Depends(current_superuser)],
)
