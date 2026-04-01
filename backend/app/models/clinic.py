import uuid
from datetime import datetime
from sqlalchemy import String, Text, JSON, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Clinic(Base):
    __tablename__ = "clinics"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(200))
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(15), nullable=True)
    email: Mapped[str | None] = mapped_column(String(150), nullable=True)
    gstin: Mapped[str | None] = mapped_column(String(20), nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    working_hours: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # {"mon": {"open": "09:00", "close": "18:00", "off": false}, ...}
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    users: Mapped[list["User"]] = relationship("User", back_populates="clinic", foreign_keys="User.clinic_id")
    doctors: Mapped[list["Doctor"]] = relationship("Doctor", back_populates="clinic")
    patients: Mapped[list["Patient"]] = relationship("Patient", back_populates="clinic")
