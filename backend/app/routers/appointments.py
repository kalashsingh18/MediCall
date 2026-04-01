from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from datetime import date
from app.database import get_db
from app.models.user import User
from app.models.appointment import Appointment, AppointmentStatus
from app.schemas.appointment import AppointmentCreate, AppointmentUpdate, AppointmentResponse
from app.routers.auth import get_current_user
import uuid

router = APIRouter(prefix="/appointments", tags=["Appointments"])


@router.get("", response_model=List[AppointmentResponse])
async def list_appointments(
    appointment_date: Optional[date] = Query(None),
    doctor_id: Optional[str] = Query(None),
    status: Optional[AppointmentStatus] = Query(None),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(Appointment).where(Appointment.clinic_id == current_user.clinic_id)
    if appointment_date:
        query = query.where(Appointment.appointment_date == appointment_date)
    if doctor_id:
        query = query.where(Appointment.doctor_id == doctor_id)
    if status:
        query = query.where(Appointment.status == status)
    query = query.offset(skip).limit(limit).order_by(Appointment.slot_time)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
async def create_appointment(
    data: AppointmentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Auto-assign token number for the day
    count_result = await db.execute(
        select(func.count(Appointment.id)).where(
            Appointment.clinic_id == current_user.clinic_id,
            Appointment.appointment_date == data.appointment_date,
            Appointment.doctor_id == data.doctor_id,
        )
    )
    token_number = (count_result.scalar_one() or 0) + 1

    appointment = Appointment(
        id=str(uuid.uuid4()),
        clinic_id=current_user.clinic_id,
        token_number=token_number,
        **data.model_dump()
    )
    db.add(appointment)
    await db.commit()
    await db.refresh(appointment)
    return appointment


@router.get("/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment(
    appointment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Appointment).where(
            Appointment.id == appointment_id,
            Appointment.clinic_id == current_user.clinic_id
        )
    )
    appt = result.scalar_one_or_none()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appt


@router.put("/{appointment_id}", response_model=AppointmentResponse)
async def update_appointment(
    appointment_id: str,
    data: AppointmentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Appointment).where(
            Appointment.id == appointment_id,
            Appointment.clinic_id == current_user.clinic_id
        )
    )
    appt = result.scalar_one_or_none()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(appt, field, value)
    
    await db.commit()
    await db.refresh(appt)
    return appt


@router.delete("/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_appointment(
    appointment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Appointment).where(
            Appointment.id == appointment_id,
            Appointment.clinic_id == current_user.clinic_id
        )
    )
    appt = result.scalar_one_or_none()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    await db.delete(appt)
    await db.commit()
    return None
