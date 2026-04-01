from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel


class ClinicBase(BaseModel):
    name: str
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    gstin: Optional[str] = None
    logo_url: Optional[str] = None
    working_hours: Optional[Dict[str, Any]] = None


class ClinicCreate(ClinicBase):
    pass


class ClinicUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    gstin: Optional[str] = None
    logo_url: Optional[str] = None
    working_hours: Optional[Dict[str, Any]] = None


class ClinicResponse(ClinicBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True
