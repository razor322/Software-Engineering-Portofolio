from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import AuditContext
from app.auth.dependencies import CurrentUser, require_permissions
from app.auth.models import User
from app.bookings import repository, service
from app.bookings.models import Booking, BookingStatus
from app.bookings.schemas import (
    AvailabilityBooking,
    AvailabilityDay,
    AvailabilityResponse,
    BookingCreate,
    BookingListResponse,
    BookingOut,
    BookingResponse,
    day_bounds,
)
from app.core.database import get_session
from app.core.errors import AppError
from app.core.permissions import Permission, permissions_for

router = APIRouter(tags=["bookings"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]
CanCreateBooking = Annotated[User, Depends(require_permissions(Permission.BOOKINGS_CREATE))]
CanReadBookings = Annotated[User, Depends(require_permissions(Permission.BOOKINGS_READ))]
CanViewAvailability = Annotated[User, Depends(require_permissions(Permission.ROOMS_READ))]


def _to_out(booking: Booking) -> BookingOut:
    return BookingOut(
        id=booking.id,
        room_id=booking.room_id,
        user_id=booking.user_id,
        room_name=booking.room.name,
        start_time=booking.start_time,
        end_time=booking.end_time,
        purpose=booking.purpose,
        status=booking.status,
        created_at=booking.created_at,
    )


def _audit_context(request: Request, user: User) -> AuditContext:
    forwarded = request.headers.get("x-forwarded-for", "")
    return AuditContext(
        actor_user_id=user.id,
        ip_address=(forwarded.split(",")[0].strip() if forwarded else None)
        or (request.client.host if request.client else None),
        user_agent=request.headers.get("user-agent"),
        request_id=getattr(request.state, "request_id", None),
    )


@router.get("/bookings", response_model=BookingListResponse)
async def list_bookings(
    session: SessionDep,
    current: CanReadBookings,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    room_id: str | None = None,
    booking_status: Annotated[BookingStatus | None, Query(alias="status")] = None,
    day: date | None = None,
):
    day_start, day_end = day_bounds(day) if day else (None, None)
    rows, total = await repository.list_bookings(
        session,
        # an employee only ever sees their own bookings; an admin sees every one
        user_id=None
        if Permission.BOOKINGS_READ_ALL in permissions_for(current)
        else current.id,
        room_id=room_id,
        status=booking_status,
        day_start=day_start,
        day_end=day_end,
        page=page,
        page_size=page_size,
    )
    return BookingListResponse(
        data=[_to_out(row) for row in rows],
        meta={"page": page, "page_size": page_size, "total": total},
    )


@router.post("/bookings", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    payload: BookingCreate, request: Request, session: SessionDep, current: CanCreateBooking
):
    booking = await service.create_booking(
        session,
        user_id=current.id,
        room_id=payload.room_id,
        start_time=payload.start_time,
        end_time=payload.end_time,
        purpose=payload.purpose,
        audit=_audit_context(request, current),
    )
    await session.refresh(booking)
    return BookingResponse(data=_to_out(booking))


@router.delete("/bookings/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_booking(
    booking_id: str, request: Request, session: SessionDep, current: CurrentUser
) -> Response:
    booking = await repository.get_booking(session, booking_id)
    if booking is None:
        raise AppError(404, "BOOKING_NOT_FOUND", "Booking not found.")
    # ownership first: cancelling must never happen before the check passes
    if booking.user_id != current.id and Permission.BOOKINGS_CANCEL_ALL not in permissions_for(current):
        raise AppError(403, "FORBIDDEN", "You do not have permission to perform this action.")

    await service.cancel_booking(session, booking, _audit_context(request, current))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/rooms/{room_id}/availability", response_model=AvailabilityResponse)
async def room_availability(
    room_id: str,
    session: SessionDep,
    _: CanViewAvailability,
    day: Annotated[date, Query(description="UTC day, YYYY-MM-DD")],
):
    start, end = day_bounds(day)
    bookings = await repository.list_bookings_in_range(session, room_id, start, end)
    return AvailabilityResponse(
        data=AvailabilityDay(
            room_id=room_id,
            date=day,
            bookings=[
                AvailabilityBooking(start_time=b.start_time, end_time=b.end_time, status=b.status)
                for b in bookings
            ],
        )
    )
