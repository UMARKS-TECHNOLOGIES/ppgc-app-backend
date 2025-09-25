# routes/property_routes.py
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, Query, status


from .services import (
    create_property,
    update_property,
    delete_property,
    get_property,
    list_properties,
)
from ppgc_backend.app.database import get_db
from ppgc_backend.app.controllers.actors.models import User
from ppgc_backend.app.controllers.auth.services import require_roles
from .schemas import PropertyCreate, PropertyUpdate, PropertyResponse


router = APIRouter(prefix="/properties", tags=["Properties"])


@router.post("/", response_model=PropertyResponse, status_code=status.HTTP_201_CREATED)
async def add_property(
    property_data: PropertyCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles("staff", "admin")),
):
    return await create_property(db, property_data)


@router.patch("/{property_id}/", response_model=PropertyResponse)
async def edit_property(
    property_id: int,
    property_data: PropertyUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles("staff", "admin")),
):
    return await update_property(db, property_id, property_data)


@router.delete("/{property_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def remove_property(
    property_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles("staff", "admin")),
):
    await delete_property(db, property_id)


@router.get("/{property_id}/", response_model=PropertyResponse)
async def fetch_property(
    property_id: int,
    db: AsyncSession = Depends(get_db),
):
    return await get_property(db, property_id)


@router.get("/", response_model=List[PropertyResponse])
async def fetch_properties(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    return await list_properties(db, skip=skip, limit=limit)
