from fastapi import HTTPException
from sqlalchemy.future import select
from datetime import timedelta, timezone, datetime
from sqlalchemy.ext.asyncio import AsyncSession


from .models import Booking
from ppgc_backend.app.models import User
from .schemas import BookingCreate, BookingStatus


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


async def get_booking(db: AsyncSession, booking_id: int):
    """Fetch a booking by ID."""
    try:
        result = await db.execute(select(Booking).filter(Booking.id == booking_id))
        booking = result.scalars().first()
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        if (
            (booking.check_out < datetime.now(timezone.utc)) 
            and booking.status != (BookingStatus.canceled or BookingStatus.completed)
        ):
            booking.status = BookingStatus.completed
            db.add(booking)
            await db.commit()
            await db.refresh(booking)
        return booking
    except Exception as e:
        f_msg = 'An error occurred while fetching booking.'
        d_msg = f'{f_msg} Reason: {e}'
        print(d_msg)
        raise HTTPException(
            status_code=500,
            detail=f_msg
        )


async def cancel_booking(db: AsyncSession, user: User, booking_id: int):
    """Cancel a booking."""
    try:
        stmt = await db.execute(
            select(Booking).filter(
                Booking.id == booking_id,
                Booking.booker_id == user.id
            )
        )
        booking = stmt.scalars().first()
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found or cannot be canceled")
        if booking.status not in (BookingStatus.pending):
            raise HTTPException(status_code=400, detail="Booking cannot be canceled at this stage")
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
