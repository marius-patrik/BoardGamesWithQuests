"""Verify the supported FastAPI HTTP bootstrap boundary."""

from fastapi.testclient import TestClient

from server.api.index import app


def test_live_http_health_contract():
    with TestClient(app) as client:
        response = client.get("/api/health", headers={"Accept": "application/json"})
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert response.json() == {
        "status": "ok",
        "service": "boardgameswithquests-api",
    }
