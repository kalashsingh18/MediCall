import uuid
from datetime import datetime
from sqlalchemy import String, ForeignKey, JSON, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Prescription(Base):
    __tablename__ = "prescriptions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    visit_id: Mapped[str] = mapped_column(String, ForeignKey("visits.id"), unique=True)
    patient_id: Mapped[str] = mapped_column(String, ForeignKey("patients.id"))
    doctor_id: Mapped[str] = mapped_column(String, ForeignKey("doctors.id"))
    medicines: Mapped[list | None] = mapped_column(JSON, nullable=True)
    # [{"name": "Tab. Paracetamol 500mg", "dosage": "1-0-1", "duration": "5 days", "notes": "After food"}]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    visit: Mapped["Visit"] = relationship("Visit", back_populates="prescription")
    patient: Mapped["Patient"] = relationship("Patient")
    doctor: Mapped["Doctor"] = relationship("Doctor")
