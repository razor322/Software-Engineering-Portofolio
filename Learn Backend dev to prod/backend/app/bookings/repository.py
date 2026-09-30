from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.bookings.models import Booking, BookingStatus


async def list_bookings(
    session: AsyncSession,
    *,
    user_id: str | None = None,
    room_id: str | None = None,
    status: BookingStatus | None = None,
    day_start: datetime | None = None,
    day_end: datetime | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Booking], int]:
    query = select(Booking).order_by(Booking.start_time.desc())
    if user_id is not None:
        query = query.where(Booking.user_id == user_id)
    if room_id is not None:
        query = query.where(Booking.room_id == room_id)
    if status is not None:
        query = query.where(Booking.status == status)
    if day_start is not None:
        query = query.where(Booking.start_time >= day_start)
    if day_end is not None:
        query = query.where(Booking.start_time < day_end)

    total = await session.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = list(await session.scalars(query.offset((page - 1) * page_size).limit(page_size)))
    return rows, total


async def get_booking(session: AsyncSession, booking_id: str) -> Booking | None:
    return await session.scalar(select(Booking).where(Booking.id == booking_id))


async def list_bookings_in_range(
    session: AsyncSession, room_id: str, start: datetime, end: datetime
) -> list[Booking]:
    """Confirmed bookings touching a window — what the availability view renders."""
    result = await session.execute(
        select(Booking)
        .where(
            Booking.room_id == room_id,
            Booking.start_time < end,
            Booking.end_time > start,
            Booking.status == BookingStatus.CONFIRMED,
        )
        .order_by(Booking.start_time)
    )
    return list(result.scalars())
