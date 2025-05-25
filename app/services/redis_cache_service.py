# app/services/redis_cache_service.py

import json
import logging
from uuid import UUID
from app.core.db import redis

logger = logging.getLogger(__name__)

CACHE_TTL = 60 * 5  # 5 minutes

def _cache_key(user_id: UUID) -> str:
    return f"birthdays:{user_id}"

def get_cached_birthdays(user_id: UUID) -> list[dict] | None:
    key = _cache_key(user_id)
    raw = redis.get(key)

    if raw:
        logger.debug(f"🟢 Cache hit for user {user_id}")
        return json.loads(raw)

    logger.debug(f"⚪ Cache miss for user {user_id}")
    return None

def set_cached_birthdays(user_id: UUID, items: list):
    key = _cache_key(user_id)

    payload = [item.dict() if hasattr(item, "dict") else item for item in items]
    redis.set(key, json.dumps(payload), ex=CACHE_TTL)

    logger.info(f"📝 Set cache for user {user_id} with {len(payload)} item(s)")

def invalidate_birthdays_cache(user_id: UUID):
    key = _cache_key(user_id)
    redis.delete(key)
    logger.info(f"🔄 Invalidated cache for user {user_id}")
