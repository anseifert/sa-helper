import os

from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app


def test_sync_returns_202_without_waiting():
    get_settings.cache_clear()
    os.environ["APP_USERNAME"] = "admin"
    os.environ["APP_PASSWORD"] = "test-secret"
    os.environ["SECRET_KEY"] = "test-session-secret-key-32bytes!!"
    get_settings.cache_clear()

    with TestClient(app) as client:
        client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "test-secret"},
        )
        r = client.post("/api/v1/sync")
        assert r.status_code == 202
        assert r.json()["status"] in ("started", "already_running")
