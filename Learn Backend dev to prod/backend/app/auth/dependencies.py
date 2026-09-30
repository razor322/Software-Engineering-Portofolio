"""Reusable authorization dependencies (Phase 04).

Every protected endpoint composes two things:

    authenticate  →  who is this?      (get_current_user, Phase 03)
    authorize     →  may they do this? (require_permissions, here)

Keeping them separate means a route can ask for exactly the permission it needs
instead of hard-coding role names, so renaming a role never touches a route.
"""

from typing import Annotated

from fastapi import Depends, HTTPException, status

from app.auth.models import User
from app.auth.router import get_current_user
from app.core.permissions import Permission, missing_permissions

CurrentUser = Annotated[User, Depends(get_current_user)]

FORBIDDEN_MESSAGE = "You do not have permission to perform this action."


def require_permissions(*required: Permission):
    """Build a dependency that admits only users holding *all* required permissions."""

    async def dependency(user: CurrentUser) -> User:
        if missing_permissions(user, required):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=FORBIDDEN_MESSAGE)
        return user

    return dependency
