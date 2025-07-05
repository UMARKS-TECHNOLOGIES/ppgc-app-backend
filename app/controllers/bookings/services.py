from fastapi import HTTPException
from sqlalchemy.future import select
from datetime import timedelta, timezone, datetime
from sqlalchemy.ext.asyncio import AsyncSession


from .models import Booking
from ppgc_backend.app.models import User
from .schemas import BookingCreate, BookingStatus


async def create_booking(db: AsyncSession, user_id: int, booking_data: BookingCreate):
    """Creates a new hotel booking."""
    booking = Booking(
        user_id = user_id,
        room_id = booking_data.room_id,
        check_out_date = datetime.now(timezone.utc) + timedelta(hours=booking_data.occupancy_hours),
        total_price = booking_data.total_price,
        status = booking_data.status
    )
    db.add(booking)
    await db.commit()
    await db.refresh(booking)
    return booking


async def get_booking(db: AsyncSession, booking_id: int):
    """Fetch a booking by ID."""
    result = await db.execute(select(Booking).filter(Booking.id == booking_id))
    booking = result.scalars().first()
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    if (booking.check_out < datetime.now(timezone.utc) 
        and booking.status != (BookingStatus.CANCELED or BookingStatus.COMPLETED)):
        booking.status = BookingStatus.COMPLETED
        db.add(booking)
        await db.commit()
        await db.refresh(booking)

    return booking


async def cancel_booking(db: AsyncSession, user: User, booking_id: int):
    """Cancel a booking."""
    stmt = await db.execute(
        select(Booking).filter(
            Booking.id == booking_id,
            Booking.user_id == user.id
        )
    )
    booking = stmt.scalars().first()
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found or cannot be canceled")
    
    if booking.status not in (BookingStatus.CANCELED, BookingStatus.COMPLETED):
        raise HTTPException(status_code=400, detail="Booking cannot be canceled at this stage")
    
    booking.status = BookingStatus.CANCELED
    db.add(booking)
    await db.commit()
    await db.refresh(booking)
    return booking
