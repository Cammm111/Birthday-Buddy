# app/services/redis_cache_service.py

from __future__ import annotations
import json
import logging
from typing import Any, Dict, List, Optional, Sequence
from uuid import UUID
from redis import Redis, RedisError
from app.core.db import redis
logger = logging.getLogger(__name__)

CACHE_TTL = 300  # Cache time - 5 minutes
###──────────────────────────────────────────────────────────Key Templates──────────────────────────────────────────────────────────###
_BIRTHDAYS_ALL = "birthdays:all"
_BIRTHDAYS_BY_WS = lambda ws_id: f"birthdays:ws:{ws_id}"
_USERS_ALL = "users:all"
_WORKSPACES_ALL = "workspaces:all"

###──────────────────────────────────────────────────────────Helper Functions for caching──────────────────────────────────────────────────────────###
#─────────────────────────────_serialize helper─────────────────────────────
def _serialise(items: Sequence[Any]) -> str: # Return a JSON string, converting SQLModel/Pydantic objects to dict
    def to_dict(x: Any) -> Any:
        return x.dict() if hasattr(x, "dict") else x
    return json.dumps([to_dict(i) for i in items], default=str)

#─────────────────────────────_deserialize helper─────────────────────────────
def _deserialise(raw: Optional[str]) -> Optional[List[Dict[str, Any]]]: # String to list
    return json.loads(raw) if raw else None

#─────────────────────────────_safe_get helper─────────────────────────────
def _safe_get(key: str) -> Optional[str]: # Catch on error to log a failed GET
    try:
        return redis.get(key)
    except RedisError as e:
        logger.warning("Redis GET %s failed: %s", key, e)
        return None

#─────────────────────────────_safe_set helper─────────────────────────────
def _safe_set(key: str, payload: str, ttl: int = CACHE_TTL) -> None: # Catch on error to log a failed SET
    try:
        redis.set(key, payload, ex=ttl)
    except RedisError as e:
        logger.warning("Redis SET %s failed: %s", key, e)

#─────────────────────────────_safe_del helper─────────────────────────────
def _safe_del(key: str) -> None: # Catch on error to log a failed DELETE
    try:
        redis.delete(key)
    except RedisError as e:
        logger.warning("Redis DEL %s failed: %s", key, e)
 
###──────────────────────────────────────────────────────────Birthdays (all)──────────────────────────────────────────────────────────###
#─────────────────────────────GET cached birthdays (all)─────────────────────────────
def get_cached_birthdays_all() -> Optional[List[Dict[str, Any]]]:
    return _deserialise(_safe_get(_BIRTHDAYS_ALL))

#  ─────────────────────────────SET cached birthdays (all)─────────────────────────────
def set_cached_birthdays_all(items: Sequence[Any], ttl: int = CACHE_TTL) -> None:
    _safe_set(_BIRTHDAYS_ALL, _serialise(items), ttl)
    logger.info("Cached %d birthdays (all workspaces)", len(items))

#  ─────────────────────────────DELETE cached birthdays (all)─────────────────────────────
def invalidate_birthdays_all() -> None:
    _safe_del(_BIRTHDAYS_ALL)
    logger.info("Invalidated birthdays:all cache")

### ──────────────────────────────────────────────────────────Birthdays – per workspace──────────────────────────────────────────────────────────###
#─────────────────────────────GET cached birthdays (workspace)─────────────────────────────
def get_cached_birthdays_by_workspace(workspace_id: UUID) -> Optional[List[Dict[str, Any]]]:
    return _deserialise(_safe_get(_BIRTHDAYS_BY_WS(workspace_id)))

#─────────────────────────────SET cached birthdays (workspace)─────────────────────────────
def set_cached_birthdays_by_workspace(workspace_id: UUID,
                                      items: Sequence[Any],
                                      ttl: int = CACHE_TTL) -> None:
    _safe_set(_BIRTHDAYS_BY_WS(workspace_id), _serialise(items), ttl)
    logger.info("Cached %d birthdays for workspace %s", len(items), workspace_id)

#─────────────────────────────DELETE cached birthdays (workspace)─────────────────────────────
def invalidate_birthdays_by_workspace(workspace_id: UUID) -> None:
    _safe_del(_BIRTHDAYS_BY_WS(workspace_id))
    logger.info("Invalidated birthday cache for workspace %s", workspace_id)


### ──────────────────────────────────────────────────────────Users (all)──────────────────────────────────────────────────────────###
#─────────────────────────────GET cached users (all)─────────────────────────────
def get_cached_users_all() -> Optional[List[Dict[str, Any]]]:
    return _deserialise(_safe_get(_USERS_ALL))

#─────────────────────────────SET cached users (all)─────────────────────────────
def set_cached_users_all(items: Sequence[Any], ttl: int = CACHE_TTL) -> None:
    _safe_set(_USERS_ALL, _serialise(items), ttl)
    logger.info("Cached %d users", len(items))

#─────────────────────────────DELETE cached users (all)─────────────────────────────
def invalidate_users_cache_all() -> None:
    _safe_del(_USERS_ALL)
    logger.info("Invalidated users:all cache")

### ──────────────────────────────────────────────────────────Workspaces (all)──────────────────────────────────────────────────────────###
#─────────────────────────────GET cached workspaces (all)─────────────────────────────
def get_cached_workspaces() -> Optional[List[Dict[str, Any]]]:
    return _deserialise(_safe_get(_WORKSPACES_ALL))

#─────────────────────────────SET cached workspaces (all)─────────────────────────────
def set_cached_workspaces(items: Sequence[Any], ttl: int = CACHE_TTL) -> None:
    _safe_set(_WORKSPACES_ALL, _serialise(items), ttl)
    logger.info("Cached %d workspaces", len(items))

#─────────────────────────────GET cached workspaces (all)─────────────────────────────
def invalidate_workspaces_cache() -> None:
    _safe_del(_WORKSPACES_ALL)
    logger.info("Invalidated workspaces:all cache")