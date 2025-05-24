from fastapi import APIRouter, Depends
from typing import List
from sqlmodel import select, Session
from app.models import Birthday, BirthdayCreate
from app.db import get_session
from app.redis_cache import redis_client
import json

router = APIRouter(prefix="/birthdays", tags=["birthdays"])

@router.get("/", response_model=List[Birthday])
async def list_birthdays(session: Session = Depends(get_session)):
    """Return all birthdays sorted by month/day, with async Redis caching."""
    cache_key = "birthdays:all"
    cached = await redis_client.get(cache_key)
    if cached:
        # Deserialize JSON to Python objects
        return [Birthday(**item) for item in json.loads(cached)]
    # Query DB
    stmt = select(Birthday).order_by(Birthday.date_of_birth)
    result = session.exec(stmt).all()
    # Cache result for 60 seconds
    await redis_client.setex(cache_key, 60, json.dumps([b.dict() for b in result]))
    return result

@router.post("/", response_model=Birthday, status_code=201)
async def create_birthday(data: BirthdayCreate, session: Session = Depends(get_session)):
    """Create a new birthday entry and invalidate cache."""
    birthday = Birthday.from_orm(data)
    session.add(birthday)
    session.commit()
    session.refresh(birthday)
    # Invalidate cache after change
    await redis_client.delete("birthdays:all")
    return birthday
