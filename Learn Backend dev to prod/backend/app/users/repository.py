from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.models import User


async def list_users(session: AsyncSession) -> list[User]:
    result = await session.execute(select(User).options(selectinload(User.roles)).order_by(User.email))
    return list(result.scalars())
