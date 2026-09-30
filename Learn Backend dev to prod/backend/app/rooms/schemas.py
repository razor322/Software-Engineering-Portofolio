from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.rooms.models import RoomStatus


class RoomCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    location: str = Field(min_length=1, max_length=120)
    capacity: int = Field(ge=1, le=500)


class RoomUpdate(BaseModel):
    """PATCH semantics: every field is optional, but at least one must be present."""

    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    location: str | None = Field(default=None, min_length=1, max_length=120)
    capacity: int | None = Field(default=None, ge=1, le=500)
    status: RoomStatus | None = None

    def changes(self) -> dict:
        # exclude_unset keeps "field omitted" distinct from "field set to null"
        return self.model_dump(exclude_unset=True)


class RoomOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None
    location: str
    capacity: int
    status: RoomStatus
    created_at: datetime
    updated_at: datetime


class RoomResponse(BaseModel):
    data: RoomOut


class RoomListResponse(BaseModel):
    data: list[RoomOut]
