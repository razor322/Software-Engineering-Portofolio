"""Audit logging (Phase 06): the trail must be written, and only with the thing it describes."""

from fastapi.testclient import TestClient

from tests.test_bookings import (
    ADMIN_EMAIL,
    EMPLOYEE_EMAIL,
    OTHER_EMAIL,
    PREFIX,
    at,
    book,
    csrf,
)


def test_creating_a_booking_writes_an_audit_entry(client: TestClient, dev_user, room, login, admin_user):
    login(EMPLOYEE_EMAIL)
    created = book(client, room, at(10), at(11)).json()["data"]

    login(ADMIN_EMAIL)
    entries = client.get(f"{PREFIX}/audit-logs").json()["data"]
    entry = next(e for e in entries if e["resource_id"] == created["id"])

    assert entry["action"] == "BOOKING_CREATED"
    assert entry["resource_type"] == "BOOKING"
    assert entry["actor_user_id"] == dev_user
    assert entry["new_value"]["room_id"] == room


def test_audit_entry_carries_the_request_id(client: TestClient, dev_user, room, login, admin_user):
    login(EMPLOYEE_EMAIL)
    client.post(
        f"{PREFIX}/bookings",
        json={"room_id": room, "start_time": at(10), "end_time": at(11)},
        headers={**csrf(client), "X-Request-ID": "req_trace_123"},
    )

    login(ADMIN_EMAIL)
    entries = client.get(f"{PREFIX}/audit-logs", params={"action": "BOOKING_CREATED"}).json()["data"]

    assert entries[0]["request_id"] == "req_trace_123"


def test_a_rejected_booking_leaves_no_audit_entry(
    client: TestClient, dev_user, other_user, room, login, admin_user
):
    """The booking and its audit row share a transaction, so neither survives a failure."""
    login(EMPLOYEE_EMAIL)
    book(client, room, at(10), at(11))

    login(OTHER_EMAIL)
    assert book(client, room, at(10, 30), at(11, 30)).status_code == 409

    login(ADMIN_EMAIL)
    assert client.get(f"{PREFIX}/audit-logs").json()["meta"]["total"] == 1


def test_cancelling_a_booking_records_the_transition(client: TestClient, dev_user, room, login, admin_user):
    login(EMPLOYEE_EMAIL)
    created = book(client, room, at(10), at(11)).json()["data"]
    client.delete(f"{PREFIX}/bookings/{created['id']}", headers=csrf(client))

    login(ADMIN_EMAIL)
    entries = client.get(
        f"{PREFIX}/audit-logs",
        params={"action": "BOOKING_CANCELLED", "resource_id": created["id"]},
    ).json()["data"]

    assert entries[0]["old_value"] == {"status": "CONFIRMED"}
    assert entries[0]["new_value"] == {"status": "CANCELLED"}


def test_employee_cannot_read_audit_logs(client: TestClient, dev_user, room, login):
    login(EMPLOYEE_EMAIL)
    assert client.get(f"{PREFIX}/audit-logs").status_code == 403


def test_audit_logs_support_pagination(client: TestClient, dev_user, room, login, admin_user):
    login(EMPLOYEE_EMAIL)
    book(client, room, at(9), at(10))
    book(client, room, at(11), at(12))
    book(client, room, at(13), at(14))

    login(ADMIN_EMAIL)
    first = client.get(f"{PREFIX}/audit-logs", params={"page": 1, "page_size": 2})

    assert len(first.json()["data"]) == 2
    assert first.json()["meta"] == {"page": 1, "page_size": 2, "total": 3}
