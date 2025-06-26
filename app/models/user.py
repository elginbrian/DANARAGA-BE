from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from app.models.common import IDModelMixin
from app.models.enums import Gender

class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    phone: Optional[str] = None
    age: Optional[int] = Field(None, ge=0)
    gender: Optional[Gender] = None
    ktp_number: Optional[str] = None
    address: Optional[str] = None
    bpjs_status: Optional[bool] = None
    employment_status: Optional[str] = None
    income_level: Optional[int] = None
    education_level: Optional[str] = None
    chronic_conditions: Optional[str] = None
    max_budget: Optional[int] = None
    max_distance_km: Optional[int] = None
    perusahaan: Optional[str] = None
    lamaBekerjaJumlah: Optional[str] = None
    lamaBekerjaSatuan: Optional[str] = None
    sumberPendapatanLain: Optional[str] = None
    kotaKabupaten: Optional[str] = None
    kodePos: Optional[str] = None
    provinsi: Optional[str] = None
    persetujuanAnalisisData: Optional[bool] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class UserCreate(UserBase):
    email: EmailStr
    name: str
    password: str

class UserUpdate(UserBase):
    password: Optional[str] = None

class UserInDB(IDModelMixin, UserBase):
    hashed_password: str
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None

class UserPublic(IDModelMixin, UserBase):
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None

    class Config:
        from_attributes = True