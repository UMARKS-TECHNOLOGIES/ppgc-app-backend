from fastapi import APIRouter, Depends, status, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from .models import Room, Hotel
from ppgc_backend.app.database import get_db
from ppgc_backend.app.controllers.actors.models import User
from ppgc_backend.app.controllers.auth.services import (
    require_roles, 
)
from .schemas import (
    RoomCreate, 
    RoomResponse, 
    HotelUpdate,
    HotelCreate, 
    HotelResponse, 
)
from .services import (
    get_room,
    get_rooms,
    get_hotel,
    update_room,
    create_room, 
    delete_room,
    create_hotel,
    update_hotel,
    delete_hotel,
    paginated_hotel,
)


router = APIRouter(prefix="/hotel", tags=["hotels"])


@router.post("/", response_model=HotelResponse, status_code=status.HTTP_201_CREATED)
async def add_hotel(
    hotel_data: HotelCreate, 
    _: User = Depends(require_roles("staff", "admin")),
    db: AsyncSession = Depends(get_db)
):
    """Create a new hotel."""
    return await create_hotel(db, hotel_data)


@router.get("/all/", response_model=list[HotelResponse])
async def get_all_hotels_with_pagination(
    page: int = 1,
    size: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """Get all hotels with pagination."""
    return await paginated_hotel(page, size, db)


@router.get("/{hotel_id}/", response_model=HotelResponse)
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


@router.get("/rooms/{room_id}/", response_model=RoomResponse)
async def fetch_room(room_id: int, db: AsyncSession = Depends(get_db)):
    """Get room details by ID."""
    return await get_room(db, room_id)


@router.patch("/rooms/{room_id}/", response_model=RoomResponse)
async def update_room_endpoint(
    room_id: int,
    room_data: RoomCreate = Body(...),
    _: User = Depends(require_roles("staff", "admin")),
    db: AsyncSession = Depends(get_db)
):
    return await update_room(db, room_id, room_data)


@router.get("/{hotel_id}/rooms/", response_model=list[RoomResponse])
async def get_hotel_rooms_endpoint(hotel_id: int, db: AsyncSession = Depends(get_db)):
    return await get_rooms(db, hotel_id)


@router.delete("/rooms/{room_id}/", status_code=204)
async def delete_room_endpoint(
    room_id: int,
    _: User = Depends(require_roles("staff", "admin")),
    db: AsyncSession = Depends(get_db)
):
    return await delete_room(db, room_id)


@router.patch("/{hotel_id}/", response_model=HotelResponse)
async def update_hotel_endpoint(
    hotel_id: int,
    hotel_data: HotelUpdate = Body(...),
    _: User = Depends(require_roles("staff", "admin")),
    db: AsyncSession = Depends(get_db)
):
    return await update_hotel(db,hotel_id,hotel_data)


@router.delete("/{hotel_id}/", status_code=204)
async def delete_hotel_endpoint(
    hotel_id: int,
    _: User = Depends(require_roles("staff", "admin")),
    db: AsyncSession = Depends(get_db)
):
    return await delete_hotel(db, hotel_id)