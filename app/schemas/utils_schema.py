# /app/schemas/utils_schema.py

from typing import List, Any, Optional 
from uuid import UUID
from pydantic import BaseModel

# ─────────────────────────────Timezone model─────────────────────────────
class TimezoneList(BaseModel):
    timezones: List[str]

# ─────────────────────────────Job results model ─────────────────────────────
class JobResult(BaseModel):
    detail: str

# ─────────────────────────────Count results model─────────────────────────────
class CountResult(BaseModel):
    count: int

# ─────────────────────────────Cache results model─────────────────────────────
class CacheResult(BaseModel):
    user_id: UUID
    cached: Optional[List[dict[str, Any]]] = None

# ─────────────────────────────Cache all users model─────────────────────────────
class CacheAllUsers(BaseModel):
    users: dict[str, dict[str, Any | None]]