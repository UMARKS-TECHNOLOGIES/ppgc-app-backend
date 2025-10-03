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
    try:
        inspection = Inspection(
            **inspection_data.model_dump(),
            requester_id = user.id,
        )
        db.add(inspection)
        await db.commit()
        await db.refresh(inspection)
        return inspection
    except Exception as e:
        await db.rollback()
        f_msg = 'An error occurred while creating inspection.'
        d_msg = f'{f_msg} Reason: {e}'
        print(d_msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f_msg
        )


@router.get("/all", response_model=List[InspectionResponse])
async def list_all_inspections(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles("staff", "admin")),
):
    try:
        offset = (page - 1) * size
        inspections = await db.execute(
            select(Inspection)
            .options(
                selectinload(Inspection.requester),
                selectinload(Inspection.property)
            )
            .order_by(Inspection.id.desc())
            .offset(offset)
            .limit(size)
        )
        return inspections.scalars().all()
    except Exception as e:
        f_msg = 'An error occurred while listing all inspections.'
        d_msg = f'{f_msg} Reason: {e}'
        print(d_msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f_msg
        )


@router.get("/my-inspections", response_model=List[InspectionResponse])
async def list_user_inspections(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(decode_user_from_token),
):
    try:
        offset = (page - 1) * size
        inspections = await db.execute(
            select(Inspection)
            .where(Inspection.requester_id == user.id)
            .options(
                selectinload(Inspection.requester),
                selectinload(Inspection.property)
            )
            .order_by(Inspection.id.desc())
            .offset(offset)
            .limit(size)
        )
        return inspections.scalars().all()
    except Exception as e:
        f_msg = 'An error occurred while listing user inspections.'
        d_msg = f'{f_msg} Reason: {e}'
        print(d_msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f_msg
        )



@router.get("/{inspection_id}", response_model=InspectionResponse)
async def get_inspection(
    inspection_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(decode_user_from_token)
):
    try:
        inspection = await db.get(Inspection, inspection_id)
        if not inspection:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inspection not found")
        if user.user_role == "user":
            if inspection.requester_id != user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to view this inspection."
                )
        return inspection
    except Exception as e:
        f_msg = 'An error occurred while fetching inspection.'
        d_msg = f'{f_msg} Reason: {e}'
        print(d_msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f_msg
        )


@router.delete("/{inspection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_inspection(
    inspection_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(decode_user_from_token)
):
    try:
        inspection = await db.get(Inspection, inspection_id)
        if not inspection:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inspection not found")
        is_owner = inspection.requester_id == user.id
        is_admin_or_staff = user.user_role in ("admin", "staff")
        if not (is_owner or is_admin_or_staff):
            raise HTTPException(status_code=403, detail="Not authorized to delete this inspection")
        await db.delete(inspection)
        await db.commit()
    except Exception as e:
        await db.rollback()
        f_msg = 'An error occurred while deleting inspection.'
        d_msg = f'{f_msg} Reason: {e}'
        print(d_msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f_msg
        )


@router.patch("/{inspection_id}", response_model=InspectionResponse)
async def update_inspection(
    inspection_id: int,
    update_data: InspectionUpdate,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(decode_user_from_token)
):
    try:
        inspection = await session.get(Inspection, inspection_id)
        if not inspection:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inspection not found")
        is_owner = inspection.requester_id == user.id
        is_admin_or_staff = user.user_role in ("admin", "staff")
        if not (is_owner or is_admin_or_staff):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this inspection")
        if inspection.status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only inspections with status 'pending' can be modified"
            )
        for field, value in update_data.model_dump(exclude_unset=True).items():
            setattr(inspection, field, value)
        await session.commit()
        await session.refresh(inspection)
        return inspection
    except Exception as e:
        await session.rollback()
        f_msg = 'An error occurred while updating inspection.'
        d_msg = f'{f_msg} Reason: {e}'
        print(d_msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f_msg
        )
