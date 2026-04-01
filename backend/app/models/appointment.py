import enum
import uuid
from datetime import datetime, date, time
from sqlalchemy import String, ForeignKey, Enum, Date, Time, Integer, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class AppointmentStatus(str, enum.Enum):
    pending_payment = "pending_payment"
    scheduled = "scheduled"
    arrived = "arrived"
    in_consultation = "in_consultation"
    done = "done"
    no_show = "no_show"
    cancelled = "cancelled"


class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    clinic_id: Mapped[str] = mapped_column(String, ForeignKey("clinics.id"))
    patient_id: Mapped[str] = mapped_column(String, ForeignKey("patients.id"))
    doctor_id: Mapped[str] = mapped_column(String, ForeignKey("doctors.id"))
    appointment_date: Mapped[date] = mapped_column(Date, index=True)
    slot_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    token_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[AppointmentStatus] = mapped_column(
        Enum(AppointmentStatus), default=AppointmentStatus.scheduled
    )
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_walk_in: Mapped[bool] = mapped_column(default=False)
    reminder_sent: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    clinic: Mapped["Clinic"] = relationship("Clinic")
    patient: Mapped["Patient"] = relationship("Patient", back_populates="appointments")
    doctor: Mapped["Doctor"] = relationship("Doctor", back_populates="appointments")
    visit: Mapped["Visit"] = relationship("Visit", back_populates="appointment", uselist=False)
