"""RBAC (Phase 04): the same request, three roles, three different answers.

Every test below asks the same question — "can this role do this?" — so the role
matrix is visible in one file instead of scattered across endpoint tests.
"""

from fastapi.testclient import TestClient

PREFIX = "/api/v1"
ADMIN_EMAIL = "admin@test.officehub.dev"
SUPPORT_EMAIL = "support@test.officehub.dev"
EMPLOYEE_EMAIL = "tester@officehub.dev"
OTHER_EMAIL = "other@test.officehub.dev"


def test_anonymous_cannot_list_users(client: TestClient):
    assert client.get(f"{PREFIX}/users").status_code == 401


def test_admin_can_list_users(client: TestClient, admin_user, login):
    login(ADMIN_EMAIL)

    response = client.get(f"{PREFIX}/users")

    assert response.status_code == 200
    emails = [user["email"] for user in response.json()["data"]]
    assert ADMIN_EMAIL in emails


def test_employee_cannot_list_users(client: TestClient, dev_user, login):
    login(EMPLOYEE_EMAIL)

    response = client.get(f"{PREFIX}/users")

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_it_support_cannot_list_users(client: TestClient, it_support_user, login):
    login(SUPPORT_EMAIL)

    assert client.get(f"{PREFIX}/users").status_code == 403


def test_employee_can_read_their_own_account(client: TestClient, dev_user, login):
    login(EMPLOYEE_EMAIL)

    response = client.get(f"{PREFIX}/users/{dev_user}")

    assert response.status_code == 200
    assert response.json()["data"]["email"] == EMPLOYEE_EMAIL


def test_employee_cannot_read_another_account(client: TestClient, dev_user, other_user, login):
    login(EMPLOYEE_EMAIL)

    response = client.get(f"{PREFIX}/users/{other_user}")

    assert response.status_code == 403


def test_admin_can_read_another_account(client: TestClient, admin_user, other_user, login):
    login(ADMIN_EMAIL)

    response = client.get(f"{PREFIX}/users/{other_user}")

    assert response.status_code == 200
    assert response.json()["data"]["email"] == OTHER_EMAIL


def test_admin_getting_an_unknown_user_returns_404(client: TestClient, admin_user, login):
    login(ADMIN_EMAIL)

    response = client.get(f"{PREFIX}/users/does-not-exist")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_forbidden_response_carries_the_request_id(client: TestClient, dev_user, login):
    login(EMPLOYEE_EMAIL)

    response = client.get(f"{PREFIX}/users")

    assert response.json()["error"]["request_id"] == response.headers["X-Request-ID"]
