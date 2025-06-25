from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from app.models.common import IDModelMixin

class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    phone: Optional[str] = None
    age: Optional[int] = Field(None, ge=0)

class UserCreate(UserBase):
    email: EmailStr
    name: str
    password: str

class UserUpdate(UserBase):
    password: Optional[str] = None

class UserInDB(IDModelMixin, UserBase):
    hashed_password: str

class UserPublic(IDModelMixin, UserBase):
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None

    class Config:
        from_attributes = True 