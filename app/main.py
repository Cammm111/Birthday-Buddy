# app/main.py
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from app.core.logging_config import setup_logging
from app.core.db import init_db
from app.services.scheduler_service import start_scheduler
from app.services.auth_service import fastapi_users, auth_backend
from app.routes.user_route import router as user_router
from app.routes.birthday_route import router as birthday_router
from app.routes.workspace_route import router as workspace_router
from app.routes.utils_route import router as utils_router
from app.schemas.user_schema import UserRead, UserCreate, UserUpdate

# 1) Configure logging
setup_logging()

# 2) Init database & seed admin
init_db()

# 3) Kick off the daily scheduler
start_scheduler()

# 4) Create the FastAPI app
app = FastAPI(title="Birthday Buddy")

# 5) AUTHENTICATION ROUTES

# JWT login/logout
app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)

# Registration (requires UserRead & UserCreate so date_of_birth is mandatory)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)

# Forgot-Password & Reset-Password
app.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["auth"],
)

# Email Verification (if you ever need it)
# app.include_router(
#     fastapi_users.get_verify_router(UserRead),
#     prefix="/auth",
#     tags=["auth"],
# )

# (No need to include fastapi_users.get_users_router if you expose
# all admin-only user operations under your own `/users` router.)

# 6) Your other, non-auth routers
app.include_router(user_router)
app.include_router(birthday_router)
app.include_router(workspace_router)
app.include_router(utils_router)
