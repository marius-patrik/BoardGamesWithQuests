"""FastAPI bootstrap. No gameplay, definitions or persistence are implemented here.

The published catalog and full API are authored and tested in the integration PR.
Returning zero definitions is deliberate until there is real provider-backed state.
"""

from fastapi import FastAPI

app = FastAPI(title="BoardGamesWithQuests")


@app.get("/api/v1/definitions", response_model=list)
def list_definitions() -> list:
    """Empty bootstrap catalog; no fake shipped JSON or server filesystem paths."""
    return []
