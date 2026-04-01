import enum
import uuid
from datetime import datetime
from sqlalchemy import String, Enum, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class UserRole(str, enum.Enum):
    superadmin = "superadmin"
    doctor = "doctor"
    receptionist = "receptionist"


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.receptionist)
    clinic_id: Mapped[str | None] = mapped_column(String, ForeignKey("clinics.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    clinic: Mapped["Clinic"] = relationship("Clinic", back_populates="users", foreign_keys=[clinic_id])
    doctor_profile: Mapped["Doctor"] = relationship("Doctor", back_populates="user", uselist=False)
