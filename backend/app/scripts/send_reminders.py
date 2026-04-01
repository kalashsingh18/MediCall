import asyncio
import os
import sys

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from datetime import datetime, timedelta
from sqlalchemy import select, and_
from app.database import AsyncSessionLocal
from app.models.appointment import Appointment, AppointmentStatus
from app.models.patient import Patient
from app.models.doctor import Doctor
from twilio.rest import Client
from app.core.config import settings

async def send_whatsapp_reminder(phone: str, message: str):
    if not settings.TWILIO_ACCOUNT_SID or "AC" not in settings.TWILIO_ACCOUNT_SID:
        print(f"[SIMULATION] To {phone}: {message}")
        return
    try:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        client.messages.create(
            from_=settings.TWILIO_WHATSAPP_NUMBER,
            body=message,
            to=f"whatsapp:{phone}"
        )
        print(f"[SUCCESS] Sent reminder to {phone}")
    except Exception as e:
        print(f"[ERROR] Failed to send to {phone}: {e}")

async def check_and_send_reminders():
    print(f"--- Running Reminder Check at {datetime.now()} ---")
    async with AsyncSessionLocal() as session:
        now = datetime.now()
        two_hours_later = now + timedelta(hours=2)
        
        # Query appointments for today that haven't been reminded
        stmt = (
            select(Appointment, Patient, Doctor)
            .join(Patient, Appointment.patient_id == Patient.id)
            .join(Doctor, Appointment.doctor_id == Doctor.id)
            .where(
                and_(
                    Appointment.appointment_date == now.date(),
                    Appointment.status == AppointmentStatus.scheduled,
                    Appointment.reminder_sent == False
                )
            )
        )
        
        result = await session.execute(stmt)
        records = result.all()
        
        if not records:
            print("No pending reminders found.")
            return

        for appt, patient, doctor in records:
            if not appt.slot_time:
                continue

            appt_datetime = datetime.combine(appt.appointment_date, appt.slot_time)
            
            # If the appointment is within the next 2 hours
            if now < appt_datetime <= two_hours_later:
                msg = (
                    f"Hello {patient.name}! 🏥 This is a reminder for your appointment with "
                    f"Dr. {doctor.name} at {appt.slot_time.strftime('%I:%M %p')} today.\n\n"
                    f"Are you on your way? Please reply:\n"
                    f"1️⃣ - Confirming I'm coming\n"
                    f"2️⃣ - Need to reschedule"
                )
                await send_whatsapp_reminder(patient.phone, msg)
                appt.reminder_sent = True
        
        await session.commit()
    print("--- Check Complete ---")

if __name__ == "__main__":
    asyncio.run(check_and_send_reminders())
