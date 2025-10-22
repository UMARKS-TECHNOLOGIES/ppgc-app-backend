from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta, timezone, datetime
from fastapi import HTTPException, Depends, Path, status


from .models import Booking
from ppgc_backend.app.models import User
from ppgc_backend.app.initiator import logger
from ppgc_backend.app.database import get_db
from ppgc_backend.config.settings import DEBUG
from ppgc_backend.app.controllers.hotels.models import Hotel
from .schemas import BookingCreate, BookingStatus, BookingUpdate
from ppgc_backend.app.controllers.auth.services import decode_user_from_token

async def require_booking_priviledges(
    booking_id: int = Path(...),
    db: AsyncSession = Depends(get_db),
    requester: User = Depends(decode_user_from_token),
):
    booking = await db.get(Booking,booking_id)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found."
        )
    
    hotel: Hotel = booking.room.hotel
    accepted_ids = [
        booking.booker_id, # booker
        hotel.manager_id, # manager
        hotel.receptionist_id # receptionist
    ]

    logger.info(f'requester_id: {requester.id}; accepted_ids:{accepted_ids}')
    if not requester.id in accepted_ids:
        detail = "You do not have permission to perform this action"
        if DEBUG:
            logger.error(detail)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )

    return requester, booking


async def create_booking(db: AsyncSession, user_id: int, booking_data: BookingCreate):
    """Creates a new hotel booking."""
    try:
        schema_to_dict = booking_data.model_dump(exclude=["occupancy_hours"])
        booking = Booking(
            booker_id = user_id,
            check_out = datetime.now(timezone.utc) + timedelta(hours=booking_data.occupancy_hours),
            **schema_to_dict
        )
        db.add(booking)
        await db.commit()
        await db.refresh(booking)
        return booking
    except Exception as e:
        await db.rollback()
        f_msg = 'An error occurred while creating booking.'
        d_msg = f'{f_msg} Reason: {e}'
        print(d_msg)
        raise HTTPException(
            status_code=500,
            detail=f_msg
        )


async def get_all_bookings(db: AsyncSession, requester_id: int, page:int, size: int):
    """Fetch all bookings of a user."""
    try:
        offset = (page - 1) * size
        result = await db.execute(
            select(Booking)
            .where(Booking.booker_id == requester_id)
            .order_by(Booking.check_in.desc())
            .offset(offset)
            .limit(size)
        )
        booking = result.scalars().all()
        return booking
    except Exception as e:
        f_msg = 'An error occurred while fetching bookings.'
        d_msg = f'{f_msg} Reason: {e}'
        logger.error(d_msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f_msg
        )


async def cancel_booking(db: AsyncSession, booking: Booking):
    """Cancel a booking."""
    try:
        booking.status = BookingStatus.canceled
        db.add(booking)
        await db.commit()
        await db.refresh(booking)
        return booking
    except Exception as e:
        await db.rollback()
        f_msg = 'An error occurred while canceling booking.'
        d_msg = f'{f_msg} Reason: {e}'
        print(d_msg)
        raise HTTPException(
            status_code=500,
            detail=f_msg
        )


async def update_booking(db: AsyncSession, booking: Booking, booking_data: BookingUpdate):
    """Update a booking."""
    # Only allow patch if booking is pending
    if booking.status != BookingStatus.pending:
        raise HTTPException(status_code=400, detail="Only pending bookings can be updated.")
    
    try:
        for field, value in booking_data.model_dump(exclude_unset=True).items():
            setattr(booking, field, value)

        db.add(booking)
        await db.commit()
        await db.refresh(booking)
        return booking
    except Exception as e:
        await db.rollback()
        f_msg = 'An error occurred while canceling booking.'
        d_msg = f'{f_msg} Reason: {e}'
        print(d_msg)
        raise HTTPException(
            status_code=500,
            detail=f_msg
        )
