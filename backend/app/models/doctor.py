import uuid
from datetime import datetime
from sqlalchemy import String, ForeignKey, Numeric, JSON, DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Doctor(Base):
    __tablename__ = "doctors"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    clinic_id: Mapped[str] = mapped_column(String, ForeignKey("clinics.id"))
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String(100))
    specialization: Mapped[str | None] = mapped_column(String(100), nullable=True)
    degree: Mapped[str | None] = mapped_column(String(200), nullable=True)
    registration_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(15), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    consultation_fee: Mapped[float] = mapped_column(Numeric(10, 2), default=500.0)
    schedule: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # {"mon": true, "tue": true, ..., "slot_duration_mins": 15, "start": "09:00", "end": "17:00"}
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    clinic: Mapped["Clinic"] = relationship("Clinic", back_populates="doctors")
    user: Mapped["User"] = relationship("User", back_populates="doctor_profile")
    appointments: Mapped[list["Appointment"]] = relationship("Appointment", back_populates="doctor")
