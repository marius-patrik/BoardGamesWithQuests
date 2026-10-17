"""FastAPI catalog and provider-verified identity boundary."""

from fastapi import Depends, FastAPI, HTTPException, Request, Response

import httpx

from server.auth import (
    AuthenticationRejected,
    AuthenticationUnavailable,
    SupabaseAuth,
    auth_transport,
    bearer_token,
)

from server.engine.model.game.configuration import installed_definitions

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


@app.get("/me", tags=["identity"])
async def current_identity(
    request: Request,
    response: Response,
    transport: httpx.AsyncBaseTransport | None = Depends(auth_transport),
) -> dict[str, str | bool]:
    """Return only the identity verified by Supabase Auth for this bearer request.

    Args:
        request: HTTP request containing the caller's Authorization header.
        response: HTTP response carrying the identity-cache isolation policy.
        transport: External HTTP boundary; the default performs real verified-TLS requests.

    Returns:
        Canonical provider identifier and strict registered/guest classification.

    Raises:
        HTTPException: 401 for rejected credentials; 503 when verification is unavailable.
    """
    privacy = {"Cache-Control": "no-store", "Vary": "Authorization"}
    response.headers.update(privacy)
    try:
        token = bearer_token(request.headers.getlist("authorization"))
        identity = await SupabaseAuth.from_environment(transport).authenticate(token)
        return identity.to_json()
    except AuthenticationRejected:
        raise HTTPException(
            401, "Authentication required", headers={**privacy, "WWW-Authenticate": "Bearer"}
        ) from None
    except AuthenticationUnavailable:
        raise HTTPException(503, "Authentication service unavailable", headers=privacy) from None
