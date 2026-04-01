from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.database import get_db
from app.models.user import User
from app.models.visit import Visit
from app.schemas.visit import VisitCreate, VisitUpdate, VisitResponse
from app.routers.auth import get_current_user
import uuid

router = APIRouter(prefix="/visits", tags=["Visits"])


@router.post("", response_model=VisitResponse, status_code=status.HTTP_201_CREATED)
async def create_visit(
    data: VisitCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    visit = Visit(
        id=str(uuid.uuid4()),
        clinic_id=current_user.clinic_id,
        **data.model_dump()
    )
    db.add(visit)
    await db.commit()
    await db.refresh(visit)
    return visit


@router.get("/patient/{patient_id}", response_model=List[VisitResponse])
async def get_patient_visits(
    patient_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Visit).where(
            Visit.patient_id == patient_id,
            Visit.clinic_id == current_user.clinic_id
        ).order_by(Visit.visit_date.desc())
    )
    return result.scalars().all()


@router.get("/{visit_id}", response_model=VisitResponse)
async def get_visit(
    visit_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Visit).where(Visit.id == visit_id, Visit.clinic_id == current_user.clinic_id)
    )
    visit = result.scalar_one_or_none()
    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found")
    return visit


@router.put("/{visit_id}", response_model=VisitResponse)
async def update_visit(
    visit_id: str,
    data: VisitUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Visit).where(Visit.id == visit_id, Visit.clinic_id == current_user.clinic_id)
    )
    visit = result.scalar_one_or_none()
    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(visit, field, value)
    return visit
