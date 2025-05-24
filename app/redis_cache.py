# app/redis_cache.py
import os
from redis.asyncio import Redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Async Redis client singleton
redis_client = Redis.from_url(REDIS_URL, decode_responses=True)
