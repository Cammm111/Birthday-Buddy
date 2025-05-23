# app/db.py
from sqlmodel import SQLModel, create_engine, Session
from app.models import User
from sqlmodel import select
from passlib.context import CryptContext
import os
from app.models import User
from sqlmodel import select
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

# echo=True will print all SQL to the console (helpful for debugging)
engine = create_engine(sqlite_url, echo=True)

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