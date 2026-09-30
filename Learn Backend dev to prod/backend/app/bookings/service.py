"""Booking business rules (Phase 06).

This is the first module where a transaction is not optional. Everything that
must succeed or fail together — the booking row and its audit entry — is
written between one `commit()` and one `rollback()`:

    validate room → validate time range → check room status → insert booking
    → write audit log → COMMIT

`session.commit()` rather than `async with session.begin()`: SQLAlchemy starts a
transaction implicitly on the first query, so `begin()` would raise "a
transaction is already begun" as soon as the service reads the room first.

The overlap rule itself is **not** implemented here. A `SELECT ... WHERE not
exists` check has a race: two requests can both find the slot free and both
insert. `bookings_no_overlap_per_room` is an exclusion constraint, so the
database refuses the second INSERT no matter how the requests interleave, and
this module only translates that refusal into a 409.
"""

from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.models import AuditAction
from app.audit.service import AuditContext, record
from app.bookings.models import Booking, BookingStatus
from app.core.errors import AppError
from app.rooms import repository as rooms_repository

BOOKING_CONFLICT = "The room is already booked for the requested time."
EXCLUSION_VIOLATION = "23P01"


def _conflict() -> AppError:
    return AppError(409, "BOOKING_CONFLICT", BOOKING_CONFLICT)


async def create_booking(
    session: AsyncSession,
    *,
    user_id: str,
    room_id: str,
    start_time: datetime,
    end_time: datetime,
    purpose: str | None,
    audit: AuditContext,
) -> Booking:
    try:
        room = await rooms_repository.get_room(session, room_id)
        if room is None:
            raise AppError(404, "ROOM_NOT_FOUND", "Room not found.")
        if room.status.name != "ACTIVE":
            raise AppError(409, "ROOM_INACTIVE", "This room is not available for booking.")

        if end_time <= start_time:
            raise AppError(422, "INVALID_TIME_RANGE", "end_time must be after start_time.")
        if start_time < datetime.now(timezone.utc):
            raise AppError(422, "INVALID_TIME_RANGE", "start_time cannot be in the past.")

        booking = Booking(
            room_id=room_id,
            user_id=user_id,
            start_time=start_time,
            end_time=end_time,
            purpose=purpose,
            status=BookingStatus.CONFIRMED,
        )
        session.add(booking)
        await session.flush()
        await record(
            session,
            audit,
            AuditAction.BOOKING_CREATED,
            "BOOKING",
            booking.id,
            new_value={
                "room_id": room_id,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "purpose": purpose,
            },
        )
        await session.commit()
    except IntegrityError as exc:
        # a failed insert must not leave an audit row behind claiming success
        await session.rollback()
        conflict = as_conflict(exc)
        if conflict is not None:
            raise conflict from exc
        raise
    except Exception:
        await session.rollback()
        raise

    return booking


async def cancel_booking(
    session: AsyncSession, booking: Booking, audit: AuditContext
) -> Booking:
    if booking.status is not BookingStatus.CONFIRMED:
        raise AppError(409, "BOOKING_NOT_CANCELLABLE", "Only a confirmed booking can be cancelled.")

    try:
        booking.status = BookingStatus.CANCELLED
        await session.flush()
        await record(
            session,
            audit,
            AuditAction.BOOKING_CANCELLED,
            "BOOKING",
            booking.id,
            old_value={"status": BookingStatus.CONFIRMED.value},
            new_value={"status": BookingStatus.CANCELLED.value},
        )
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    return booking


def as_conflict(exc: IntegrityError) -> AppError | None:
    """Translate the database's exclusion-constraint refusal into a 409.

    Keyed on SQLSTATE 23P01 (exclusion_violation) rather than the exception class:
    SQLAlchemy replaces asyncpg's exception with its own dialect wrapper, so the
    class you catch is never the class you expected.
    """
    if getattr(exc.orig, "sqlstate", None) == EXCLUSION_VIOLATION:
        return _conflict()
    return None
