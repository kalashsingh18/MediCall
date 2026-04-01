from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from app.models.bill import PaymentMode, BillStatus


class BillItem(BaseModel):
    description: str
    amount: float


class BillCreate(BaseModel):
    visit_id: Optional[str] = None
    patient_id: str
    items: List[Dict[str, Any]]
    discount: float = 0
    gst_percent: float = 0
    payment_mode: PaymentMode = PaymentMode.pending


class BillUpdate(BaseModel):
    paid_amount: Optional[float] = None
    payment_mode: Optional[PaymentMode] = None
    status: Optional[BillStatus] = None
    discount: Optional[float] = None


class BillResponse(BaseModel):
    id: str
    patient_id: str
    clinic_id: str
    visit_id: Optional[str] = None
    items: Optional[List[Dict[str, Any]]] = []
    subtotal: float
    discount: float
    total: float
    paid_amount: float
    payment_mode: PaymentMode
    status: BillStatus
    gst_percent: float
    bill_number: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
