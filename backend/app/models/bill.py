import enum
import uuid
from datetime import datetime
from sqlalchemy import String, ForeignKey, JSON, Numeric, Enum, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class PaymentMode(str, enum.Enum):
    cash = "cash"
    upi = "upi"
    card = "card"
    net_banking = "net_banking"
    pending = "pending"


class BillStatus(str, enum.Enum):
    unpaid = "unpaid"
    paid = "paid"
    partial = "partial"


class Bill(Base):
    __tablename__ = "bills"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    visit_id: Mapped[str | None] = mapped_column(String, ForeignKey("visits.id"), nullable=True, unique=True)
    patient_id: Mapped[str] = mapped_column(String, ForeignKey("patients.id"))
    clinic_id: Mapped[str] = mapped_column(String, ForeignKey("clinics.id"))
    items: Mapped[list | None] = mapped_column(JSON, nullable=True)
    # [{"description": "Consultation Fee", "amount": 500}, {"description": "ECG", "amount": 200}]
    subtotal: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    discount: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    total: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    paid_amount: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    payment_mode: Mapped[PaymentMode] = mapped_column(Enum(PaymentMode), default=PaymentMode.pending)
    status: Mapped[BillStatus] = mapped_column(Enum(BillStatus), default=BillStatus.unpaid)
    gst_percent: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    bill_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    visit: Mapped["Visit"] = relationship("Visit", back_populates="bill")
    patient: Mapped["Patient"] = relationship("Patient", back_populates="bills")
    clinic: Mapped["Clinic"] = relationship("Clinic")
