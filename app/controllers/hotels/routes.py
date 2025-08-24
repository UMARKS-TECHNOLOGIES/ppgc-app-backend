from fastapi import APIRouter, Depends, status, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

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
from .services import create_hotel, get_hotel, create_room, get_room


router = APIRouter(prefix="/hotel", tags=["hotels"])


@router.post("/", response_model=HotelResponse, status_code=status.HTTP_201_CREATED)
async def add_hotel(
    hotel_data: HotelCreate, 
    _: User = Depends(require_roles("staff", "admin")),
    db: AsyncSession = Depends(get_db)
):
    """Create a new hotel."""
    return await create_hotel(db, hotel_data)


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


@router.patch("/rooms/{room_id}", response_model=RoomResponse)
async def update_room(
    room_id: int,
    room_data: RoomCreate = Body(...),
    _: User = Depends(require_roles("staff", "admin")),
    db: AsyncSession = Depends(get_db)
):
    room = await db.get(Room, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    for field, value in room_data.model_dump(exclude_unset=True).items():
        setattr(room, field, value)
    await db.commit()
    await db.refresh(room)
    return room


@router.get("/{hotel_id}/rooms", response_model=list[RoomResponse])
async def get_hotel_rooms(hotel_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Room).where(Room.hotel_id == hotel_id))
    return result.scalars().all()


@router.delete("/rooms/{room_id}", status_code=204)
async def delete_room(
    room_id: int,
    _: User = Depends(require_roles("staff", "admin")),
    db: AsyncSession = Depends(get_db)
):
    room = await db.get(Room, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    await db.delete(room)
    await db.commit()


@router.patch("/{hotel_id}", response_model=HotelResponse)
async def update_hotel(
    hotel_id: int,
    hotel_data: HotelUpdate = Body(...),
    _: User = Depends(require_roles("staff", "admin")),
    db: AsyncSession = Depends(get_db)
):
    hotel = await db.get(Hotel, hotel_id)
    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")
    for field, value in hotel_data.model_dump(exclude_unset=True).items():
        setattr(hotel, field, value)
    await db.commit()
    await db.refresh(hotel)
    return hotel


@router.delete("/{hotel_id}", status_code=204)
async def delete_hotel(
    hotel_id: int,
    _: User = Depends(require_roles("staff", "admin")),
    db: AsyncSession = Depends(get_db)
):
    hotel = await db.get(Hotel, hotel_id)
    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")
    await db.delete(hotel)
    await db.commit()