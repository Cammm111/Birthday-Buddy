# app/services/redis_cache_service.py

import json
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID
from app.core.db import redis

logger = logging.getLogger(__name__)

CACHE_TTL = 300  # Cache time - 5 minutes
PREFIX_TEMPLATE = "user:{uid}:"

# ─────────────────────────────Cached keys helper─────────────────────────────
def _cache_key(user_id: UUID) -> str:
    return f"birthdays:{user_id}"

# ─────────────────────────────User prefix helper─────────────────────────────
def _user_prefix(user_id: UUID) -> str: # Return key prefix used for all of this user’s cache entries
    return PREFIX_TEMPLATE.format(uid=user_id)

# ─────────────────────────────Get cached birthdays─────────────────────────────
def get_cached_birthdays(user_id: UUID) -> Optional[List[Dict[str, Any]]]:
    key = _cache_key(user_id)
    raw = redis.get(key)

    if raw:
        logger.debug(f"Cache hit for user {user_id}")
        return json.loads(raw)

    logger.debug(f"Cache miss for user {user_id}")
    return None

# ─────────────────────────────Set Cached birthdays─────────────────────────────
def set_cached_birthdays(user_id: UUID,
                         items: List[Any]):
    key = _cache_key(user_id)

    payload = [item.dict() if hasattr(item, "dict") else item for item in items]
    redis.set(key, json.dumps(payload), ex=CACHE_TTL)

    logger.info(f"Set cache for user {user_id} with {len(payload)} item(s)")

# ─────────────────────────────Invalidate user's cached birthdays─────────────────────────────
def invalidate_birthdays_cache(user_id: UUID):
    key = _cache_key(user_id)
    redis.delete(key)
    logger.info(f"Invalidated cache for user {user_id}")

# ─────────────────────────────List user cache─────────────────────────────
def list_user_cache(user_id: UUID,
                    include_values: bool = True) -> Dict[str, Any]: # List all Redis keys/values under this user’s prefix.
    prefix = _user_prefix(user_id)
    cursor = 0
    keys: List[str] = []
    while True:
        cursor, batch = redis.scan(cursor=cursor, match=f"{prefix}*")
        keys.extend(batch)
        if cursor == 0:
            break

    if not include_values:
        return {k: None for k in keys}

    if keys:
        values = redis.mget(keys)
        return dict(zip(keys, values))
    return {}

# ─────────────────────────────Clear user cache─────────────────────────────
def clear_user_cache(user_id: UUID) -> int: # Delete all Redis keys that belong to the user. Returns the number of keys deleted.
    keys = list_user_cache(user_id, include_values=False).keys()
    if not keys:
        return 0
    total_deleted = 0

    key_list = list(keys)
    batch_size = 1000 # Delete in batches of 1000
    for i in range(0, len(key_list), batch_size):
        batch = key_list[i : i + batch_size]
        deleted = redis.delete(*batch)
        total_deleted += deleted

    logger.info("Cleared %d cache key(s) for user %s", total_deleted, user_id)
    return total_deleted

# ─────────────────────────────List all users cache─────────────────────────────
def list_all_users_cache(include_values: bool = True) -> Dict[str, Optional[Dict[str, Any]]]: # Return a mapping for every user that has at least one key.  Uses SCAN so it does *not* block Redis. If include_values=False, returns {user_id: {key: None}} so you can see the inventory without transferring a lot of data.
    pattern = "user:*:*" # Any key that follows user:{uuid}:{resource}
    cursor = 0
    results: dict[str, dict[str, Any] | None] = {}

    while True:
        cursor, batch = redis.scan(cursor=cursor, match=pattern, count=500)
        for full_key in batch:
            _, user_id, _ = full_key.split(":", 2)   # Faster than regex according to the internet
            results.setdefault(user_id, {})
            if include_values:
                value = redis.get(full_key)
                results[user_id][full_key] = value
            else:
                results[user_id][full_key] = None
        if cursor == 0:
            break

    return results