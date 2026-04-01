import enum
import uuid
from datetime import datetime, date
from sqlalchemy import String, ForeignKey, Enum, Date, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Gender(str, enum.Enum):
    male = "male"
    female = "female"
    other = "other"


class BloodGroup(str, enum.Enum):
    A_pos = "A+"
    A_neg = "A-"
    B_pos = "B+"
    B_neg = "B-"
    AB_pos = "AB+"
    AB_neg = "AB-"
    O_pos = "O+"
    O_neg = "O-"
    unknown = "unknown"


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    clinic_id: Mapped[str] = mapped_column(String, ForeignKey("clinics.id"))
    name: Mapped[str] = mapped_column(String(100))
    phone: Mapped[str] = mapped_column(String(15), index=True)
    dob: Mapped[date | None] = mapped_column(Date, nullable=True)
    gender: Mapped[Gender | None] = mapped_column(Enum(Gender), nullable=True)
    blood_group: Mapped[BloodGroup | None] = mapped_column(Enum(BloodGroup), nullable=True, default=BloodGroup.unknown)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    email: Mapped[str | None] = mapped_column(String(150), nullable=True)
    allergies: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    clinic: Mapped["Clinic"] = relationship("Clinic", back_populates="patients")
    appointments: Mapped[list["Appointment"]] = relationship("Appointment", back_populates="patient")
    visits: Mapped[list["Visit"]] = relationship("Visit", back_populates="patient")
    bills: Mapped[list["Bill"]] = relationship("Bill", back_populates="patient")
