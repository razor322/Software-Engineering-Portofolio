"""User management endpoints (first endpoints that enforce RBAC).

Two authorization shapes live side by side here on purpose:

- a **permission** guard — "may this role list every account?"
- an **ownership** check — "may this account read *this particular* account?"

Routes ask for a permission; ownership is decided per resource, because only the
route knows what "own" means for its data.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import repository as auth_repository
from app.auth.dependencies import FORBIDDEN_MESSAGE, CurrentUser, require_permissions
from app.auth.models import User
from app.auth.schemas import UserOut
from app.core.database import get_session
from app.core.permissions import Permission, missing_permissions
from app.users import repository
from app.users.schemas import UserListResponse, UserResponse

router = APIRouter(prefix="/users", tags=["users"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]
CanReadUsers = Annotated[User, Depends(require_permissions(Permission.USERS_READ))]


def _to_out(user: User) -> UserOut:
    return UserOut(
        id=user.id,
        name=user.name,
        email=user.email,
        roles=[role.name.value for role in user.roles],
    )


@router.get("", response_model=UserListResponse)
async def list_users(session: SessionDep, _: CanReadUsers):
    return UserListResponse(data=[_to_out(user) for user in await repository.list_users(session)])


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, session: SessionDep, current: CurrentUser):
    # ownership first: reading your own account never needs a permission
    if user_id != current.id and missing_permissions(current, (Permission.USERS_READ,)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=FORBIDDEN_MESSAGE)

    user = await auth_repository.get_user_by_id(session, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return UserResponse(data=_to_out(user))
