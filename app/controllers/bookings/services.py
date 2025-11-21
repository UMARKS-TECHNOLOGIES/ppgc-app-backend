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


async def check_room_availability(
    db: AsyncSession,
    room_id: int,
    check_in: datetime,
    check_out: datetime,
    exclude_booking_id: int = None
):
    """
    Check if a room has any overlapping bookings during the given date range.
    
    Args:
        db: Database session
        room_id: Room ID to check
        check_in: Check-in datetime
        check_out: Check-out datetime
        exclude_booking_id: Optional booking ID to exclude (for updates)
    
    Returns:
        True if room is available, False if there are conflicts
    """
    try:
        # Query for overlapping bookings
        # Bookings overlap if: check_in < other.check_out AND check_out > other.check_in
        query = select(Booking).where(
            (Booking.room_id == room_id) &
            (Booking.check_in < check_out) &
            (Booking.check_out > check_in) &
            (Booking.status != BookingStatus.canceled)
        )
        
        # Exclude the booking being updated
        if exclude_booking_id:
            query = query.where(Booking.id != exclude_booking_id)
        
        result = await db.execute(query)
        overlapping = result.scalars().first()
        
        return overlapping is None
    except Exception as e:
        d_msg = f"Error checking room availability: {e}"
        logger.error(d_msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error checking room availability"
        )


async def create_booking(db: AsyncSession, user_id: int, booking_data: BookingCreate):
    """Creates a new hotel booking with validation for room availability."""
    try:
        # Validate check-in is before check-out
        if booking_data.check_in >= booking_data.check_out:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Check-in time must be before check-out time"
            )
        
        # Check room availability
        room_available = await check_room_availability(
            db,
            booking_data.room_id,
            booking_data.check_in,
            booking_data.check_out
        )
        
        if not room_available:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Room is not available for the selected dates. Another booking already exists for this period."
            )
        
        # Create the booking with all fields
        booking = Booking(
            booker_id=user_id,
            guest_name=booking_data.guest_name,
            phone=booking_data.phone,
            email=booking_data.email,
            check_in=booking_data.check_in,
            check_out=booking_data.check_out,
            price_per_night=booking_data.price_per_night,
            paid_amount=booking_data.paid_amount,
            notes=booking_data.notes,
            room_id=booking_data.room_id,
            hotel_id=booking_data.hotel_id,
            total_number_of_days=booking_data.total_number_of_days,
            total_amount=booking_data.total_amount,
            balance_payment=booking_data.balance_payment,
            status=booking_data.status,
            guests=booking_data.guests,
            total_price=booking_data.total_amount,  # For backward compatibility
        )
        
        db.add(booking)
        await db.commit()
        await db.refresh(booking)
        
        if DEBUG:
            logger.info(f"Booking created successfully: {booking.id}")
        
        return booking
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        f_msg = 'An error occurred while creating booking.'
        d_msg = f'{f_msg} Reason: {e}'
        logger.error(d_msg)
        if DEBUG:
            print(d_msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
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
    if booking.status == 'canceled':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Booking already canceled."
        )
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
    """Update a booking with validation for room availability if dates change."""
    try:
        updates = booking_data.model_dump(exclude_unset=True)
        
        # If check_in or check_out is being updated, validate room availability
        if 'check_in' in updates or 'check_out' in updates:
            check_in = updates.get('check_in', booking.check_in)
            check_out = updates.get('check_out', booking.check_out)
            
            # Validate check-in is before check-out
            if check_in >= check_out:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Check-in time must be before check-out time"
                )
            
            # Check room availability (excluding current booking)
            room_id = updates.get('room_id', booking.room_id)
            room_available = await check_room_availability(
                db,
                room_id,
                check_in,
                check_out,
                exclude_booking_id=booking.id
            )
            
            if not room_available:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Room is not available for the selected dates."
                )
        
        # Apply updates
        for field, value in updates.items():
            if hasattr(booking, field):
                setattr(booking, field, value)
            # Also update total_price if total_amount is being updated (for backward compatibility)
            if field == 'total_amount' and hasattr(booking, 'total_price'):
                booking.total_price = value

        db.add(booking)
        await db.commit()
        await db.refresh(booking)
        
        if DEBUG:
            logger.info(f"Booking {booking.id} updated successfully")
        
        return booking
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        f_msg = 'An error occurred while updating booking.'
        d_msg = f'{f_msg} Reason: {e}'
        logger.error(d_msg)
        if DEBUG:
            print(d_msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f_msg
        )