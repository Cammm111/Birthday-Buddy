# app/crud.py
from sqlmodel import Session, select
from sqlalchemy import Index
from app.db import engine
from app.models import Birthday, Workspace
import redis

# Redis client (env‐backed URL)
r = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"), decode_responses=True)

# create an index on birthdays (run in Alembic migration or via metadata)
Index("ix_birthday_dob", Birthday.date_of_birth)

def get_birthdays_for_workspace(ws_id: str):
    key = f"birthdays:{ws_id}"
    cached = r.get(key)
    if cached:
        return json.loads(cached)
    with Session(engine) as session:
        rows = session.exec(select(Birthday).where(Birthday.workspace_id==ws_id)).all()
        result = [b.dict() for b in rows]
    r.set(key, json.dumps(result), ex=300)
    return result

def create_birthday(bday: Birthday):
    with Session(engine) as session:
        session.add(bday)
        session.commit()
        session.refresh(bday)
    # invalidate cache
    r.delete(f"birthdays:{bday.workspace_id}")
    return bday
