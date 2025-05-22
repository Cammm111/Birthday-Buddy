# app/db.py
from sqlmodel import SQLModel, create_engine, Session

sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

# echo=True will print all SQL to the console (helpful for debugging)
engine = create_engine(sqlite_url, echo=True)

def get_session() -> Session:
    with Session(engine) as session:
        yield session

def init_db() -> None:
    SQLModel.metadata.create_all(engine)
