"""Room management (Phase 05): who may see rooms, and who may change them."""

from fastapi.testclient import TestClient

PREFIX = "/api/v1"
ADMIN_EMAIL = "admin@test.officehub.dev"
SUPPORT_EMAIL = "support@test.officehub.dev"
EMPLOYEE_EMAIL = "tester@officehub.dev"

ROOM = {"name": "Aurora", "description": "Town hall", "location": "3rd floor", "capacity": 40}


def csrf(client: TestClient) -> dict[str, str]:
    return {"X-CSRF-Token": client.cookies.get("csrf_token", "")}


def create_room(client: TestClient, **overrides) -> dict:
    response = client.post(f"{PREFIX}/rooms", json={**ROOM, **overrides}, headers=csrf(client))
    assert response.status_code == 201, response.text
    return response.json()["data"]


def test_anonymous_cannot_list_rooms(client: TestClient):
    assert client.get(f"{PREFIX}/rooms").status_code == 401


def test_it_support_cannot_list_rooms(client: TestClient, it_support_user, login):
    # IT_SUPPORT has no room permissions at all in V1
    login(SUPPORT_EMAIL)
    assert client.get(f"{PREFIX}/rooms").status_code == 403


def test_employee_can_list_rooms(client: TestClient, dev_user, login):
    login(EMPLOYEE_EMAIL)
    assert client.get(f"{PREFIX}/rooms").status_code == 200


def test_employee_cannot_create_a_room(client: TestClient, dev_user, login):
    login(EMPLOYEE_EMAIL)
    response = client.post(f"{PREFIX}/rooms", json=ROOM, headers=csrf(client))
    assert response.status_code == 403


def test_admin_creates_a_room(client: TestClient, admin_user, login):
    login(ADMIN_EMAIL)

    room = create_room(client)

    assert room["name"] == "Aurora"
    assert room["capacity"] == 40
    assert room["status"] == "ACTIVE"


def test_room_requires_a_capacity_of_at_least_one(client: TestClient, admin_user, login):
    login(ADMIN_EMAIL)

    response = client.post(f"{PREFIX}/rooms", json={**ROOM, "capacity": 0}, headers=csrf(client))

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_room_requires_a_name(client: TestClient, admin_user, login):
    login(ADMIN_EMAIL)

    response = client.post(f"{PREFIX}/rooms", json={**ROOM, "name": ""}, headers=csrf(client))

    assert response.status_code == 422


def test_unknown_room_returns_404(client: TestClient, admin_user, login):
    login(ADMIN_EMAIL)

    response = client.get(f"{PREFIX}/rooms/does-not-exist")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_admin_can_read_a_room(client: TestClient, admin_user, login):
    login(ADMIN_EMAIL)
    room = create_room(client)

    response = client.get(f"{PREFIX}/rooms/{room['id']}")

    assert response.status_code == 200
    assert response.json()["data"]["name"] == "Aurora"


def test_admin_can_patch_a_room(client: TestClient, admin_user, login):
    login(ADMIN_EMAIL)
    room = create_room(client)

    response = client.patch(
        f"{PREFIX}/rooms/{room['id']}", json={"capacity": 12}, headers=csrf(client)
    )

    assert response.status_code == 200
    body = response.json()["data"]
    assert body["capacity"] == 12
    # untouched fields survive a PATCH
    assert body["name"] == "Aurora"
    assert body["location"] == "3rd floor"


def test_patch_with_no_fields_is_rejected(client: TestClient, admin_user, login):
    login(ADMIN_EMAIL)
    room = create_room(client)

    response = client.patch(f"{PREFIX}/rooms/{room['id']}", json={}, headers=csrf(client))

    assert response.status_code == 422


def test_admin_can_disable_a_room(client: TestClient, admin_user, login):
    login(ADMIN_EMAIL)
    room = create_room(client)

    response = client.patch(
        f"{PREFIX}/rooms/{room['id']}", json={"status": "INACTIVE"}, headers=csrf(client)
    )

    assert response.json()["data"]["status"] == "INACTIVE"


def test_employee_does_not_see_disabled_rooms(client: TestClient, admin_user, dev_user, login):
    login(ADMIN_EMAIL)
    create_room(client, name="Retired room")
    target = next(r for r in client.get(f"{PREFIX}/rooms").json()["data"] if r["name"] == "Retired room")
    client.patch(f"{PREFIX}/rooms/{target['id']}", json={"status": "INACTIVE"}, headers=csrf(client))

    login(EMPLOYEE_EMAIL)

    names = [room["name"] for room in client.get(f"{PREFIX}/rooms").json()["data"]]
    assert "Retired room" not in names


def test_admin_still_sees_disabled_rooms(client: TestClient, admin_user, login):
    login(ADMIN_EMAIL)
    room = create_room(client)
    client.patch(f"{PREFIX}/rooms/{room['id']}", json={"status": "INACTIVE"}, headers=csrf(client))

    statuses = {r["id"]: r["status"] for r in client.get(f"{PREFIX}/rooms").json()["data"]}

    assert statuses[room["id"]] == "INACTIVE"


def test_employee_cannot_delete_a_room(client: TestClient, admin_user, dev_user, login):
    login(ADMIN_EMAIL)
    room = create_room(client)

    login(EMPLOYEE_EMAIL)
    response = client.delete(f"{PREFIX}/rooms/{room['id']}", headers=csrf(client))

    assert response.status_code == 403


def test_admin_can_delete_a_room(client: TestClient, admin_user, login):
    login(ADMIN_EMAIL)
    room = create_room(client)

    response = client.delete(f"{PREFIX}/rooms/{room['id']}", headers=csrf(client))

    assert response.status_code == 204
    assert client.get(f"{PREFIX}/rooms/{room['id']}").status_code == 404
