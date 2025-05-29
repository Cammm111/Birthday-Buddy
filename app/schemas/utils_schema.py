# /app/schemas/utils_schema.py

from typing import Any, List
from pydantic import BaseModel

class TimezoneList(BaseModel): # Used by /timezones
    timezones: List[str]

class JobResult(BaseModel): # Used by /run-birthday-job
    detail: str

class CountResult(BaseModel): # Used by /refresh-birthday-table & /backfill-birthdays
    count: int 

class CacheResult(BaseModel): # Single cache wrapper. Used by all /cache utils
    data: Any