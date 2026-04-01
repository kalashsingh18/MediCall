from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel
from app.models.patient import Gender, BloodGroup


class PatientBase(BaseModel):
    name: str
    phone: str
    dob: Optional[date] = None
    gender: Optional[Gender] = None
    blood_group: Optional[BloodGroup] = None
    address: Optional[str] = None
    email: Optional[str] = None
    allergies: Optional[str] = None


class PatientCreate(PatientBase):
    pass


class PatientUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    dob: Optional[date] = None
    gender: Optional[Gender] = None
    blood_group: Optional[BloodGroup] = None
    address: Optional[str] = None
    email: Optional[str] = None
    allergies: Optional[str] = None


class PatientResponse(PatientBase):
    id: str
    clinic_id: str
    created_at: datetime

    class Config:
        from_attributes = True
