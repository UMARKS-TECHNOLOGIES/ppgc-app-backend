from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException

from .models import Hotel, Room
from .schemas import HotelCreate
from ppgc_backend.app.models import Area

async def create_hotel(db: AsyncSession, hotel_data: HotelCreate):
    """Creates a new hotel."""
    _hotel_data = hotel_data.model_dump()
    area_data = _hotel_data.pop('area') 
    hotel = Hotel(
        **_hotel_data,
        area = Area(**area_data)
    )
    db.add(hotel)
    await db.commit()
    await db.refresh(hotel)
    return hotel


async def get_hotel(db: AsyncSession, hotel_id: int):
    """Fetch a hotel by ID."""
    result = await db.execute(select(Hotel).where(Hotel.id == hotel_id))
    hotel = result.scalars().one_or_none()
    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")
    return hotel


async def create_room(db: AsyncSession, room_data: dict):
    """Creates a new room in a hotel."""
    room = Room(**room_data)
    db.add(room)
    await db.commit()
    await db.refresh(room)
    return room


async def get_room(db: AsyncSession, room_id: int):
    """Fetch a room by ID."""
    result = await db.execute(select(Room).filter(Room.id == room_id))
    room = result.scalars().first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room