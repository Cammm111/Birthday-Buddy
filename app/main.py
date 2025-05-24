# app/main.py
import os
from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../.env"))

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
from app.routes import (
    birthdays,
    users as users_router,
    workspaces,
    utils,
)

# ─── Initialize FastAPI app ──────────────────────────────────────────────
app = FastAPI(title="Birthday Buddy")

# ─── SlowAPI Rate Limiting ───────────────────────────────────────────────
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# You can set a default rate limit for ALL endpoints here
# (adjust as you wish, or omit default_limits to require explicit decorators)
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ─── CORS (for local testing) ────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Init database ───────────────────────────────────────────────────────
init_db()

# ─── Authentication routes ───────────────────────────────────────────────
app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)
# app.include_router(
#    fastapi_users.get_register_router(UserRead, UserCreate),
#    prefix="/auth",
#    tags=["auth"],
# )
app.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["auth"],
)
# app.include_router(
#    fastapi_users.get_verify_router(UserRead),
#    prefix="/auth",
#    tags=["auth"],
# )

# ─── Custom Application routes ───────────────────────────────────────────

app.include_router(
    birthdays.router,
    tags=["birthdays"],
    dependencies=[Depends(current_active_user)],
)
app.include_router(
    users_router.router,
    tags=["users"],
    dependencies=[Depends(current_active_user)],
)
app.include_router(
    workspaces.router,
    tags=["workspaces"],
    dependencies=[Depends(current_superuser)],
)
app.include_router(
    utils.router,
    tags=["utils"],
    dependencies=[Depends(current_superuser)],
)
