from datetime import datetime, date, time
from typing import Optional, List, Any, Union
from pydantic import BaseModel, field_serializer, field_validator
from app.models.appointment import AppointmentStatus


class AppointmentBase(BaseModel):
    patient_id: str
    doctor_id: str
    appointment_date: date
    slot_time: Optional[Any] = None
    reason: Optional[str] = None
    is_walk_in: bool = False

    @field_validator("slot_time")
    @classmethod
    def parse_slot_time(cls, v: Any):
        if isinstance(v, str) and v:
            # Try parsing "HH:MM AM/PM" or "HH:MM"
            for fmt in ("%I:%M %p", "%H:%M:%S", "%H:%M"):
                try:
                    return datetime.strptime(v, fmt).time()
                except ValueError:
                    continue
        return v


class AppointmentCreate(AppointmentBase):
    pass


class AppointmentUpdate(BaseModel):
    status: Optional[AppointmentStatus] = None
    appointment_date: Optional[date] = None
    doctor_id: Optional[str] = None
    slot_time: Optional[Any] = None
    reason: Optional[str] = None
    notes: Optional[str] = None
    token_number: Optional[int] = None

    @field_validator("slot_time")
    @classmethod
    def parse_slot_time(cls, v: Any):
        if isinstance(v, str) and v:
            for fmt in ("%I:%M %p", "%H:%M:%S", "%H:%M"):
                try:
                    return datetime.strptime(v, fmt).time()
                except ValueError:
                    continue
        return v


class AppointmentResponse(AppointmentBase):
    id: str
    clinic_id: str
    token_number: Optional[int] = None
    status: AppointmentStatus
    created_at: datetime

    @field_serializer("slot_time")
    def serialize_slot_time(self, slot_time: Any, _info):
        if isinstance(slot_time, time):
            return slot_time.strftime("%I:%M %p")
        return slot_time

    class Config:
        from_attributes = True
