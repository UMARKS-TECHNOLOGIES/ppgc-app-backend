from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException

from .models import Hotel, Room

async def create_hotel(db: AsyncSession, hotel_data: dict):
    """Creates a new hotel."""
    hotel = Hotel(**hotel_data)
    db.add(hotel)
    await db.commit()
    await db.refresh(hotel)
    return hotel


async def get_hotel(db: AsyncSession, hotel_id: int):
    """Fetch a hotel by ID."""
    result = await db.execute(select(Hotel).filter(Hotel.id == hotel_id))
    hotel = result.scalars().first()
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