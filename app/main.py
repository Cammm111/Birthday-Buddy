# app/main.py
from dotenv import load_dotenv
load_dotenv() # this will look for a “.env” file in your project root and load it into os.environ
from fastapi import FastAPI
from app.core.logging_config import setup_logging
from app.core.db import init_db
from app.services.scheduler_service import start_scheduler
from app.services.auth_service import fastapi_users, auth_backend
from app.routes.user_route import router as user_router
from app.routes.birthday_route import router as birthday_router
from app.routes.workspace_route import router as workspace_router
from app.routes.utils_route import router as utils_router

# Import only the schemas needed for the routers we keep
from app.schemas.user_schema import UserRead, UserCreate

# 1) Configure logging
setup_logging()

# 2) Init database & seed admin
init_db()

# 3) Kick off the daily scheduler
start_scheduler()

# 4) Create the FastAPI app
app = FastAPI(title="Birthday Buddy")

# 5) AUTHENTICATION ROUTES

# Login & Logout
app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)

# Forgot-Password & Reset-Password
app.include_router(
    fastapi_users.get_reset_password_router(),  # provides both POST /forgot-password and POST /reset-password
    prefix="/auth",
    tags=["auth"],
)

# (No register, verify, or user-CRUD routers here)

# 6) Your other, non-auth routers
app.include_router(user_router)
app.include_router(birthday_router)
app.include_router(workspace_router)
app.include_router(utils_router)
