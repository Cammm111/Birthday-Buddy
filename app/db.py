# app/db.py
import os
from sqlmodel import SQLModel, create_engine, Session, select
from app.models import User
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

DATABASE_URL = os.getenv("DATABASE_URL")
print("DEBUG: DATABASE_URL =", os.getenv("DATABASE_URL"))

engine = create_engine(DATABASE_URL, echo=True)

def get_session() -> Session:
    with Session(engine) as session:
        yield session

def init_db() -> None:
    SQLModel.metadata.create_all(engine)
    # --- ADMIN USER AUTO-CREATION ---
    admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com")
    admin_password = os.getenv("ADMIN_PASSWORD", "adminpassword")
    with Session(engine) as session:
        admin_user = session.exec(select(User).where(User.is_superuser == True)).first()
        if not admin_user:
            admin = User(
                email=admin_email,
                hashed_password=pwd_context.hash(admin_password),
                is_superuser=True,
                is_active=True,
                is_verified=True,
            )
            session.add(admin)
            session.commit()
            print(f"==> Admin user created: {admin_email} / {admin_password}")
        else:
            print("==> Admin user already exists. See README for default credentials")
