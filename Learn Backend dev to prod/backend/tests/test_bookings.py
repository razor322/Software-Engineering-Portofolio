"""Booking (Phase 06): the overlap rule, the transaction, and who may cancel."""

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from tests.conftest import _create_room, run

PREFIX = "/api/v1"
ADMIN_EMAIL = "admin@test.officehub.dev"
SUPPORT_EMAIL = "support@test.officehub.dev"
EMPLOYEE_EMAIL = "tester@officehub.dev"
OTHER_EMAIL = "other@test.officehub.dev"


def csrf(client: TestClient) -> dict[str, str]:
    return {"X-CSRF-Token": client.cookies.get("csrf_token", "")}


def at(hour: int, minute: int = 0, days: int = 1) -> str:
    """An absolute UTC timestamp, safely in the future so past-time rules never fire."""
    moment = datetime.now(timezone.utc).replace(second=0, microsecond=0) + timedelta(days=days)
    return moment.replace(hour=hour, minute=minute).isoformat()


def book(client: TestClient, room_id: str, start: str, end: str, purpose: str = "sync"):
    return client.post(
        f"{PREFIX}/bookings",
        json={"room_id": room_id, "start_time": start, "end_time": end, "purpose": purpose},
        headers=csrf(client),
    )


def test_it_support_cannot_create_a_booking(client: TestClient, it_support_user, login):
    login(SUPPORT_EMAIL)

    response = book(client, "any-room", at(10), at(11))

    assert response.status_code == 403


def test_employee_creates_a_booking(client: TestClient, dev_user, room, login):
    login(EMPLOYEE_EMAIL)

    response = book(client, room, at(10), at(11))

    assert response.status_code == 201, response.text
    body = response.json()["data"]
    assert body["status"] == "CONFIRMED"
    assert body["room_name"] == "Aurora"
    assert body["user_id"] == dev_user


def test_overlapping_booking_is_rejected(client: TestClient, dev_user, other_user, room, login):
    login(EMPLOYEE_EMAIL)
    assert book(client, room, at(10), at(11)).status_code == 201

    # a different employee, same room, overlapping slot
    login(OTHER_EMAIL)
    response = book(client, room, at(10, 30), at(11, 30))

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "BOOKING_CONFLICT"


def test_back_to_back_bookings_are_allowed(client: TestClient, dev_user, other_user, room, login):
    """[) ranges: 10:00-11:00 and 11:00-12:00 touch but do not overlap."""
    login(EMPLOYEE_EMAIL)
    assert book(client, room, at(10), at(11)).status_code == 201

    login(OTHER_EMAIL)

    assert book(client, room, at(11), at(12)).status_code == 201


def test_cancelled_booking_frees_the_slot(client: TestClient, dev_user, other_user, room, login):
    login(EMPLOYEE_EMAIL)
    created = book(client, room, at(10), at(11)).json()["data"]

    assert client.delete(f"{PREFIX}/bookings/{created['id']}", headers=csrf(client)).status_code == 204

    login(OTHER_EMAIL)
    assert book(client, room, at(10), at(11)).status_code == 201


def test_booking_in_the_past_is_rejected(client: TestClient, dev_user, room, login):
    login(EMPLOYEE_EMAIL)

    response = book(client, room, at(10, days=-2), at(11, days=-2))

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_TIME_RANGE"


def test_end_before_start_is_rejected(client: TestClient, dev_user, room, login):
    login(EMPLOYEE_EMAIL)

    response = book(client, room, at(14), at(13))

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_TIME_RANGE"


def test_unknown_room_returns_404(client: TestClient, dev_user, room, login):
    login(EMPLOYEE_EMAIL)

    response = book(client, "no-such-room", at(10), at(11))

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "ROOM_NOT_FOUND"


def test_inactive_room_cannot_be_booked(client: TestClient, dev_user, inactive_room, login):
    login(EMPLOYEE_EMAIL)

    response = book(client, inactive_room, at(10), at(11))

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "ROOM_INACTIVE"


def test_employee_sees_only_their_own_bookings(client: TestClient, dev_user, other_user, room, login):
    login(EMPLOYEE_EMAIL)
    book(client, room, at(10), at(11))
    login(OTHER_EMAIL)
    mine = book(client, room, at(12), at(13)).json()["data"]

    ids = [b["id"] for b in client.get(f"{PREFIX}/bookings").json()["data"]]

    assert ids == [mine["id"]]


def test_admin_sees_every_booking(client: TestClient, dev_user, other_user, room, login, admin_user):
    login(EMPLOYEE_EMAIL)
    book(client, room, at(10), at(11))
    login(OTHER_EMAIL)
    book(client, room, at(12), at(13))

    login(ADMIN_EMAIL)
    response = client.get(f"{PREFIX}/bookings")

    assert response.status_code == 200
    assert response.json()["meta"]["total"] == 2


def test_bookings_can_be_filtered_by_room(client: TestClient, dev_user, room, login):
    second = run(_create_room("Borealis"))
    login(EMPLOYEE_EMAIL)
    book(client, room, at(10), at(11))
    book(client, second, at(12), at(13))

    response = client.get(f"{PREFIX}/bookings", params={"room_id": second})

    assert [b["room_id"] for b in response.json()["data"]] == [second]


def test_employee_cannot_cancel_someone_elses_booking(
    client: TestClient, dev_user, other_user, room, login
):
    login(EMPLOYEE_EMAIL)
    created = book(client, room, at(10), at(11)).json()["data"]

    login(OTHER_EMAIL)
    response = client.delete(f"{PREFIX}/bookings/{created['id']}", headers=csrf(client))

    assert response.status_code == 403


def test_admin_can_cancel_any_booking(client: TestClient, dev_user, room, login, admin_user):
    login(EMPLOYEE_EMAIL)
    created = book(client, room, at(10), at(11)).json()["data"]

    login(ADMIN_EMAIL)
    response = client.delete(f"{PREFIX}/bookings/{created['id']}", headers=csrf(client))

    assert response.status_code == 204
    assert client.get(f"{PREFIX}/bookings").json()["data"][0]["status"] == "CANCELLED"


def test_cancelling_twice_is_rejected(client: TestClient, dev_user, room, login):
    login(EMPLOYEE_EMAIL)
    created = book(client, room, at(10), at(11)).json()["data"]
    client.delete(f"{PREFIX}/bookings/{created['id']}", headers=csrf(client))

    response = client.delete(f"{PREFIX}/bookings/{created['id']}", headers=csrf(client))

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "BOOKING_NOT_CANCELLABLE"


def test_availability_lists_the_days_bookings(client: TestClient, dev_user, room, login):
    login(EMPLOYEE_EMAIL)
    start, end = at(10), at(11)
    book(client, room, start, end)

    response = client.get(f"{PREFIX}/rooms/{room}/availability", params={"day": start[:10]})

    assert response.status_code == 200
    body = response.json()["data"]
    assert body["room_id"] == room
    assert body["date"] == start[:10]
    assert [b["status"] for b in body["bookings"]] == ["CONFIRMED"]


def test_availability_omits_cancelled_bookings(client: TestClient, dev_user, room, login):
    login(EMPLOYEE_EMAIL)
    created = book(client, room, at(10), at(11)).json()["data"]
    client.delete(f"{PREFIX}/bookings/{created['id']}", headers=csrf(client))

    response = client.get(
        f"{PREFIX}/rooms/{room}/availability", params={"day": created["start_time"][:10]}
    )

    assert response.json()["data"]["bookings"] == []
