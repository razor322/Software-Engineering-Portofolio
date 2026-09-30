"""Create the roles and one development user per role.

Idempotent: safe to run repeatedly.

    uv run python -m scripts.seed_dev

The IT_SUPPORT and EMPLOYEE accounts exist so the Phase 04 role matrix can be
tried by hand, not just in tests.

Production gets its users through provisioning, never through this script.
"""

import asyncio

from sqlalchemy import select

from app.auth.models import Role, RoleName, User, user_roles
from app.core.database import SessionLocal, engine
from app.core.security import hash_password
from app.rooms.models import Room, RoomStatus

DEV_PASSWORD = "ChangeMe123!"

DEV_USERS = [
    ("admin@officehub.dev", "Dev Admin", RoleName.ADMIN),
    ("support@officehub.dev", "Dev IT Support", RoleName.IT_SUPPORT),
    ("employee@officehub.dev", "Dev Employee", RoleName.EMPLOYEE),
]

DEV_ROOMS = [
    ("Aurora", "Main town hall with projector", "3rd floor", 40),
    ("Borealis", "Small meeting room, whiteboard", "3rd floor", 6),
    ("Cassiopeia", "Focus room, no bookings over 2h", "4th floor", 2),
]


async def seed() -> None:
    async with SessionLocal() as session:
        roles: dict[RoleName, Role] = {}
        for name in RoleName:
            role = await session.scalar(select(Role).where(Role.name == name))
            if role is None:
                role = Role(name=name)
                session.add(role)
                await session.flush()
            roles[name] = role

        created: list[str] = []
        for email, name, role_name in DEV_USERS:
            if await session.scalar(select(User).where(User.email == email)):
                continue
            session.add(
                User(email=email, name=name, password_hash=hash_password(DEV_PASSWORD))
            )
            user = await session.scalar(select(User).where(User.email == email))
            await session.execute(
                user_roles.insert().values(user_id=user.id, role_id=roles[role_name].id)
            )
            created.append(f"{email} ({role_name.value})")

        if not await session.scalar(select(Room).limit(1)):
            for room_name, description, location, capacity in DEV_ROOMS:
                session.add(
                    Room(
                        name=room_name,
                        description=description,
                        location=location,
                        capacity=capacity,
                        status=RoomStatus.ACTIVE,
                    )
                )
            created.append(f"{len(DEV_ROOMS)} rooms")

        await session.commit()

    print(f"roles: {', '.join(r.value for r in RoleName)}")
    print(f"password for every dev account: {DEV_PASSWORD}")
    if created:
        print(f"created: {', '.join(created)}")
    else:
        print("all dev accounts already existed")


async def main() -> None:
    try:
        await seed()
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
