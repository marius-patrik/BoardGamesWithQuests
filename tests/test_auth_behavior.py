"""FR-80: authenticate actual HTTP callers through the genuine Supabase adapter."""

from collections.abc import Iterator
import json

from fastapi.testclient import TestClient
import httpx
import pytest

from server.app import app
from server.auth import MAX_RESPONSE_BYTES, MAX_TOKEN_BYTES, auth_transport

URL = "https://wdthdcdoqdtywngwvddk.supabase.co"
KEY = "sb_publishable_boundary_test"
IDENTITY = "9ce68826-13a5-4970-a2d3-0d516e984beb"


@pytest.fixture(autouse=True)
def configured_boundary(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Isolate application configuration and restore only the external transport."""
    monkeypatch.setenv("SUPABASE_URL", URL)
    monkeypatch.setenv("SUPABASE_PUBLISHABLE_KEY", KEY)
    yield
    app.dependency_overrides.pop(auth_transport, None)


def client_with_provider(handler) -> TestClient:
    """Replace the nondeterministic network, preserving all authentication code."""

    async def external_provider(request):
        response = handler(request)
        if response.is_stream_consumed:
            return httpx.Response(
                response.status_code,
                headers=response.headers,
                stream=httpx.ByteStream(response.content),
            )
        return response

    transport = httpx.MockTransport(external_provider)
    app.dependency_overrides[auth_transport] = lambda: transport
    return TestClient(app)


def provider_request(request: httpx.Request, *, guest: bool = False) -> httpx.Response:
    """Return the real provider-owned user shape after observing an HTTP request."""
    assert request.method == "GET"
    assert str(request.url) == URL + "/auth/v1/user"
    assert request.headers["apikey"] == KEY
    assert request.headers["authorization"].startswith("Bearer ")
    assert request.headers["Accept-Encoding"] == "identity"
    assert request.extensions["timeout"] == {"connect": 5.0, "read": 5.0, "write": 5.0, "pool": 5.0}
    return httpx.Response(
        200,
        json={
            "id": IDENTITY,
            "is_anonymous": guest,
            "email": "private@example.invalid",
            "user_metadata": {"id": "spoof", "is_anonymous": not guest, "role": "admin"},
            "app_metadata": {"provider": "anonymous" if guest else "email"},
        },
    )


@pytest.mark.parametrize("guest", [False, True])
def test_registered_and_guest_http_callers_receive_only_verified_identity(guest: bool) -> None:
    """FR-80: provider verification governs identity equally for both account kinds."""
    client = client_with_provider(lambda request: provider_request(request, guest=guest))
    response = client.get(
        "/me?id=spoof&is_guest=false", headers={"Authorization": "Bearer opaque-token"}
    )
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["Vary"] == "Authorization"
    assert response.json() == {"id": IDENTITY, "is_guest": guest}
    assert "private@example.invalid" not in response.text and "metadata" not in response.text
    assert client.post("/games", json={"user_id": IDENTITY}).status_code in (404, 405)


@pytest.mark.parametrize(
    "authorization",
    [
        None,
        "",
        "Basic secret",
        "Bearer",
        "Bearer ",
        "Bearer  token",
        "Bearer token ",
        "Bearer token\n",
        "Bearer token\t",
        "Bearer " + "t" * (MAX_TOKEN_BYTES + 1),
    ],
)
def test_malformed_http_authorization_rejects_before_any_provider_request(
    authorization: str | None,
) -> None:
    """FR-80: invalid headers cannot trigger identity verification or leak input."""
    requests = []
    client = client_with_provider(
        lambda request: requests.append(request) or provider_request(request)
    )
    response = client.get(
        "/me", headers={} if authorization is None else {"Authorization": authorization}
    )
    assert response.status_code == 401
    assert response.headers["Cache-Control"] == "no-store"
    assert response.json() == {"detail": "Authentication required"}
    assert response.headers["WWW-Authenticate"] == "Bearer"
    assert requests == []


def test_duplicate_authorization_headers_are_not_silently_selected() -> None:
    """FR-80: request smuggling cannot choose between two caller identities."""
    calls = []
    client = client_with_provider(
        lambda request: calls.append(request) or provider_request(request)
    )
    response = client.get(
        "/me", headers=[("Authorization", "Bearer first"), ("Authorization", "Bearer second")]
    )
    assert response.status_code == 401 and calls == []


def test_token_at_size_boundary_is_verified_as_opaque_data() -> None:
    """FR-80: the declared maximum is inclusive and never decoded as client claims."""
    token = "t" * MAX_TOKEN_BYTES

    def handler(request):
        assert request.headers["Authorization"] == "Bearer " + token
        return provider_request(request)

    assert client_with_provider(handler).get(
        "/me", headers={"Authorization": "Bearer " + token}
    ).json() == {"id": IDENTITY, "is_guest": False}


@pytest.mark.parametrize("status", [401, 403])
def test_provider_denial_has_a_generic_401_challenge(status: int) -> None:
    """FR-80: rejected provider credentials never expose response bodies or tokens."""
    client = client_with_provider(
        lambda request: httpx.Response(status, text="private provider rejection opaque-secret")
    )
    response = client.get("/me", headers={"Authorization": "Bearer opaque-secret"})
    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"
    assert response.json() == {"detail": "Authentication required"}
    assert "opaque-secret" not in response.text and "provider rejection" not in response.text


@pytest.mark.parametrize("status", [302, 429, 500, 503])
def test_transient_errors_and_redirects_fail_closed_without_following(status: int) -> None:
    """FR-80: verification cannot redirect credentials or infer identity from errors."""
    calls = []

    def handler(request):
        calls.append(str(request.url))
        return httpx.Response(
            status, headers={"Location": "https://attacker.invalid/user"}, text="opaque-secret"
        )

    response = client_with_provider(handler).get(
        "/me", headers={"Authorization": "Bearer opaque-secret"}
    )
    assert response.status_code == 503
    assert response.json() == {"detail": "Authentication service unavailable"}
    assert calls == [URL + "/auth/v1/user"]
    assert "opaque-secret" not in response.text and "attacker" not in response.text


@pytest.mark.parametrize(
    "error", [httpx.ConnectError, httpx.ReadTimeout, httpx.RemoteProtocolError]
)
def test_network_failures_never_authorize_or_disclose_provider_diagnostics(error) -> None:
    """FR-80: provider outages return a safe retryable service response."""

    def handler(request):
        raise error("provider failed with opaque-secret", request=request)

    response = client_with_provider(handler).get(
        "/me", headers={"Authorization": "Bearer opaque-secret"}
    )
    assert response.status_code == 503
    assert response.json() == {"detail": "Authentication service unavailable"}


@pytest.mark.parametrize(
    "payload",
    [
        None,
        [],
        {},
        {"id": IDENTITY},
        {"id": IDENTITY, "is_anonymous": 1},
        {"id": IDENTITY, "is_anonymous": "false"},
        {"id": "not-a-uuid", "is_anonymous": False},
        {"id": IDENTITY.upper(), "is_anonymous": False},
        {"id": IDENTITY.replace("-", ""), "is_anonymous": False},
        {"user_metadata": {"id": IDENTITY, "is_anonymous": False}},
    ],
)
def test_malformed_provider_identity_cannot_fall_back_to_metadata(payload) -> None:
    """FR-80: only canonical provider UUID and strict anonymous boolean are trusted."""
    response = client_with_provider(lambda request: httpx.Response(200, json=payload)).get(
        "/me", headers={"Authorization": "Bearer opaque-secret"}
    )
    assert response.status_code == 503
    assert response.json() == {"detail": "Authentication service unavailable"}


@pytest.mark.parametrize(
    "body",
    [
        b"not json",
        b"\xff",
        ('{"id":"' + IDENTITY + '","id":"spoof","is_anonymous":false}').encode(),
        b"[" * 1500 + b"0" + b"]" * 1500,
        b"x" * (MAX_RESPONSE_BYTES + 1),
    ],
)
def test_invalid_or_oversized_provider_documents_fail_closed(body: bytes) -> None:
    """FR-80: duplicate fields, decoder failures and size attacks cannot authorize."""
    response = client_with_provider(
        lambda request: httpx.Response(
            200, content=body, headers={"Content-Type": "application/json"}
        )
    ).get("/me", headers={"Authorization": "Bearer opaque-secret"})
    assert response.status_code == 503
    assert response.json() == {"detail": "Authentication service unavailable"}


def test_response_size_boundary_is_inclusive() -> None:
    """FR-80: valid bounded JSON at the exact provider byte cap is accepted."""
    prefix = json.dumps({"id": IDENTITY, "is_anonymous": False}).encode()
    body = prefix + b" " * (MAX_RESPONSE_BYTES - len(prefix))
    response = client_with_provider(
        lambda request: httpx.Response(
            200, content=body, headers={"Content-Type": "application/json"}
        )
    ).get("/me", headers={"Authorization": "Bearer opaque-token"})
    assert response.status_code == 200 and response.json() == {"id": IDENTITY, "is_guest": False}


@pytest.mark.parametrize(
    "url,key",
    [
        ("", KEY),
        (URL, ""),
        ("http://wdthdcdoqdtywngwvddk.supabase.co", KEY),
        ("https://attacker.invalid", KEY),
        (URL + "/other", KEY),
        (URL + "?token=secret", KEY),
        (URL, "sb_secret_forbidden"),
        (URL, "legacy-jwt"),
        (URL, KEY + "\n"),
    ],
)
def test_missing_or_unsafe_configuration_does_not_transmit_caller_credentials(
    monkeypatch, url: str, key: str
) -> None:
    """FR-80: malformed server configuration blocks transmission and identity."""
    monkeypatch.setenv("SUPABASE_URL", url)
    monkeypatch.setenv("SUPABASE_PUBLISHABLE_KEY", key)
    calls = []
    response = client_with_provider(
        lambda request: calls.append(request) or provider_request(request)
    ).get("/me", headers={"Authorization": "Bearer opaque-secret"})
    assert response.status_code == 503 and calls == []
    assert response.json() == {"detail": "Authentication service unavailable"}


def test_repeated_verified_requests_remain_isolated_from_spoofed_client_inputs() -> None:
    """FR-80: repeated auth reads neither cache another user nor trust request bodies."""

    def handler(request):
        return provider_request(request, guest=request.headers["Authorization"] == "Bearer guest")

    client = client_with_provider(handler)
    for token, guest in [("guest", True), ("registered", False), ("guest", True)]:
        response = client.request(
            "GET",
            "/me?user_id=attacker",
            headers={"Authorization": "Bearer " + token},
            json={"id": "attacker", "is_guest": not guest},
        )
        assert response.status_code == 200 and response.json() == {
            "id": IDENTITY,
            "is_guest": guest,
        }


def test_nonfinite_json_extensions_in_private_fields_block_identity() -> None:
    """FR-80: invalid JSON cannot hide in provider fields excluded from output."""
    body = ('{"id":"' + IDENTITY + '","is_anonymous":false,"metadata":{"number":NaN}}').encode()
    response = client_with_provider(
        lambda request: httpx.Response(
            200, content=body, headers={"Content-Type": "application/json"}
        )
    ).get("/me", headers={"Authorization": "Bearer opaque-token"})
    assert response.status_code == 503


def test_genuine_provider_gate_reports_missing_credentials_as_blocked(monkeypatch) -> None:
    """FR-80: external success cannot be reported from missing provider inputs."""
    import os
    from pathlib import Path
    import subprocess
    import sys

    environment = dict(os.environ)
    for name in (
        "SUPABASE_URL",
        "SUPABASE_PUBLISHABLE_KEY",
        "BGWQ_REGISTERED_ACCESS_TOKEN",
        "BGWQ_REGISTERED_USER_ID",
        "BGWQ_GUEST_ACCESS_TOKEN",
        "BGWQ_GUEST_USER_ID",
    ):
        environment.pop(name, None)
    environment["PYTHONPATH"] = str(Path(__file__).parents[1] / "packages")
    result = subprocess.run(
        [sys.executable, "-m", "server.auth", "--verify-provider"],
        env=environment,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    assert "verification blocked" in result.stderr
    assert "BGWQ_REGISTERED_ACCESS_TOKEN" in result.stderr
    assert "passed" not in result.stdout


@pytest.mark.parametrize("scheme", ["bearer", "bEaReR", "BEARER"])
def test_authentication_scheme_is_case_insensitive_with_one_ascii_separator(scheme: str) -> None:
    """FR-80: HTTP scheme casing cannot distinguish otherwise valid callers."""
    response = client_with_provider(provider_request).get(
        "/me", headers={"Authorization": scheme + " opaque-token"}
    )
    assert response.status_code == 200 and response.json() == {"id": IDENTITY, "is_guest": False}


@pytest.mark.parametrize("encoding", ["gzip", "br", "deflate", "gzip, identity"])
def test_compressed_provider_stream_is_rejected_before_reading_body(encoding: str) -> None:
    """FR-80: response decompression cannot amplify work beyond the raw body cap."""

    class HostileStream(httpx.AsyncByteStream):
        consumed = False

        async def __aiter__(self):
            self.consumed = True
            raise AssertionError("compressed provider body must not be read")
            yield b"unreachable"

    stream = HostileStream()
    response = client_with_provider(
        lambda request: httpx.Response(
            200,
            stream=stream,
            headers={"Content-Type": "application/json", "Content-Encoding": encoding},
        )
    ).get("/me", headers={"Authorization": "Bearer opaque-token"})
    assert response.status_code == 503
    assert response.json() == {"detail": "Authentication service unavailable"}
    assert stream.consumed is False


@pytest.mark.parametrize("slow", [True, False])
def test_total_deadline_bounds_slow_drip_and_closes_provider_stream(monkeypatch, slow):
    """FR-80: total network duration is bounded despite individually timely bytes."""
    import asyncio
    import time
    import server.auth as auth

    monkeypatch.setattr(auth, "AUTH_TIMEOUT_SECONDS", 0.08)

    class ProviderStream(httpx.AsyncByteStream):
        closed = False
        cancelled = False

        async def __aiter__(self):
            body = json.dumps({"id": IDENTITY, "is_anonymous": False}).encode()
            try:
                if slow:
                    for byte in body:
                        await asyncio.sleep(0.015)
                        yield bytes([byte])
                else:
                    yield body[:5]
                    yield body[5:]
            except asyncio.CancelledError:
                self.cancelled = True
                raise

        async def aclose(self):
            self.closed = True

    stream = ProviderStream()
    client = client_with_provider(
        lambda request: httpx.Response(
            200, headers={"Content-Type": "application/json"}, stream=stream
        )
    )
    started = time.monotonic()
    response = client.get("/me", headers={"Authorization": "Bearer private-token"})
    assert time.monotonic() - started < 1.0
    assert stream.closed
    if slow:
        assert stream.cancelled
        assert response.status_code == 503
        assert response.json() == {"detail": "Authentication service unavailable"}
        assert "private-token" not in response.text and IDENTITY not in response.text
    else:
        assert not stream.cancelled
        assert response.status_code == 200
        assert response.json() == {"id": IDENTITY, "is_guest": False}
