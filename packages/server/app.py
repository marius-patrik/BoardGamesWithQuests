"""FastAPI application boundary; gameplay routes are not available yet."""

from fastapi import FastAPI

app = FastAPI(
    title="BoardGamesWithQuests API",
    description="Authoritative multiplayer API; currently bootstrapped only.",
    version="0.0.0",
)


@app.get("/health", tags=["operational"])
def health() -> dict[str, str | bool]:
    """Report process availability without claiming gameplay readiness."""
    return {"status": "bootstrap", "playable": False}
