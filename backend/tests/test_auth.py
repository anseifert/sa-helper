import os

from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app


def _client() -> TestClient:
    get_settings.cache_clear()
    os.environ["APP_USERNAME"] = "admin"
    os.environ["APP_PASSWORD"] = "test-secret"
    os.environ["SECRET_KEY"] = "test-session-secret-key-32bytes!!"
    get_settings.cache_clear()
    return TestClient(app)


def test_auth_login_protects_api():
    with _client() as client:
        assert client.get("/api/v1/health").status_code == 200

        assert client.get("/api/v1/dashboard").status_code == 401

        bad = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "wrong"},
        )
        assert bad.status_code == 401

        ok = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "test-secret"},
        )
        assert ok.status_code == 200
        assert ok.json()["authenticated"] is True

        assert client.get("/api/v1/dashboard").status_code == 200

        logout = client.post("/api/v1/auth/logout")
        assert logout.status_code == 200
        assert logout.json()["authenticated"] is False

        assert client.get("/api/v1/dashboard").status_code == 401
