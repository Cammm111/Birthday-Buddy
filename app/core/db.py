# app/core/db.py

from sqlmodel import SQLModel, create_engine, Session, select
from redis.asyncio import Redis
from passlib.context import CryptContext

from app.core.config import settings
from app.models.user_model import User  # corrected import

# --- Password hasher for seeding the admin user ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- SQLModel / PostgreSQL engine ---
engine = create_engine(
    settings.database_url,
    echo=True,  # set False in production if too verbose
)

def get_session():
    """
    FastAPI dependency that yields a SQLModel Session and
    ensures it’s closed after use.
    """
    with Session(engine) as session:
        yield session

# --- Async Redis client for caching, locks, etc. ---
redis = Redis.from_url(
    settings.redis_url,
    encoding="utf-8",
    decode_responses=True,
)

def init_db() -> None:
    """
    Create database tables and seed an admin user if one doesn't exist.
    Call this on startup (e.g. in main.py).
    """
    # create all tables from your SQLModel models
    SQLModel.metadata.create_all(engine)

    # gather admin credentials from settings
    admin_email = settings.admin_email
    admin_password = settings.admin_password

    with Session(engine) as session:
        # look for any existing superuser
        existing = session.exec(
            select(User).where(User.is_superuser == True)
        ).first()

        if not existing:
            admin = User(
                email=admin_email,
                hashed_password=pwd_context.hash(admin_password),
                is_superuser=True,
                is_active=True,
                is_verified=True,
                workspace_id=None,
            )
            session.add(admin)
            session.commit()
