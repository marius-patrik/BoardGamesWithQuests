"""Public configuration discovery for BoardGamesWithQuests.

This is a permanent, read-only HTTP contract. Gameplay writes are owned by
authenticated server actions and are not implemented through this catalog.
"""

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException

app = FastAPI(title="BoardGamesWithQuests")


def _catalog() -> dict[str, dict]:
    """Read the owned configuration set without accepting client filesystem paths."""
    root = Path(__file__).resolve().parents[3]
    candidates = (root / "config", Path(__file__).resolve().parents[1] / "config", Path.cwd() / "config")
    source = next((path for path in candidates if path.is_dir()), None)
    if source is None:
        raise RuntimeError("Published game definitions are unavailable")
    return {
        file.stem: json.loads(file.read_text(encoding="utf-8"))
        for file in sorted(source.glob("*.json"))
    }


@app.get("/api/definitions")
def definitions() -> dict:
    """Return public game metadata from shipped JSON (never state or secrets)."""
    return {
        "definitions": [
            {
                "id": name,
                "title": data["title"],
                "board": {
                    "rows": data["board"]["rows"],
                    "columns": data["board"]["columns"],
                },
            }
            for name, data in _catalog().items()
        ]
    }


@app.get("/api/definitions/{name}")
def definition(name: str) -> dict:
    """Return exactly one shipped declarative definition by identifier."""
    match = _catalog().get(name)
    if match is None:
        raise HTTPException(status_code=404, detail="Unknown game definition")
    return match
