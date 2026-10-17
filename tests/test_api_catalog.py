"""Observe catalog endpoints over real HTTP rather than inspecting internal code."""

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
    """Serve real HTTP requests over an isolated local port."""
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error"))
    worker = Thread(target=server.run, daemon=True)
    worker.start()
    deadline = monotonic() + 10
    try:
        while not server.started:
            if not worker.is_alive() or monotonic() > deadline:
                raise RuntimeError("HTTP server failed to start")
            sleep(0.02)
        yield f"http://127.0.0.1:{port}"
    finally:
        server.should_exit = True
        worker.join(timeout=10)
        assert not worker.is_alive(), "HTTP server failed to stop"


def test_catalog_is_available_to_anonymous_http_clients():
    with live_api() as url:
        with urlopen(url + "/api/definitions") as response:
            assert response.status == 200
            games = json.load(response)["definitions"]
        assert {game["id"] for game in games} >= {"chess", "draughts", "international-draughts"}
        for game in games:
            assert game["board"]["rows"] > 0
            assert game["board"]["columns"] > 0
        with urlopen(url + "/api/definitions/chess") as response:
            assert response.status == 200
            assert json.load(response)["name"] == "chess"


def test_unknown_definitions_are_rejected_without_exposing_paths():
    with live_api() as url:
        for path in ["nonexistent", ".gitignore", "chess.json", "..%2F.gitignore"]:
            try:
                urlopen(url + "/api/definitions/" + path)
            except HTTPError as error:
                assert error.code in {400, 404}
            else:
                raise AssertionError(f"Unexpectedly accepted a private path: {path}")
