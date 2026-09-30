from datetime import date, datetime, time, timedelta, timezone

from pydantic import BaseModel, ConfigDict, Field

from app.bookings.models import BookingStatus


class BookingCreate(BaseModel):
    room_id: str = Field(min_length=1, max_length=32)
    start_time: datetime
    end_time: datetime
    purpose: str | None = Field(default=None, max_length=255)


class BookingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    room_id: str
    user_id: str
    room_name: str | None = None
    start_time: datetime
    end_time: datetime
    purpose: str | None
    status: BookingStatus
    created_at: datetime


class BookingResponse(BaseModel):
    data: BookingOut


class BookingListResponse(BaseModel):
    data: list[BookingOut]
    meta: dict


class AvailabilityBooking(BaseModel):
    start_time: datetime
    end_time: datetime
    status: BookingStatus


class AvailabilityDay(BaseModel):
    room_id: str
    date: date
    bookings: list[AvailabilityBooking]


class AvailabilityResponse(BaseModel):
    data: AvailabilityDay


def day_bounds(day: date) -> tuple[datetime, datetime]:
    """Half-open UTC day range [00:00, next 00:00) — the same shape as the overlap constraint."""
    start = datetime.combine(day, time.min, tzinfo=timezone.utc)
    return start, start + timedelta(days=1)
