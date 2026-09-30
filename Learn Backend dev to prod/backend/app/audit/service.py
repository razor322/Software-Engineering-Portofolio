from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.models import AuditAction, AuditLog


@dataclass(frozen=True)
class AuditContext:
    """Who did it, from where, and under which request id."""

    actor_user_id: str | None
    ip_address: str | None = None
    user_agent: str | None = None
    request_id: str | None = None


async def record(
    session: AsyncSession,
    context: AuditContext,
    action: AuditAction,
    resource_type: str,
    resource_id: str,
    old_value: dict | None = None,
    new_value: dict | None = None,
) -> None:
    """Add an audit row.

    Deliberately does **not** commit: the caller owns the transaction, so an
    audit entry can never survive a failed business operation, and a business
    operation can never commit without its audit entry.
    """
    session.add(
        AuditLog(
            actor_user_id=context.actor_user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            old_value=old_value,
            new_value=new_value,
            ip_address=context.ip_address,
            user_agent=(context.user_agent or "")[:256] or None,
            request_id=context.request_id,
        )
    )
