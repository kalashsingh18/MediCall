import enum
import uuid
from datetime import date
from sqlalchemy import String, ForeignKey, Enum, Date, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class WaitlistStatus(str, enum.Enum):
    waiting = "waiting"
    notified = "notified"
    claimed = "claimed"
    expired = "expired"


class Waitlist(Base):
    __tablename__ = "waitlist"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id: Mapped[str] = mapped_column(String, ForeignKey("patients.id"))
    doctor_id: Mapped[str] = mapped_column(String, ForeignKey("doctors.id"))
    preferred_date: Mapped[date] = mapped_column(Date, index=True)
    status: Mapped[WaitlistStatus] = mapped_column(
        Enum(WaitlistStatus), default=WaitlistStatus.waiting
    )
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    patient: Mapped["Patient"] = relationship("Patient")
    doctor: Mapped["Doctor"] = relationship("Doctor")
