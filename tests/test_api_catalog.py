"""Exercise real HTTP behavior of the published game-definition API."""

import pytest
import httpx

from server.api.index import app


@pytest.mark.asyncio
async def test_catalog_is_available_to_anonymous_http_clients():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/definitions")
        assert response.status_code == 200
        games = response.json()["definitions"]
        assert {game["id"] for game in games} >= {"chess", "draughts"}
        for game in games:
            assert game["board"]["rows"] > 0
            assert game["board"]["columns"] > 0
        result = await client.get("/api/definitions/chess")
        assert result.status_code == 200
        assert result.json()["name"] == "chess"


@pytest.mark.asyncio
async def test_catalog_rejects_unknown_ids_without_exposing_filesystem():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        for path in ["/api/definitions/nonexistent", "/api/definitions/.gitignore", "/api/definitions/chess.json"]:
            response = await client.get(path)
            assert response.status_code == 404
            assert "Unknown game definition" in response.text
