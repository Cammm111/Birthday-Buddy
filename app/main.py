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
from app.schemas.user_schema import UserRead, UserCreate

# 1) Configure logging
setup_logging()

# 2) Initialize database & seed admin user
init_db()

# 3) Create the FastAPI app
app = FastAPI(title="Birthday Buddy")

# 4) Start the scheduler on application startup
@app.on_event("startup")
def on_startup():
    start_scheduler()

# 5) AUTHENTICATION ROUTES

# JWT login/logout
app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)

# Registration (requires UserRead & UserCreate)
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

# 6) Your application routers

app.include_router(user_router)
app.include_router(birthday_router)
app.include_router(workspace_router)
app.include_router(utils_router)
