from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.ext.asyncio import AsyncSession


from ppgc_backend.app.database import get_db
from .schemas import BookingCreate, BookingResponse, BookingUpdate, BookingStatus
from ppgc_backend.app.controllers.actors.enums import UserRoleChoice
from ppgc_backend.app.controllers.auth.services import (
    decode_user_from_token,
)
from ppgc_backend.app.controllers.actors.models import User
from .services import create_booking, get_booking, cancel_booking

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post("/", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def book_hotel(
    booking_data: BookingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(decode_user_from_token)
):
    """Handles hotel bookings."""
    return await create_booking(db, current_user.id, booking_data)


@router.get("/{booking_id}", response_model=BookingResponse)
async def fetch_booking(
    booking_id: int,
    db: AsyncSession = Depends(get_db),
    _ = Depends(decode_user_from_token)
):
    """Retrieve a booking by ID."""
    return await get_booking(db, booking_id)


@router.delete("/{booking_id}", response_model=BookingResponse)
async def cancel_hotel_booking(
    booking_id: int,
    db: AsyncSession = Depends(get_db),
    user = Depends(decode_user_from_token)
):
    """Cancel a pending booking."""
    return await cancel_booking(db, user, booking_id)


@router.patch("/{booking_id}", response_model=BookingResponse)
async def patch_booking(
    booking_id: int,
    booking_data: BookingUpdate = Body(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(decode_user_from_token)
):
    booking = await get_booking(db, booking_id)
    # Only allow patch if booking is pending
    if booking.status != BookingStatus.pending:
        raise HTTPException(status_code=400, detail="Only pending bookings can be updated.")
    # Only booker, staff, or admin can patch
    if not (
        booking.booker_id == user.id
        or user.user_role in (UserRoleChoice.admin, UserRoleChoice.staff)
    ):
        raise HTTPException(status_code=403, detail="Not authorized to update this booking.")
    for field, value in booking_data.model_dump(exclude_unset=True).items():
        setattr(booking, field, value)
    db.add(booking)
    await db.commit()
    await db.refresh(booking)
    return booking