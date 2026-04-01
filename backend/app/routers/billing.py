from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from app.database import get_db
from app.models.user import User
from app.models.bill import Bill, BillStatus, PaymentMode
from app.schemas.bill import BillCreate, BillUpdate, BillResponse
from app.routers.auth import get_current_user
import uuid
from datetime import datetime

router = APIRouter(prefix="/billing", tags=["Billing"])


def generate_bill_number() -> str:
    now = datetime.now()
    return f"INV-{now.strftime('%Y%m%d')}-{str(uuid.uuid4())[:4].upper()}"


@router.get("", response_model=List[BillResponse])
async def list_bills(
    patient_id: Optional[str] = Query(None),
    status: Optional[BillStatus] = Query(None),
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(Bill).where(Bill.clinic_id == current_user.clinic_id)
    if patient_id:
        query = query.where(Bill.patient_id == patient_id)
    if status:
        query = query.where(Bill.status == status)
    query = query.offset(skip).limit(limit).order_by(Bill.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=BillResponse, status_code=status.HTTP_201_CREATED)
async def create_bill(
    data: BillCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    subtotal = sum(item.get("amount", 0) for item in data.items)
    discount = data.discount or 0
    gst_amount = (subtotal - discount) * (data.gst_percent / 100)
    total = subtotal - discount + gst_amount

    paid_amount = total if data.payment_mode != PaymentMode.pending else 0
    bill_status = BillStatus.paid if paid_amount >= total else (
        BillStatus.partial if paid_amount > 0 else BillStatus.unpaid
    )

    bill = Bill(
        id=str(uuid.uuid4()),
        clinic_id=current_user.clinic_id,
        patient_id=data.patient_id,
        visit_id=data.visit_id,
        items=data.items,
        subtotal=subtotal,
        discount=discount,
        total=total,
        paid_amount=paid_amount,
        payment_mode=data.payment_mode,
        gst_percent=data.gst_percent,
        status=bill_status,
        bill_number=generate_bill_number(),
    )
    db.add(bill)
    await db.commit()
    await db.refresh(bill)
    return bill


@router.get("/{bill_id}", response_model=BillResponse)
async def get_bill(
    bill_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Bill).where(Bill.id == bill_id, Bill.clinic_id == current_user.clinic_id)
    )
    bill = result.scalar_one_or_none()
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    return bill


@router.put("/{bill_id}/pay", response_model=BillResponse)
async def record_payment(
    bill_id: str,
    data: BillUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Bill).where(Bill.id == bill_id, Bill.clinic_id == current_user.clinic_id)
    )
    bill = result.scalar_one_or_none()
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(bill, field, value)
    # Auto-update status
    if bill.paid_amount >= bill.total:
        bill.status = BillStatus.paid
    elif bill.paid_amount > 0:
        bill.status = BillStatus.partial
    return bill
