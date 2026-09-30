from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.models import AuditAction, AuditLog
from app.auth.dependencies import require_permissions
from app.core.database import get_session
from app.core.permissions import Permission

router = APIRouter(prefix="/audit-logs", tags=["audit"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]
CanReadAudit = Annotated[object, Depends(require_permissions(Permission.AUDIT_READ))]


@router.get("")
async def list_audit_logs(
    session: SessionDep,
    _: CanReadAudit,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=200)] = 50,
    action: AuditAction | None = None,
    resource_type: str | None = None,
    actor_user_id: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
):
    query = select(AuditLog).order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
    if action is not None:
        query = query.where(AuditLog.action == action)
    if resource_type:
        query = query.where(AuditLog.resource_type == resource_type)
    if actor_user_id:
        query = query.where(AuditLog.actor_user_id == actor_user_id)
    if date_from is not None:
        query = query.where(AuditLog.created_at >= date_from)
    if date_to is not None:
        query = query.where(AuditLog.created_at <= date_to)

    total = await session.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = list(await session.scalars(query.offset((page - 1) * page_size).limit(page_size)))
    return {
        "data": [
            {
                "id": row.id,
                "actor_user_id": row.actor_user_id,
                "action": row.action.value,
                "resource_type": row.resource_type,
                "resource_id": row.resource_id,
                "old_value": row.old_value,
                "new_value": row.new_value,
                "request_id": row.request_id,
                "created_at": row.created_at,
            }
            for row in rows
        ],
        "meta": {"page": page, "page_size": page_size, "total": total},
    }
