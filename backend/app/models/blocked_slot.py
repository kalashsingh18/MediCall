import uuid
from datetime import date, time
from sqlalchemy import String, ForeignKey, Date, Time, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class BlockedSlot(Base):
    __tablename__ = "blocked_slots"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    clinic_id: Mapped[str] = mapped_column(String, ForeignKey("clinics.id"))
    doctor_id: Mapped[str] = mapped_column(String, ForeignKey("doctors.id"))
    date: Mapped[date] = mapped_column(Date, index=True)
    slot_time: Mapped[time] = mapped_column(Time)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    clinic: Mapped["Clinic"] = relationship("Clinic")
    doctor: Mapped["Doctor"] = relationship("Doctor")
