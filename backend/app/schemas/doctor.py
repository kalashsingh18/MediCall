from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel


class DoctorBase(BaseModel):
    name: str
    specialization: Optional[str] = None
    degree: Optional[str] = None
    registration_number: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    consultation_fee: float = 500.0
    schedule: Optional[Dict[str, Any]] = None


class DoctorCreate(DoctorBase):
    email: str
    password: str


class DoctorUpdate(BaseModel):
    name: Optional[str] = None
    specialization: Optional[str] = None
    degree: Optional[str] = None
    registration_number: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    consultation_fee: Optional[float] = None
    schedule: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class DoctorResponse(DoctorBase):
    id: str
    clinic_id: str
    user_id: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
