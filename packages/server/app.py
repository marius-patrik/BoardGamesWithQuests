"""FastAPI application boundary; gameplay routes are not available yet."""

from fastapi import FastAPI

from engine.model.game.configuration import installed_definitions

app = FastAPI(
    title="BoardGamesWithQuests API",
    description="Game catalog, service health and authoritative multiplayer API.",
    version="0.0.0",
)


@app.get("/health", tags=["operational"])
def health() -> dict[str, str | bool]:
    """Report process availability without claiming gameplay readiness."""
    return {"status": "bootstrap", "playable": False}


@app.get("/games", tags=["catalog"])
def game_catalog() -> dict[str, list[dict[str, str | bool]]]:
    """List installed JSON definitions without granting or simulating gameplay."""
    return {
        "games": [
            {"id": game.name, "title": game.title, "playable": game.playable}
            for game in installed_definitions()
        ]
    }
