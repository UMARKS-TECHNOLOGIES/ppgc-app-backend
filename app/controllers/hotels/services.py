from typing import Callable
from functools import wraps
from sqlalchemy import delete
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status, Depends, Path

from .schemas import (
    RoomCreate,
    HotelCreate,
    HotelUpdate,
)
from .models import Hotel, Room
from ppgc_backend.app.models import Area
from ppgc_backend.app.database import get_db
from ppgc_backend.app.initiator import logger
from ppgc_backend.config.settings import DEBUG
from ppgc_backend.log_config.logger_config import log_error
from ppgc_backend.app.controllers.actors.models import User
from ppgc_backend.app.controllers.auth.services import require_roles 


async def require_manager(
    hotel_id: int = Path(...),
    db: AsyncSession = Depends(get_db),
    requester: User = Depends(require_roles("staff", "admin")),
):
    query = await db.execute(
        select(Hotel)
        .where(
            Hotel.id == hotel_id,
            Hotel.manager_id == requester.id
        )
    )
    hotel = query.scalars().first()

    if not hotel:
        detail = "Hotel non-existent or You do not have permission to perform this action"
        if DEBUG:
            logger.error(detail)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )

    return requester  # Optionally return for access


async def create_hotel(db: AsyncSession, hotel_data: HotelCreate, manager_id: int):
    """Creates a new hotel."""
    try:
        _hotel_data = hotel_data.model_dump()
        area_data = _hotel_data.pop('area') 
        hotel = Hotel(
            **_hotel_data,
            area = Area(**area_data),
            manager_id = manager_id
        )
        db.add(hotel)
        await db.commit()
        await db.refresh(hotel)
        return hotel
    except Exception as e:
        await db.rollback()
        f_msg = 'An error occured while creating hotel.'
        d_msg = f'{f_msg} Reason: {e}'
        #if DEBUG:
        logger.error(d_msg)
        log_error(d_msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f_msg            
        )


async def get_hotel(db: AsyncSession, hotel_id: int):
    """Fetch a hotel by ID."""
    hotel = await db.get(Hotel, hotel_id)
    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")
    return hotel


async def paginated_hotel(
    page: int,
    size: int,
    db: AsyncSession,
):
    """Get all hotels with pagination."""
    try:
        offset = (page - 1) * size
        result = await db.execute(
            select(Hotel)
            .offset(offset)
            .limit(size)
            .order_by(Hotel.id.desc())
        )
        hotels = result.scalars().all()
        return hotels
    except Exception as e:
        await db.rollback()
        f_msg = 'An error occurred while creating room.'
        d_msg = f'{f_msg} Reason: {e}'
        #if DEBUG:
        logger.error(d_msg)
        log_error(d_msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f_msg
        )


async def create_room(hotel_id: int, db: AsyncSession, room_data: dict):
    """Creates a new room in a hotel."""
    room = (await db.execute(
        select(Room)
        .where(
            Room.hotel_id == hotel_id,
            Room.room_number == room_data['room_number']
        )
    )).scalars().first()
    if room:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Duplicate room number disallowed."
        )
    
    try:
        room = Room(**room_data, hotel_id=hotel_id)
        db.add(room)
        await db.commit()
        await db.refresh(room)
        return room
    except Exception as e:
        await db.rollback()
        f_msg = 'An error occurred while creating room.'
        d_msg = f'{f_msg} Reason: {e}'
        #if DEBUG:
        logger.error(d_msg)
        log_error(d_msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f_msg
        )


async def update_hotel(db: AsyncSession, hotel_id:int, hotel_data: HotelUpdate):
    hotel = await db.get(Hotel, hotel_id)
    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")
    try:
        for field, value in hotel_data.model_dump(exclude_unset=True).items():
            setattr(hotel, field, value)
        await db.commit()
        await db.refresh(hotel)
        return hotel
    except Exception as e:
        await db.rollback()
        f_msg = 'An error occurred while updating hotel.'
        d_msg = f'{f_msg} Reason: {e}'
        #if DEBUG:
        logger.error(d_msg)
        log_error(d_msg)
        raise HTTPException(status_code=500, detail=f_msg)


async def delete_hotel(db: AsyncSession, hotel_id: int):
    hotel = await db.get(Hotel, hotel_id)
    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")
    try:
        await db.delete(hotel)
        await db.commit()
    except Exception as e:
        await db.rollback()
        f_msg = 'An error occurred while deleting hotel.'
        d_msg = f'{f_msg} Reason: {e}'
        #if DEBUG:
        logger.error(d_msg)
        log_error(d_msg)
        raise HTTPException(status_code=500, detail=f_msg)


async def delete_room(db: AsyncSession, room_id: int):
    try:
        result = await db.execute(delete(Room).where(Room.id == room_id))
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Room not found")
        await db.commit()
    except Exception as e:
        await db.rollback()
        f_msg = 'An error occurred while deleting room.'
        d_msg = f'{f_msg} Reason: {e}'
        #if DEBUG:
        logger.error(d_msg)
        log_error(d_msg)
        raise HTTPException(status_code=500, detail=f_msg)


async def get_room(db: AsyncSession, room_id: int):
    """Fetch a room by ID."""
    room = await db.get(Room,room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room


async def get_rooms(db: AsyncSession, hotel_id: int, page: int, size: int):
    try:
        offset = (page - 1) * size
        result = await db.execute(
            select(Room)
            .where(Room.hotel_id == hotel_id)
            .order_by(Room.id.desc())
            .limit(size)
            .offset(offset)
        )
        return result.scalars().all()
    except Exception as e:
        f_msg = 'An error occurred while fetching hotel rooms.'
        d_msg = f'{f_msg} Reason: {e}'
        #if DEBUG:
        logger.error(d_msg)
        log_error(d_msg)
        raise HTTPException(status_code=500, detail=f_msg)
    

async def update_room(db: AsyncSession, room_id: int, room_data: RoomCreate):
    try:
        room = await db.get(Room, room_id)
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")
        for field, value in room_data.model_dump(exclude_unset=True).items():
            setattr(room, field, value)
        await db.commit()
        await db.refresh(room)
        return room
    except Exception as e:
        await db.rollback()
        f_msg = 'An error occurred while updating room.'
        d_msg = f'{f_msg} Reason: {e}'
        #if DEBUG:
        logger.error(d_msg)
        log_error(d_msg)
        raise HTTPException(status_code=500, detail=f_msg)
