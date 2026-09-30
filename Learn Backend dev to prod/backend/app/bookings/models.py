from __future__ import annotations

import enum
from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import ExcludeConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base import Base
from app.rooms.models import Room


class BookingStatus(str, enum.Enum):
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: uuid4().hex)
    room_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    purpose: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[BookingStatus] = mapped_column(
        Enum(BookingStatus, native_enum=False, length=20), nullable=False, default=BookingStatus.CONFIRMED
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # joined by default: every listing shows the room name
    room: Mapped[Room] = relationship(lazy="joined")

    __table_args__ = (
        # The overlap rule is a database constraint, not application code: two
        # concurrent requests can both pass a SELECT-based check before either
        # INSERTs, and only the database can arbitrate. btree_gist provides the
        # equality operator on room_id that the range operator then needs.
        ExcludeConstraint(
            (room_id, "="),
            (func.tstzrange(start_time, end_time, "[)"), "&&"),
            using="gist",
            where=(status == BookingStatus.CONFIRMED),
            name="bookings_no_overlap_per_room",
        ),
    )
