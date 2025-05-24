# app/services/redis_cache_service.py

import json
from uuid import UUID
from typing import List, Optional

from app.core.db import redis
from app.schemas.birthday_schema import BirthdayRead

# Time (in seconds) to cache birthday lists
CACHE_EXPIRE_SECONDS = 60


def get_cached_birthdays(user_id: UUID) -> Optional[List[BirthdayRead]]:
    """
    Retrieve a user’s cached birthdays from Redis.
    Returns a list of BirthdayRead objects if present, else None.
    """
    key = f"birthdays:{user_id}"
    data = redis.get(key)  # sync call
    if not data:
        return None
    items = json.loads(data)
    return [BirthdayRead(**item) for item in items]


def set_cached_birthdays(user_id: UUID, birthdays: List[BirthdayRead]) -> None:
    """
    Cache a user’s birthday list in Redis for CACHE_EXPIRE_SECONDS.
    """
    key = f"birthdays:{user_id}"
    payload = [b.dict() for b in birthdays]
    redis.set(key, json.dumps(payload), ex=CACHE_EXPIRE_SECONDS)


def invalidate_birthdays_cache(user_id: UUID) -> None:
    """
    Remove a user’s birthday list from Redis (e.g., after create/update/delete).
    """
    key = f"birthdays:{user_id}"
    redis.delete(key)
