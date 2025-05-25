# app/services/redis_cache_service.py

import json
from uuid import UUID
from app.core.db import redis

CACHE_TTL = 60 * 5  # five minutes

def _cache_key(user_id: UUID) -> str:
    return f"birthdays:{user_id}"  # str(user_id) under the hood

def get_cached_birthdays(user_id: UUID) -> list[dict] | None:
    key = _cache_key(user_id)
    raw = redis.get(key)
    if not raw:
        return None
    return json.loads(raw)

def set_cached_birthdays(user_id: UUID, items: list):
    key = _cache_key(user_id)
    # if items are ORM objects, convert to dicts first
    payload = [item.dict() if hasattr(item, "dict") else item for item in items]
    redis.set(key, json.dumps(payload), ex=CACHE_TTL)

def invalidate_birthdays_cache(user_id: UUID):
    key = _cache_key(user_id)
    redis.delete(key)
