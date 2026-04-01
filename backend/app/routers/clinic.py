from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.models.clinic import Clinic
from app.schemas.clinic import ClinicCreate, ClinicUpdate, ClinicResponse
from app.routers.auth import get_current_user

router = APIRouter(prefix="/clinic", tags=["Clinic"])


@router.get("", response_model=ClinicResponse)
async def get_clinic(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Clinic).where(Clinic.id == current_user.clinic_id))
    clinic = result.scalar_one_or_none()
    if not clinic:
        raise HTTPException(status_code=404, detail="Clinic not found")
    return clinic


@router.put("", response_model=ClinicResponse)
async def update_clinic(
    data: ClinicUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Clinic).where(Clinic.id == current_user.clinic_id))
    clinic = result.scalar_one_or_none()
    if not clinic:
        raise HTTPException(status_code=404, detail="Clinic not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(clinic, field, value)
    return clinic
