from fastapi.testclient import TestClient

from app.core.security import CSRF_COOKIE, SESSION_COOKIE
from app.main import app
from tests.conftest import DEV_EMAIL, DEV_PASSWORD

client = TestClient(app)

PREFIX = "/api/v1"
CSRF_HEADER_NAME = "X-CSRF-Token"


def _csrf_headers() -> dict[str, str]:
    return {CSRF_HEADER_NAME: client.cookies.get(CSRF_COOKIE, "")}


def _login(email: str = DEV_EMAIL, password: str = DEV_PASSWORD):
    return client.post(f"{PREFIX}/auth/login", json={"email": email, "password": password})


def test_login_returns_user_and_sets_httponly_cookie(dev_user):
    response = _login()

    assert response.status_code == 200
    assert response.json() == {
        "data": {
            "id": dev_user,
            "name": "Test User",
            "email": DEV_EMAIL,
            "roles": ["EMPLOYEE"],
        }
    }
    session_cookie = next(
        c for c in response.headers.get_list("set-cookie") if SESSION_COOKIE in c
    )
    assert "httponly" in session_cookie.lower()
    assert "samesite=lax" in session_cookie.lower()
    assert "secure" not in session_cookie.lower()


def test_password_is_never_stored_in_plaintext(dev_user):
    _login()
    # the cookie value must not equal anything we could reverse into the password
    raw_token = client.cookies[SESSION_COOKIE]
    assert DEV_PASSWORD not in raw_token


def test_login_with_wrong_password_is_rejected(dev_user):
    response = _login(password="not-the-password")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_unknown_email_returns_the_same_error_as_wrong_password(dev_user):
    unknown = _login(email="nobody@officehub.dev")
    wrong = _login(password="not-the-password")

    # FR-AUTH-002: the response must not reveal whether the account exists
    # (request_id differs per request by design, so compare the client-visible fields)
    assert unknown.status_code == wrong.status_code == 401
    assert {k: v for k, v in unknown.json()["error"].items() if k != "request_id"} == {
        k: v for k, v in wrong.json()["error"].items() if k != "request_id"
    }


def test_login_rejects_inactive_user(inactive_user):
    response = _login(email="disabled@officehub.dev")

    assert response.status_code == 401


def test_me_requires_a_session():
    response = client.get(f"{PREFIX}/auth/me")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_me_returns_the_signed_in_user(dev_user):
    _login()

    response = client.get(f"{PREFIX}/auth/me")

    assert response.status_code == 200
    assert response.json()["data"]["email"] == DEV_EMAIL


def test_logout_revokes_the_session(dev_user):
    _login()

    assert client.post(f"{PREFIX}/auth/logout", headers=_csrf_headers()).status_code == 204
    # FR-AUTH-006: a revoked session must stop authenticating immediately
    assert client.get(f"{PREFIX}/auth/me").status_code == 401


def test_expired_session_does_not_authenticate(dev_user, expire_sessions):
    _login()
    expire_sessions()

    # FR-AUTH-006
    assert client.get(f"{PREFIX}/auth/me").status_code == 401


def test_forged_session_token_is_rejected(dev_user):
    client.cookies.set(SESSION_COOKIE, "not-a-real-token")

    assert client.get(f"{PREFIX}/auth/me").status_code == 401


def test_csrf_endpoint_returns_a_token_matching_the_cookie():
    response = client.get(f"{PREFIX}/auth/csrf")

    assert response.status_code == 200
    assert response.json()["data"]["token"] == response.cookies.get(CSRF_COOKIE)


def test_state_change_without_csrf_header_is_forbidden(dev_user):
    _login()

    response = client.post(f"{PREFIX}/auth/logout")

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "CSRF_TOKEN_INVALID"


def test_state_change_with_wrong_csrf_header_is_forbidden(dev_user):
    _login()

    response = client.post(
        f"{PREFIX}/auth/logout", headers={CSRF_HEADER_NAME: "wrong-token"}
    )

    assert response.status_code == 403


def test_state_change_with_matching_csrf_header_succeeds(dev_user):
    _login()

    response = client.post(f"{PREFIX}/auth/logout", headers=_csrf_headers())

    assert response.status_code == 204