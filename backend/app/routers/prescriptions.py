from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.models.prescription import Prescription
from app.schemas.prescription import PrescriptionCreate, PrescriptionUpdate, PrescriptionResponse
from app.routers.auth import get_current_user
import uuid

router = APIRouter(prefix="/prescriptions", tags=["Prescriptions"])


@router.post("", response_model=PrescriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_prescription(
    data: PrescriptionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Check if prescription already exists for this visit
    existing = await db.execute(
        select(Prescription).where(Prescription.visit_id == data.visit_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Prescription already exists for this visit")

    prescription = Prescription(
        id=str(uuid.uuid4()),
        **data.model_dump()
    )
    db.add(prescription)
    await db.commit()
    await db.refresh(prescription)
    return prescription


@router.get("/visit/{visit_id}", response_model=PrescriptionResponse)
async def get_prescription_by_visit(
    visit_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Prescription).where(Prescription.visit_id == visit_id)
    )
    rx = result.scalar_one_or_none()
    if not rx:
        raise HTTPException(status_code=404, detail="Prescription not found")
    return rx


@router.put("/{prescription_id}", response_model=PrescriptionResponse)
async def update_prescription(
    prescription_id: str,
    data: PrescriptionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Prescription).where(Prescription.id == prescription_id)
    )
    rx = result.scalar_one_or_none()
    if not rx:
        raise HTTPException(status_code=404, detail="Prescription not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(rx, field, value)
    return rx
