import uuid
from datetime import datetime, date
from sqlalchemy import String, ForeignKey, Numeric, Text, Date, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Visit(Base):
    __tablename__ = "visits"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    appointment_id: Mapped[str | None] = mapped_column(String, ForeignKey("appointments.id"), nullable=True)
    patient_id: Mapped[str] = mapped_column(String, ForeignKey("patients.id"))
    doctor_id: Mapped[str] = mapped_column(String, ForeignKey("doctors.id"))
    clinic_id: Mapped[str] = mapped_column(String, ForeignKey("clinics.id"))

    # Vitals
    bp_systolic: Mapped[int | None] = mapped_column(nullable=True)
    bp_diastolic: Mapped[int | None] = mapped_column(nullable=True)
    weight_kg: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    temperature_f: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    spo2: Mapped[int | None] = mapped_column(nullable=True)
    pulse: Mapped[int | None] = mapped_column(nullable=True)

    # Clinical
    chief_complaint: Mapped[str | None] = mapped_column(Text, nullable=True)
    diagnosis: Mapped[str | None] = mapped_column(Text, nullable=True)
    clinical_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    investigations: Mapped[str | None] = mapped_column(Text, nullable=True)
    follow_up_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    visit_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    appointment: Mapped["Appointment"] = relationship("Appointment", back_populates="visit")
    patient: Mapped["Patient"] = relationship("Patient", back_populates="visits")
    doctor: Mapped["Doctor"] = relationship("Doctor")
    clinic: Mapped["Clinic"] = relationship("Clinic")
    prescription: Mapped["Prescription"] = relationship("Prescription", back_populates="visit", uselist=False)
    bill: Mapped["Bill"] = relationship("Bill", back_populates="visit", uselist=False)
