"""Request validation schemas."""
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class RegisterIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    email: EmailStr
    password: str = Field(min_length=6, max_length=72)  # bcrypt 72-byte limit
    business_name: str = Field(min_length=1, max_length=120)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class QueueCreateIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class QueueUpdateIn(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    is_open: Optional[bool] = None


class JoinIn(BaseModel):
    customer_name: str = Field(min_length=1, max_length=80)
