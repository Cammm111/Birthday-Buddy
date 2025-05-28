# app/core/db.py

from sqlmodel import SQLModel, create_engine, Session, select
from sqlalchemy.exc import IntegrityError
from redis import Redis
from app.core.config import settings
from app.models.user_model import User

# ──────────────────────────────────Create SQLModel Engine──────────────────────────────────
engine = create_engine(settings.database_url, echo=False)
SessionLocal = Session # aliases the local session

# ──────────────────────────────────Create Redis client──────────────────────────────────
redis = Redis.from_url(settings.redis_url, decode_responses=True)

# ──────────────────────────────────Initialize database & seed admin──────────────────────────────────
def init_db() -> None:
    """
    Create all tables and ensure the default admin user exists.
    """
    SQLModel.metadata.create_all(engine)

    with SessionLocal(engine) as session: # look for an existing superuser
        existing = session.exec(
            select(User).where(User.is_superuser == True)
        ).first()                                     
        if not existing:
            admin = User(
                email=settings.admin_email,
                hashed_password=settings.hashed_admin_password,
                date_of_birth=settings.admin_dob,
                is_active=True,
                is_superuser=True,
                is_verified=True,
            )
            session.add(admin)
            try:
                session.commit()
            except IntegrityError: # if two processes race eat it up so only 1 admin exists
                session.rollback()
                
# ──────────────────────────────────Give local session info──────────────────────────────────
def get_session():
    """
    Dependency that yields a database session and closes it after use.
    """
    with SessionLocal(engine) as session:
        yield session