from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.rooms.models import Room, RoomStatus


async def list_rooms(session: AsyncSession, only_active: bool = False) -> list[Room]:
    query = select(Room).order_by(Room.name)
    if only_active:
        query = query.where(Room.status == RoomStatus.ACTIVE)
    return list(await session.scalars(query))


async def get_room(session: AsyncSession, room_id: str) -> Room | None:
    return await session.scalar(select(Room).where(Room.id == room_id))


async def create_room(session: AsyncSession, values: dict) -> Room:
    room = Room(**values)
    session.add(room)
    await session.commit()
    return room


async def update_room(session: AsyncSession, room_id: str, values: dict) -> Room | None:
    if values:
        await session.execute(update(Room).where(Room.id == room_id).values(**values))
        await session.commit()
    return await get_room(session, room_id)


async def delete_room(session: AsyncSession, room: Room) -> None:
    await session.delete(room)
    await session.commit()
