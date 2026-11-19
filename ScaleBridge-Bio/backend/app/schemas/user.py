from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, ConfigDict

class UserBase(BaseModel):
    email: EmailStr
    full_name: str

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class UserRead(UserBase):
    id: str
    is_active: bool
    is_superuser: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class MembershipRead(BaseModel):
    id: str
    organization_id: str
    user_id: str
    role: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
