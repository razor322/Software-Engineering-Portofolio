"""Room endpoints (Phase 05).

Two different audiences, one endpoint:

- anybody with `rooms:read` may **list and view** rooms
- only ADMIN (`rooms:create` / `rooms:update` / `rooms:delete`) may change them

Employees see ACTIVE rooms only; admins see everything, because a disabled room
still matters when you are the one who has to find out why it disappeared.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_permissions
from app.auth.models import User
from app.core.database import get_session
from app.core.permissions import Permission, permissions_for
from app.rooms import repository
from app.rooms.schemas import RoomCreate, RoomListResponse, RoomResponse, RoomUpdate

router = APIRouter(prefix="/rooms", tags=["rooms"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]
CanReadRooms = Annotated[User, Depends(require_permissions(Permission.ROOMS_READ))]
CanCreateRooms = Annotated[User, Depends(require_permissions(Permission.ROOMS_CREATE))]
CanUpdateRooms = Annotated[User, Depends(require_permissions(Permission.ROOMS_UPDATE))]
CanDeleteRooms = Annotated[User, Depends(require_permissions(Permission.ROOMS_DELETE))]


async def _require_room(session: AsyncSession, room_id: str):
    room = await repository.get_room(session, room_id)
    if room is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found.")
    return room


@router.get("", response_model=RoomListResponse)
async def list_rooms(session: SessionDep, current: CanReadRooms):
    # whoever may change rooms also needs to see the disabled ones
    only_active = Permission.ROOMS_UPDATE not in permissions_for(current)
    rooms = await repository.list_rooms(session, only_active=only_active)
    return RoomListResponse(data=rooms)


@router.post("", response_model=RoomResponse, status_code=status.HTTP_201_CREATED)
async def create_room(payload: RoomCreate, session: SessionDep, _: CanCreateRooms):
    room = await repository.create_room(session, payload.model_dump())
    return RoomResponse(data=room)


@router.get("/{room_id}", response_model=RoomResponse)
async def get_room(room_id: str, session: SessionDep, current: CanReadRooms):
    return RoomResponse(data=await _require_room(session, room_id))


@router.patch("/{room_id}", response_model=RoomResponse)
async def update_room(room_id: str, payload: RoomUpdate, session: SessionDep, _: CanUpdateRooms):
    if not payload.changes():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="No fields to update."
        )
    await _require_room(session, room_id)
    room = await repository.update_room(session, room_id, payload.changes())
    return RoomResponse(data=room)


@router.delete("/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_room(room_id: str, session: SessionDep, _: CanDeleteRooms) -> Response:
    await _require_room(session, room_id)
    await repository.delete_room(session, await repository.get_room(session, room_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
