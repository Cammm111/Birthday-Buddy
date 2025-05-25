# app/core/db.py

from sqlmodel import SQLModel, create_engine, Session, select
from sqlalchemy.exc import IntegrityError
from redis import Redis
from app.core.config import settings
from app.models.user_model import User

# 1) Database engine & session factory
engine = create_engine(settings.database_url, echo=False)
SessionLocal = Session  # alias, same signature as Session(engine)

# 2) Shared Redis client
redis = Redis.from_url(settings.redis_url, decode_responses=True)


def init_db() -> None:
    """
    Create all tables and ensure the default admin user exists.
    """
    SQLModel.metadata.create_all(engine)

    with SessionLocal(engine) as session:
        # look for an existing superuser
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
            except IntegrityError:
                session.rollback()
                # if two processes race, ignore

def get_session():
    """
    Dependency that yields a database session and closes it after use.
    Usage in your routes:
        @router.get(..., dependencies=[Depends(get_session)])
        def read_stuff(db: Session = Depends(get_session)):
            …
    """
    with SessionLocal(engine) as session:
        yield session