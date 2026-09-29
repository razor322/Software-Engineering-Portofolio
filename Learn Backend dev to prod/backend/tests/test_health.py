from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

PREFIX = "/api/v1"


def test_live_returns_ok():
    response = client.get(f"{PREFIX}/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_reports_database():
    response = client.get(f"{PREFIX}/health/ready")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "dependencies": {"database": "ok"},
    }


def test_unknown_path_uses_error_envelope():
    response = client.get(f"{PREFIX}/does-not-exist")
    assert response.status_code == 404
    body = response.json()["error"]
    assert body["code"] == "NOT_FOUND"
    assert body["request_id"] == response.headers["X-Request-ID"]


def test_client_supplied_request_id_is_propagated():
    response = client.get(f"{PREFIX}/health/live", headers={"X-Request-ID": "req_test_123"})
    assert response.headers["X-Request-ID"] == "req_test_123"


def test_root_reports_running():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "running"}


def test_openapi_schema_is_served():
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert response.json()["info"]["title"]
