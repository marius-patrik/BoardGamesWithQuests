"""Verify the actual FastAPI bootstrap over HTTP, including absent service routes."""

from contextlib import contextmanager
import json
import socket
from threading import Thread
from time import monotonic, sleep
from urllib.error import HTTPError
from urllib.request import urlopen

import uvicorn

from server.api.index import app


@contextmanager
def live_api():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error"))
    worker = Thread(target=server.run, daemon=True)
    worker.start()
    try:
        deadline = monotonic() + 10
        while not server.started:
            if not worker.is_alive() or monotonic() > deadline:
                raise RuntimeError("FastAPI HTTP server failed to start")
            sleep(0.02)
        yield f"http://127.0.0.1:{port}"
    finally:
        server.should_exit = True
        worker.join(timeout=10)
        assert not worker.is_alive(), "FastAPI HTTP server failed to stop"


def test_catalog_bootstrap_returns_empty_array_over_real_http():
    with live_api() as url:
        with urlopen(url + "/api/v1/definitions") as response:
            assert response.status == 200
            assert response.headers["content-type"].startswith("application/json")
            assert json.load(response) == []


def test_no_private_files_or_future_game_routes_exposed():
    with live_api() as url:
        for path in (
            "/api/v1/definitions/chess",
            "/api/v1/definitions/..%2F.gitignore",
            "/api/v1/definitions/unknown.json",
            "/api/v1/game",
            "/api/v1/game/secret",
        ):
            try:
                urlopen(url + path)
            except HTTPError as error:
                assert error.code in {400, 404}, (path, error.code)
            else:
                raise AssertionError(f"Undelivered or private route unexpectedly available: {path}")
