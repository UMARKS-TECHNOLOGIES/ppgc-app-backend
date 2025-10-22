from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.ext.asyncio import AsyncSession

from ppgc_backend.app.database import get_db
from ppgc_backend.app.controllers.actors.models import User
from ppgc_backend.app.controllers.auth.services import (
    decode_user_from_token,
)
from ppgc_backend.app.controllers.actors.enums import UserRoleChoice
from .schemas import BookingCreate, BookingResponse, BookingUpdate, BookingStatus
from .services import create_booking, get_all_bookings, update_booking, cancel_booking, require_booking_priviledges as require_booker_rights

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post("/", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def book_hotel(
    booking_data: BookingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(decode_user_from_token)
):
    """Handles hotel bookings."""
    return await create_booking(db, current_user.id, booking_data)


@router.get("/all/", response_model=List[BookingResponse], status_code=status.HTTP_200_OK)
async def all_hotels(
    page: int = 1,
    size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(decode_user_from_token)
):
    """gets hotel bookings of current_user."""
    return await get_all_bookings(db, current_user.id, page, size)


@router.get("/{booking_id}/", response_model=BookingResponse)
async def fetch_booking(
    requester_et_booking: tuple = Depends(require_booker_rights)
):
    """Retrieve a booking by ID."""
    _, booking = requester_et_booking
    return booking


@router.delete("/{booking_id}/", response_model=BookingResponse)
async def cancel_hotel_booking(
    db: AsyncSession = Depends(get_db),
    requester_et_booking: tuple = Depends(require_booker_rights)
):
    """Cancel a pending booking."""
    _, booking = requester_et_booking
    return await cancel_booking(db, booking)


@router.patch("/{booking_id}/", response_model=BookingResponse)
async def patch_booking(
    booking_data: BookingUpdate = Body(...),
    db: AsyncSession = Depends(get_db),
    requester_et_booking: tuple = Depends(require_booker_rights)
):
    _, booking = requester_et_booking
    return await update_booking(db,booking,booking_data)
