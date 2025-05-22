# app/schemas.py
from datetime import date
from uuid import UUID
from pydantic import BaseModel, constr

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class ProfileCreate(BaseModel):
    username: constr(min_length=3, max_length=30)
    password: constr(min_length=8)
    email: constr(regex=r"^[^@]+@[^@]+\.[^@]+$")
    
class ProfileRead(BaseModel):
    id: UUID
    username: str
    email: str
    created_at: date

class BirthdayRead(BaseModel):
    id: UUID
    name: str
    date_of_birth: date
