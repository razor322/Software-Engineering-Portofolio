"""The permission catalog and the role → permission mapping (Phase 04).

A permission is a verb on a resource, stored as `resource:action`. Roles are just
names; this mapping is the single place that says what a role may do.

Only permissions that something actually enforces are listed here. Rooms,
bookings, and ticketing have no endpoints yet, so inventing their permissions
now would be configuration nobody checks — they arrive with their own phases.
"""

import enum

from app.auth.models import RoleName, User


class Permission(str, enum.Enum):
    USERS_READ = "users:read"
    USERS_CREATE = "users:create"
    USERS_UPDATE = "users:update"
    USERS_DELETE = "users:delete"
    ROOMS_READ = "rooms:read"
    ROOMS_CREATE = "rooms:create"
    ROOMS_UPDATE = "rooms:update"
    ROOMS_DELETE = "rooms:delete"
    BOOKINGS_CREATE = "bookings:create"
    BOOKINGS_READ = "bookings:read"
    BOOKINGS_READ_ALL = "bookings:read:any"
    BOOKINGS_CANCEL = "bookings:cancel"
    BOOKINGS_CANCEL_ALL = "bookings:cancel:any"
    AUDIT_READ = "audit:read"


ROLE_PERMISSIONS: dict[RoleName, frozenset[Permission]] = {
    RoleName.ADMIN: frozenset(Permission),
    # ponytail: IT_SUPPORT gets nothing until ticketing lands (Phase 07)
    RoleName.IT_SUPPORT: frozenset(),
    RoleName.EMPLOYEE: frozenset(
        {
            Permission.ROOMS_READ,
            Permission.BOOKINGS_CREATE,
            Permission.BOOKINGS_READ,
            Permission.BOOKINGS_CANCEL,
        }
    ),
}


def permissions_for(user: User) -> frozenset[Permission]:
    granted: set[Permission] = set()
    for role in user.roles:
        granted |= ROLE_PERMISSIONS.get(role.name, frozenset())
    return frozenset(granted)


def missing_permissions(user: User, required: tuple[Permission, ...]) -> list[Permission]:
    granted = permissions_for(user)
    return [permission for permission in required if permission not in granted]
