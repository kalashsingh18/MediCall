from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel


class MedicineItem(BaseModel):
    name: str
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None
    notes: Optional[str] = None


class PrescriptionCreate(BaseModel):
    visit_id: str
    patient_id: str
    doctor_id: str
    medicines: Optional[List[Dict[str, Any]]] = []


class PrescriptionUpdate(BaseModel):
    medicines: Optional[List[Dict[str, Any]]] = None


class PrescriptionResponse(BaseModel):
    id: str
    visit_id: str
    patient_id: str
    doctor_id: str
    medicines: Optional[List[Dict[str, Any]]] = []
    created_at: datetime

    class Config:
        from_attributes = True
