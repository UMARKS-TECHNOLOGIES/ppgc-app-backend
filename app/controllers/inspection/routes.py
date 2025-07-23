from typing import List
from fastapi import Query
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException, status

from .models import Inspection
from ppgc_backend.app.models import User
from ppgc_backend.app.database import get_db
from .schemas import InspectionCreate, InspectionResponse, InspectionUpdate
from ppgc_backend.app.controllers.auth.services import decode_user_from_token, require_roles

router = APIRouter(prefix="/inspections", tags=["Inspections"])


@router.post("/", response_model=InspectionResponse, status_code=status.HTTP_201_CREATED)
async def create_inspection(
    inspection_data: InspectionCreate, 
    db: AsyncSession = Depends(get_db),
    user: User = Depends(decode_user_from_token)
):
    inspection = Inspection(
        **inspection_data.model_dump(),
        requester_id = user.id,
    )
    db.add(inspection)
    await db.commit()
    await db.refresh(inspection)
    return inspection


@router.get("/all", response_model=List[InspectionResponse])
async def list_all_inspections(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles("staff", "admin")),
):
    offset = (page - 1) * size

    inspections = await db.execute(
        select(Inspection)
        .options(
            selectinload(Inspection.requester),
            selectinload(Inspection.asset)
        )
        .order_by(Inspection.id.desc())
        .offset(offset)
        .limit(size)
    )
    return inspections.scalars().all()


@router.get("/my-inspections", response_model=List[InspectionResponse])
async def list_user_inspections(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(decode_user_from_token),
):
    offset = (page - 1) * size

    inspections = await db.execute(
        select(Inspection)
        .where(Inspection.requester_id == user.id)
        .options(
            selectinload(Inspection.requester),
            selectinload(Inspection.asset)
        )
        .order_by(Inspection.id.desc())
        .offset(offset)
        .limit(size)
    )
    return inspections.scalars().all()



@router.get("/{inspection_id}", response_model=InspectionResponse)
async def get_inspection(
    inspection_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(decode_user_from_token)
):
    # Fetch the inspection
    inspection = await db.get(Inspection, inspection_id)

    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection not found")

    # Permission check: must be owner or staff/admin
    if user.user_role == "user":
        if inspection.requester_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to view this inspection."
            )

    return inspection


@router.delete("/{inspection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_inspection(
    inspection_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(decode_user_from_token)
):
    inspection = await db.get(Inspection, inspection_id)
    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection not found")

    is_owner = inspection.requester_id == user.id
    is_admin_or_staff = user.user_role in ("admin", "staff")

    if not (is_owner or is_admin_or_staff):
        raise HTTPException(status_code=403, detail="Not authorized to delete this inspection")

    await db.delete(inspection)
    await db.commit()


@router.patch("/{inspection_id}", response_model=InspectionResponse)
async def update_inspection(
    inspection_id: int,
    update_data: InspectionUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(decode_user_from_token)
):
    inspection = await db.get(Inspection, inspection_id)
    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection not found")

    is_owner = inspection.requester_id == user.id
    is_admin_or_staff = user.user_role in ("admin", "staff")

    if not (is_owner or is_admin_or_staff):
        raise HTTPException(status_code=403, detail="Not authorized to update this inspection")

    if inspection.status != "pending":
        raise HTTPException(
            status_code=400,
            detail="Only inspections with status 'pending' can be modified"
        )

    for field, value in update_data.model_dump(exclude_unset=True).items():
        setattr(inspection, field, value)

    await db.commit()
    await db.refresh(inspection)
    return inspection
