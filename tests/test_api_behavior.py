"""Assert the ASGI service's externally observable HTTP behavior."""

from fastapi.testclient import TestClient

from server.app import app

client = TestClient(app)


def test_catalog_returns_real_nonplayable_configurations() -> None:
    response = client.get("/games")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    games = response.json()["games"]
    assert {g["id"] for g in games} == {"chess", "english_draughts", "international_checkers"}
    assert all(g["title"] and g["playable"] is False for g in games)


def test_health_cannot_misrepresent_gameplay_readiness() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "bootstrap", "playable": False}


def test_anonymous_client_cannot_submit_unimplemented_gameplay() -> None:
    assert client.post("/games", json={"game": "chess"}).status_code in (404, 405)
    assert client.post("/games/random/moves", json={"source": [1, 1]}).status_code == 404
    assert client.get("/games/random/state").status_code == 404
