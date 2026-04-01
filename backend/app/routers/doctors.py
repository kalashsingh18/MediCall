from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.models.doctor import Doctor
from app.models.blocked_slot import BlockedSlot
from app.models.appointment import Appointment, AppointmentStatus
from app.schemas.doctor import DoctorCreate, DoctorUpdate, DoctorResponse
from app.core.security import hash_password
from app.routers.auth import get_current_user
from app.database import get_db
from app.models.user import User, UserRole
from pydantic import BaseModel
from datetime import date as pydate, time as pytime
import uuid

router = APIRouter(prefix="/doctors", tags=["Doctors"])


@router.get("", response_model=List[DoctorResponse])
async def list_doctors(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Doctor).where(Doctor.clinic_id == current_user.clinic_id, Doctor.is_active == True)
    )
    return result.scalars().all()


@router.post("", response_model=DoctorResponse, status_code=status.HTTP_201_CREATED)
async def create_doctor(
    data: DoctorCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Create user account for doctor
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    doctor_user = User(
        id=str(uuid.uuid4()),
        name=data.name,
        email=data.email,
        hashed_password=hash_password(data.password),
        role=UserRole.doctor,
        clinic_id=current_user.clinic_id,
    )
    db.add(doctor_user)
    await db.flush()

    doctor = Doctor(
        id=str(uuid.uuid4()),
        clinic_id=current_user.clinic_id,
        user_id=doctor_user.id,
        name=data.name,
        specialization=data.specialization,
        degree=data.degree,
        registration_number=data.registration_number,
        phone=data.phone,
        bio=data.bio,
        consultation_fee=data.consultation_fee,
        schedule=data.schedule,
    )
    db.add(doctor)
    await db.commit()
    await db.refresh(doctor)
    return doctor


@router.get("/{doctor_id}", response_model=DoctorResponse)
async def get_doctor(
    doctor_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Doctor).where(Doctor.id == doctor_id, Doctor.clinic_id == current_user.clinic_id)
    )
    doctor = result.scalar_one_or_none()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return doctor


@router.put("/{doctor_id}", response_model=DoctorResponse)
async def update_doctor(
    doctor_id: str,
    data: DoctorUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Doctor).where(Doctor.id == doctor_id, Doctor.clinic_id == current_user.clinic_id)
    )
    doctor = result.scalar_one_or_none()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(doctor, field, value)
    await db.commit()
    await db.refresh(doctor)
    return doctor


@router.delete("/{doctor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_doctor(
    doctor_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Doctor).where(Doctor.id == doctor_id, Doctor.clinic_id == current_user.clinic_id)
    )
    doctor = result.scalar_one_or_none()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    
    # Soft delete: mark as inactive instead of full deletion if they have appointments
    doctor.is_active = False
    await db.commit()
    return None
# --- Blocked Slots Management ---

class BlockSlotRequest(BaseModel):
    date: pydate
    slot_time: str # "HH:MM AM/PM"
    reason: str | None = None

@router.get("/{doctor_id}/blocked-slots")
async def get_blocked_slots(
    doctor_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(BlockedSlot).where(
            BlockedSlot.doctor_id == doctor_id, 
            BlockedSlot.clinic_id == current_user.clinic_id
        )
    )
    return result.scalars().all()

@router.post("/{doctor_id}/block-slot")
async def block_slot(
    doctor_id: str,
    data: BlockSlotRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    from datetime import datetime
    try:
        query_time = datetime.strptime(data.slot_time, "%I:%M %p").time()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid time format. Use 'HH:MM AM/PM'")

    # Check if already blocked
    existing = await db.execute(
        select(BlockedSlot).where(
            BlockedSlot.doctor_id == doctor_id,
            BlockedSlot.date == data.date,
            BlockedSlot.slot_time == query_time
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Slot already blocked")

    blocked = BlockedSlot(
        id=str(uuid.uuid4()),
        clinic_id=current_user.clinic_id,
        doctor_id=doctor_id,
        date=data.date,
        slot_time=query_time,
        reason=data.reason
    )
    db.add(blocked)
    await db.commit()
    return blocked

@router.delete("/{doctor_id}/block-slot/{slot_id}")
async def unblock_slot(
    doctor_id: str,
    slot_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(BlockedSlot).where(
            BlockedSlot.id == slot_id,
            BlockedSlot.doctor_id == doctor_id,
            BlockedSlot.clinic_id == current_user.clinic_id
        )
    )
    blocked = result.scalar_one_or_none()
    if not blocked:
        raise HTTPException(status_code=404, detail="Blocked slot not found")
    
    await db.delete(blocked)
    await db.commit()
    return {"status": "unblocked"}

@router.get("/{doctor_id}/available-slots")
async def get_available_slots(
    doctor_id: str,
    date: pydate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Doctor).where(Doctor.id == doctor_id))
    doctor = result.scalar_one_or_none()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    # Booked Slots
    appt_result = await db.execute(
        select(Appointment.slot_time).where(
            Appointment.doctor_id == doctor.id,
            Appointment.appointment_date == date,
            Appointment.status != AppointmentStatus.cancelled
        )
    )
    booked_slots = {r[0].strftime("%I:%M %p") for r in appt_result.all() if r[0]}

    # Blocked Slots
    blocked_result = await db.execute(
        select(BlockedSlot.slot_time).where(
            BlockedSlot.doctor_id == doctor.id,
            BlockedSlot.date == date
        )
    )
    blocked_slots = {r[0].strftime("%I:%M %p") for r in blocked_result.all() if r[0]}

    # Schedule
    schedule = doctor.schedule or {}
    day_name = date.strftime("%a").lower()
    if schedule and not schedule.get(day_name, True):
        return []

    start_str = schedule.get("start", "09:00")
    end_str = schedule.get("end", "20:00")
    duration = schedule.get("slot_duration_mins", 30)

    from datetime import datetime, timedelta, time as dtime
    available = []
    curr = datetime.combine(date, datetime.strptime(start_str, "%H:%M").time())
    end_time = datetime.combine(date, datetime.strptime(end_str, "%H:%M").time())
    
    break_start = dtime(13, 0)
    break_end = dtime(16, 0)
    if "break_start" in schedule:
        break_start = datetime.strptime(schedule["break_start"], "%H:%M").time()
        break_end = datetime.strptime(schedule["break_end"], "%H:%M").time()

    while curr < end_time:
        if break_start <= curr.time() < break_end:
            curr += timedelta(minutes=duration)
            continue
        
        slot_str = curr.strftime("%I:%M %p")
        if slot_str not in booked_slots and slot_str not in blocked_slots:
            available.append(slot_str)
        curr += timedelta(minutes=duration)

    return available
