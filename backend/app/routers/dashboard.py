from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import date, timedelta
from app.database import get_db
from app.models.user import User
from app.models.appointment import Appointment, AppointmentStatus
from app.models.patient import Patient
from app.models.bill import Bill, BillStatus
from app.routers.auth import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats")
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    today = date.today()
    clinic_id = current_user.clinic_id

    # Today's appointments
    total_today = await db.execute(
        select(func.count(Appointment.id)).where(
            Appointment.clinic_id == clinic_id,
            Appointment.appointment_date == today
        )
    )
    total_today_count = total_today.scalar_one() or 0

    # Patients seen today
    seen_today = await db.execute(
        select(func.count(Appointment.id)).where(
            Appointment.clinic_id == clinic_id,
            Appointment.appointment_date == today,
            Appointment.status == AppointmentStatus.done
        )
    )
    seen_today_count = seen_today.scalar_one() or 0

    # Pending today
    pending_today = await db.execute(
        select(func.count(Appointment.id)).where(
            Appointment.clinic_id == clinic_id,
            Appointment.appointment_date == today,
            Appointment.status.in_([AppointmentStatus.scheduled, AppointmentStatus.arrived])
        )
    )
    pending_today_count = pending_today.scalar_one() or 0

    # In consultation
    in_consult = await db.execute(
        select(func.count(Appointment.id)).where(
            Appointment.clinic_id == clinic_id,
            Appointment.appointment_date == today,
            Appointment.status == AppointmentStatus.in_consultation
        )
    )
    in_consult_count = in_consult.scalar_one() or 0

    # Revenue today
    revenue_today = await db.execute(
        select(func.coalesce(func.sum(Bill.total), 0)).where(
            Bill.clinic_id == clinic_id,
            func.date(Bill.created_at) == today,
            Bill.status.in_([BillStatus.paid, BillStatus.partial])
        )
    )
    revenue_today_val = float(revenue_today.scalar_one() or 0)

    # Total patients in clinic
    total_patients = await db.execute(
        select(func.count(Patient.id)).where(Patient.clinic_id == clinic_id)
    )
    total_patients_count = total_patients.scalar_one() or 0

    # Weekly appointments for chart (last 7 days)
    weekly_data = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_count = await db.execute(
            select(func.count(Appointment.id)).where(
                Appointment.clinic_id == clinic_id,
                Appointment.appointment_date == day
            )
        )
        day_revenue = await db.execute(
            select(func.coalesce(func.sum(Bill.total), 0)).where(
                Bill.clinic_id == clinic_id,
                func.date(Bill.created_at) == day,
                Bill.status.in_([BillStatus.paid, BillStatus.partial])
            )
        )
        weekly_data.append({
            "date": day.strftime("%d %b"),
            "appointments": day_count.scalar_one() or 0,
            "revenue": float(day_revenue.scalar_one() or 0)
        })

    return {
        "today": {
            "total_appointments": total_today_count,
            "patients_seen": seen_today_count,
            "pending": pending_today_count,
            "in_consultation": in_consult_count,
            "revenue": revenue_today_val,
        },
        "total_patients": total_patients_count,
        "weekly": weekly_data,
    }


from app.models.interaction import Interaction

@router.get("/ai-interactions")
async def get_ai_interactions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Fetch AI WhatsApp and Voice call logs
    """
    # In a full multi-tenant app, we would filter by clinic.
    # For now, fetch latest 50 interactions
    result = await db.execute(
        select(Interaction).order_by(Interaction.created_at.desc()).limit(50)
    )
    interactions = result.scalars().all()
    
    return [
        {
            "id": i.id,
            "patient_ph": i.patient_ph,
            "channel": i.channel,
            "transcript": i.transcript,
            "duration": i.duration,
            "created_at": i.created_at.isoformat()
        }
        for i in interactions
    ]
