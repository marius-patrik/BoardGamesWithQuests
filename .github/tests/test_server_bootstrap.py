"""Exercise the implemented server bootstrap over a real local HTTP connection."""

from contextlib import contextmanager
import json
import socket
from threading import Thread
from time import monotonic, sleep
from urllib.error import HTTPError
from urllib.request import urlopen

import pytest

pytest.importorskip("fastapi")
uvicorn = pytest.importorskip("uvicorn")
server = pytest.importorskip("server.api.index")
app = server.app


@contextmanager
def live_api():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    instance = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error"))
    thread = Thread(target=instance.run, daemon=True)
    thread.start()
    try:
        deadline = monotonic() + 10
        while not instance.started:
            if not thread.is_alive() or monotonic() > deadline:
                raise RuntimeError("ASGI bootstrap did not start")
            sleep(0.02)
        yield f"http://127.0.0.1:{port}"
    finally:
        instance.should_exit = True
        thread.join(timeout=10)
        assert not thread.is_alive(), "ASGI bootstrap did not stop"


def test_definition_catalog_returns_only_implemented_bootstrap_data():
    with live_api() as base:
        with urlopen(base + "/api/v1/definitions") as response:
            assert response.status == 200
            assert response.headers["content-type"].startswith("application/json")
            assert json.load(response) == []


def test_unimplemented_game_endpoints_are_not_advertised():
    with live_api() as base:
        for route in ("/api/v1/game", "/api/v1/game/secret"):
            with pytest.raises(HTTPError) as result:
                urlopen(base + route)
            assert result.value.code == 404
