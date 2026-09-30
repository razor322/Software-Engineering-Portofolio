"""Test bootstrap.

Runs at import time, before any app module is imported, because
`app.core.database` builds its engine at import time from the settings.

Order matters:
  1. force ENVIRONMENT=test (picks NullPool, no Secure cookie)
  2. derive a separate test database from the configured one
  3. create that database if it is missing and migrate it
  4. only then import the app
"""

import asyncio
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
TEST_DB_NAME = "officehub_test"

os.environ["ENVIRONMENT"] = "test"

from sqlalchemy.engine import make_url

from app.core.config import get_settings

_base_url = get_settings().database_url
_test_url = f"{_base_url.rsplit('/', 1)[0]}/{TEST_DB_NAME}"
os.environ["DATABASE_URL"] = _test_url

# reset the cached settings so the engine picks up the test database
get_settings.cache_clear()

import asyncpg
import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import delete, insert, select, update

from app.audit.models import AuditLog
from app.auth.models import Role, RoleName, Session, User, user_roles
from app.bookings.models import Booking
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.main import app
from app.rooms.models import Room, RoomStatus

DEV_EMAIL = "tester@officehub.dev"
DEV_PASSWORD = "TestPass123!"


def _bootstrap_database() -> None:
    async def _run() -> None:
        url = make_url(_test_url)
        admin = await asyncpg.connect(
            user=url.username,
            password=url.password,
            host=url.host,
            port=url.port or 5432,
            database="postgres",
        )
        try:
            exists = await admin.fetchval("SELECT 1 FROM pg_database WHERE datname = $1", TEST_DB_NAME)
            if not exists:
                await admin.execute(f'CREATE DATABASE "{TEST_DB_NAME}"')
        finally:
            await admin.close()

    asyncio.run(_run())
    command.upgrade(Config(str(BACKEND_ROOT / "alembic.ini")), "head")


_bootstrap_database()


def run(coro):
    """TestClient drives the app in its own event loop; helper work needs a fresh one."""
    return asyncio.run(coro)


async def _reset_state() -> None:
    """Each test starts from the same auth state (roles are static, so only re-seed them)."""
    async with SessionLocal() as session:
        await session.execute(delete(Booking))
        await session.execute(delete(AuditLog))
        await session.execute(delete(Session))
        await session.execute(delete(user_roles))
        await session.execute(delete(User))
        await session.execute(delete(Room))
        await session.execute(delete(Role))
        await session.execute(insert(Role), [{"name": name.value} for name in RoleName])
        await session.commit()


async def _create_user(
    email: str = DEV_EMAIL,
    password: str = DEV_PASSWORD,
    active: bool = True,
    role: RoleName = RoleName.EMPLOYEE,
) -> str:
    async with SessionLocal() as session:
        role_id = await session.scalar(select(Role.id).where(Role.name == role))
        user = User(email=email, name="Test User", password_hash=hash_password(password), is_active=active)
        session.add(user)
        await session.flush()
        await session.execute(insert(user_roles), [{"user_id": user.id, "role_id": role_id}])
        await session.commit()
        return user.id


async def _expire_all_sessions() -> None:
    async with SessionLocal() as session:
        await session.execute(
            update(Session).values(expires_at=datetime.now(timezone.utc) - timedelta(minutes=1))
        )
        await session.commit()


@pytest.fixture(autouse=True)
def auth_state():
    run(_reset_state())
    yield
    run(_reset_state())


@pytest.fixture
def client() -> TestClient:
    # function-scoped on purpose: a session cookie must not survive into the next test
    return TestClient(app)


@pytest.fixture
def login(client: TestClient):
    def _login(email: str, password: str = DEV_PASSWORD) -> None:
        response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
        assert response.status_code == 200, response.text

    return _login


@pytest.fixture
def dev_user() -> str:
    return run(_create_user())


@pytest.fixture
def admin_user() -> str:
    return run(_create_user(email="admin@test.officehub.dev", role=RoleName.ADMIN))


@pytest.fixture
def it_support_user() -> str:
    return run(_create_user(email="support@test.officehub.dev", role=RoleName.IT_SUPPORT))


@pytest.fixture
def other_user() -> str:
    return run(_create_user(email="other@test.officehub.dev"))


@pytest.fixture
def inactive_user() -> str:
    return run(_create_user(email="disabled@officehub.dev", active=False))


async def _create_room(name: str = "Aurora", status: str = "ACTIVE") -> str:
    async with SessionLocal() as session:
        room = Room(name=name, location="3F", capacity=10, status=RoomStatus(status))
        session.add(room)
        await session.commit()
        return room.id


@pytest.fixture
def room() -> str:
    return run(_create_room())


@pytest.fixture
def inactive_room() -> str:
    return run(_create_room("Disabled", "INACTIVE"))


@pytest.fixture
def expire_sessions():
    return lambda: run(_expire_all_sessions())
