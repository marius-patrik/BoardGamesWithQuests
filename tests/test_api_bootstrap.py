"""HTTP ASGI boundary behavior tests for the server bootstrap."""

import asyncio
import json

from server.api.index import app


async def request(path: str):
    """Dispatch an ASGI HTTP request and collect actual status/body messages."""
    sent = []
    received = False

    async def receive():
        nonlocal received
        if not received:
            received = True
            return {"type": "http.request", "body": b"", "more_body": False}
        await asyncio.sleep(0)
        return {"type": "http.disconnect"}

    async def send(message):
        sent.append(message)

    await app(
        {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": "GET",
            "scheme": "http",
            "path": path,
            "raw_path": path.encode("ascii"),
            "query_string": b"",
            "headers": [(b"accept", b"application/json")],
            "client": ("127.0.0.1", 12345),
            "server": ("127.0.0.1", 8000),
        },
        receive,
        send,
    )
    status = next(m["status"] for m in sent if m["type"] == "http.response.start")
    body = b"".join(m.get("body", b"") for m in sent if m["type"] == "http.response.body")
    return status, json.loads(body)


def test_health_exposes_running_service_but_not_gameplay():
    assert asyncio.run(request("/api/health")) == (
        200,
        {"status": "ok", "service": "boardgameswithquests-api"},
    )


def test_unimplemented_gameplay_fails_closed():
    status, body = asyncio.run(request("/api/games"))
    assert status == 404
    assert body == {"detail": "Not Found"}
