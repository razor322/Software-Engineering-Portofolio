from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import repository
from app.auth.models import Session, User
from app.core import security
from app.core.config import get_settings

# FR-AUTH-002: one message for both cases, so the response never reveals whether
# the email exists or the password was wrong.
INVALID_CREDENTIALS = "Invalid email or password."


def _unauthorized(detail: str = INVALID_CREDENTIALS) -> HTTPException:
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


async def authenticate(session: AsyncSession, email: str, password: str) -> User:
    user = await repository.get_user_by_email(session, email)
    if user is None or not security.verify_password(password, user.password_hash):
        raise _unauthorized()
    if not user.is_active:
        raise _unauthorized()
    return user


async def start_session(session: AsyncSession, user: User) -> str:
    """Create a session row and return the raw token that goes into the cookie."""
    settings = get_settings()
    raw_token = security.new_session_token()
    await repository.create_session(
        session,
        user_id=user.id,
        token_hash=security.hash_token(raw_token),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=settings.session_ttl_hours),
    )
    return raw_token


async def resolve_session(session: AsyncSession, raw_token: str | None) -> User | None:
    """Return the session's user, or None when the token is unknown, expired or revoked.

    FR-AUTH-006: expired and revoked sessions must not authenticate anything.
    """
    if not raw_token:
        return None
    record = await repository.get_session_by_token_hash(session, security.hash_token(raw_token))
    if record is None or record.revoked_at is not None:
        return None
    expires_at = record.expires_at if record.expires_at.tzinfo else record.expires_at.replace(
        tzinfo=timezone.utc
    )
    if expires_at <= datetime.now(timezone.utc):
        return None
    user = await repository.get_user_by_id(session, record.user_id)
    return user if user and user.is_active else None


async def end_session(session: AsyncSession, raw_token: str | None) -> None:
    if not raw_token:
        return
    record: Session | None = await repository.get_session_by_token_hash(
        session, security.hash_token(raw_token)
    )
    if record is not None and record.revoked_at is None:
        await repository.revoke_session(session, record)