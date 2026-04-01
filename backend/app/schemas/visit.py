from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel


class VisitBase(BaseModel):
    appointment_id: Optional[str] = None
    patient_id: str
    doctor_id: str
    bp_systolic: Optional[int] = None
    bp_diastolic: Optional[int] = None
    weight_kg: Optional[float] = None
    temperature_f: Optional[float] = None
    spo2: Optional[int] = None
    pulse: Optional[int] = None
    chief_complaint: Optional[str] = None
    diagnosis: Optional[str] = None
    clinical_notes: Optional[str] = None
    investigations: Optional[str] = None
    follow_up_date: Optional[date] = None


class VisitCreate(VisitBase):
    pass


class VisitUpdate(BaseModel):
    bp_systolic: Optional[int] = None
    bp_diastolic: Optional[int] = None
    weight_kg: Optional[float] = None
    temperature_f: Optional[float] = None
    spo2: Optional[int] = None
    pulse: Optional[int] = None
    chief_complaint: Optional[str] = None
    diagnosis: Optional[str] = None
    clinical_notes: Optional[str] = None
    investigations: Optional[str] = None
    follow_up_date: Optional[date] = None


class VisitResponse(VisitBase):
    id: str
    clinic_id: str
    visit_date: datetime
    created_at: datetime

    class Config:
        from_attributes = True
