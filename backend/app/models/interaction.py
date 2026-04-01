import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, JSON
from app.database import Base


class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_ph = Column(String, nullable=False, index=True)
    channel = Column(String, nullable=False) # "VOICE" or "WHATSAPP"
    transcript = Column(JSON, nullable=False)
    duration = Column(Integer, nullable=True) # duration in seconds if voice
    created_at = Column(DateTime, default=datetime.utcnow)
