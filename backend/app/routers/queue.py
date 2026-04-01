from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from datetime import date
from app.database import get_db
from app.models.user import User
from app.models.appointment import Appointment, AppointmentStatus
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.schemas.appointment import AppointmentResponse
from app.routers.auth import get_current_user
from app.services.whatsapp_service import send_whatsapp_message

router = APIRouter(prefix="/queue", tags=["Queue"])


@router.get("/today", response_model=List[AppointmentResponse])
async def today_queue(
    doctor_id: str = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get today's queue sorted by token number."""
    today = date.today()
    query = select(Appointment).where(
        Appointment.clinic_id == current_user.clinic_id,
        Appointment.appointment_date == today,
        Appointment.status.notin_([AppointmentStatus.cancelled, AppointmentStatus.no_show])
    )
    if doctor_id:
        query = query.where(Appointment.doctor_id == doctor_id)
    query = query.order_by(Appointment.token_number)
    result = await db.execute(query)
    return result.scalars().all()


@router.put("/{appointment_id}/arrive", response_model=AppointmentResponse)
async def mark_arrived(
    appointment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark patient as arrived — moves to top of active queue."""
    result = await db.execute(
        select(Appointment).where(
            Appointment.id == appointment_id,
            Appointment.clinic_id == current_user.clinic_id
        )
    )
    appt = result.scalar_one_or_none()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    appt.status = AppointmentStatus.arrived
    
    # WhatsApp Sync for Walk-ins/Arrivals
    try:
        pat_res = await db.execute(select(Patient).where(Patient.id == appt.patient_id))
        patient = pat_res.scalar_one_or_none()
        doc_res = await db.execute(select(Doctor).where(Doctor.id == appt.doctor_id))
        doctor = doc_res.scalar_one_or_none()
        
        if patient and doctor:
            msg = (
                f"Welcome to the clinic, {patient.name}! 👋\n\n"
                f"You have been checked in for Dr. {doctor.name}.\n"
                f"Your Token Number is: #{appt.token_number}\n\n"
                f"Please wait in the lounge. We'll notify you when it's your turn."
            )
            send_whatsapp_message(patient.phone, msg)
    except Exception as e:
        print(f"Failed to send arrival WhatsApp: {e}")

    await db.commit()
    return appt


@router.put("/{appointment_id}/call", response_model=AppointmentResponse)
async def call_patient(
    appointment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Doctor calls next patient — sets to in_consultation."""
    result = await db.execute(
        select(Appointment).where(
            Appointment.id == appointment_id,
            Appointment.clinic_id == current_user.clinic_id
        )
    )
    appt = result.scalar_one_or_none()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    appt.status = AppointmentStatus.in_consultation
    return appt


@router.put("/{appointment_id}/done", response_model=AppointmentResponse)
async def mark_done(
    appointment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark consultation done."""
    result = await db.execute(
        select(Appointment).where(
            Appointment.id == appointment_id,
            Appointment.clinic_id == current_user.clinic_id
        )
    )
    appt = result.scalar_one_or_none()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    appt.status = AppointmentStatus.done
    return appt
