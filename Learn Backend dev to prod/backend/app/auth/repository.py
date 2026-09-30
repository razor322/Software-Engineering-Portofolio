from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.models import Role, Session, User


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    result = await session.execute(
        select(User).options(selectinload(User.roles)).where(User.email == email.lower())
    )
    return result.scalar_one_or_none()


async def get_user_by_id(session: AsyncSession, user_id: str) -> User | None:
    result = await session.execute(
        select(User).options(selectinload(User.roles)).where(User.id == user_id)
    )
    return result.scalar_one_or_none()


async def get_roles(session: AsyncSession) -> list[Role]:
    return list(await session.scalars(select(Role).order_by(Role.name)))


async def create_session(
    session: AsyncSession, user_id: str, token_hash: str, expires_at: datetime
) -> Session:
    record = Session(user_id=user_id, token_hash=token_hash, expires_at=expires_at)
    session.add(record)
    await session.commit()
    return record


async def get_session_by_token_hash(session: AsyncSession, token_hash: str) -> Session | None:
    result = await session.execute(select(Session).where(Session.token_hash == token_hash))
    return result.scalar_one_or_none()


async def revoke_session(session: AsyncSession, record: Session) -> None:
    record.revoked_at = datetime.now(timezone.utc)
    await session.commit()