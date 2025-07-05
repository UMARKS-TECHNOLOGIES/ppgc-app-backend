from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from ppgc_backend.app.database import get_db
from ppgc_backend.app.controllers.actors.models import User
from ppgc_backend.app.controllers.auth.services import (
    require_roles, 
)
from .schemas import HotelCreate, HotelResponse, RoomCreate, RoomResponse
from .services import create_hotel, get_hotel, create_room, get_room

router = APIRouter(prefix="/hotel", tags=["hotels"])


@router.post("/", response_model=HotelResponse, status_code=status.HTTP_201_CREATED)
async def add_hotel(
    hotel_data: HotelCreate, 
    _: User = Depends(require_roles("staff", "admin")),
    db: AsyncSession = Depends(get_db)
):
    """Create a new hotel."""
    return await create_hotel(db, hotel_data.model_dump())


@router.get("/{hotel_id}", response_model=HotelResponse)
async def fetch_hotel(
    hotel_id: int, 
    db: AsyncSession = Depends(get_db)
):
    """Get hotel details by ID."""
    return await get_hotel(db, hotel_id)


@router.post("/create-room/", response_model=RoomResponse, status_code=status.HTTP_201_CREATED)
async def add_room(
    room_data: RoomCreate, 
    _: User = Depends(require_roles("staff", "admin")),
    db: AsyncSession = Depends(get_db)
):
    """Create a new room."""
    return await create_room(db, room_data.model_dump())


@router.get("/rooms/{room_id}", response_model=RoomResponse)
async def fetch_room(room_id: int, db: AsyncSession = Depends(get_db)):
    """Get room details by ID."""
    return await get_room(db, room_id)