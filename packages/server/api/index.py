"""ASGI bootstrap for the independent Vercel API project.

This entrypoint intentionally exposes no gameplay, account, or persistence
capabilities until their authenticated contracts are implemented.
"""

from fastapi import FastAPI

app = FastAPI(
    title="BoardGamesWithQuests",
    description="API bootstrap. Game endpoints are not implemented.",
    version="0.1.0",
)


@app.get("/api/health")
def health() -> dict[str, str]:
    """Report the running API process, not game readiness."""
    return {"status": "ok", "service": "boardgameswithquests-api"}
