"""Bounded Supabase Auth verification with no locally trusted JWT claims.

The provider owns user identity and anonymous-account status. This boundary maps
only those verified fields into application identity; user metadata, email and
unchecked token contents never authorize a caller.
"""

from __future__ import annotations

import asyncio
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
import json
import os
import re
import sys
from typing import Any
from urllib.parse import urlsplit
from uuid import UUID

import httpx

MAX_TOKEN_BYTES = 16384
MAX_RESPONSE_BYTES = 65536
AUTH_TIMEOUT_SECONDS = 5.0


class AuthenticationRejected(ValueError):
    """The caller did not supply a bearer identity accepted by Supabase Auth."""


class AuthenticationUnavailable(RuntimeError):
    """Configured provider verification cannot establish a trustworthy identity."""


@dataclass(frozen=True)
class VerifiedIdentity:
    """Minimal identity verified through the configured provider.

    Args:
        id: Canonical Supabase Auth UUID.
        is_guest: Provider-verified anonymous-account flag.
    """

    id: str
    is_guest: bool

    def to_json(self) -> dict[str, str | bool]:
        """Return detached public identity fields without private provider data.

        Returns:
            Exactly the verified identifier and guest flag.
        """
        return {"id": self.id, "is_guest": self.is_guest}


def bearer_token(headers: Sequence[str]) -> str:
    """Require one bounded, unambiguous Bearer authorization value.

    Args:
        headers: All Authorization header values supplied by the HTTP caller.

    Returns:
        Opaque visible-ASCII token; its unverified claims are never inspected.

    Raises:
        AuthenticationRejected: Header count, scheme, whitespace or size is invalid.
    """
    if len(headers) != 1:
        raise AuthenticationRejected("Authentication required")
    scheme, separator, token = headers[0].partition(" ")
    if not separator or scheme.lower() != "bearer":
        raise AuthenticationRejected("Authentication required")
    if not 1 <= len(token) <= MAX_TOKEN_BYTES or any(not 33 <= ord(char) <= 126 for char in token):
        raise AuthenticationRejected("Authentication required")
    return token


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Reject ambiguous duplicate provider fields before identity normalization.

    Args:
        pairs: JSON parser object entries.

    Returns:
        Unambiguous decoded object.

    Raises:
        ValueError: A JSON object has duplicate keys.
    """
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("ambiguous provider JSON")
        result[key] = value
    return result


@dataclass(frozen=True)
class SupabaseAuth:
    """Verify access tokens only against the application's configured Auth project.

    Args:
        url: Approved project HTTPS origin.
        publishable_key: Modern application key; never a privileged credential.
        transport: Optional external HTTP transport for deterministic boundary tests.

    Raises:
        AuthenticationUnavailable: Project origin or application key is invalid.
    """

    url: str
    publishable_key: str = field(repr=False)
    transport: httpx.AsyncBaseTransport | None = field(default=None, repr=False, compare=False)

    def __post_init__(self) -> None:
        """Reject unsafe configuration before attaching any caller credentials.

        Raises:
            AuthenticationUnavailable: Configuration does not name the approved origin/key.
        """
        try:
            parsed = urlsplit(self.url)
            project_ref = parsed.netloc.removesuffix(".supabase.co")
            valid_url = (
                parsed.scheme == "https"
                and parsed.netloc.endswith(".supabase.co")
                and re.fullmatch(r"[a-z0-9]{20}", project_ref) is not None
                and parsed.path in ("", "/")
                and not parsed.query
                and not parsed.fragment
                and all(33 <= ord(char) <= 126 for char in self.url)
            )
            valid_key = (
                isinstance(self.publishable_key, str)
                and self.publishable_key.startswith("sb_publishable_")
                and 16 < len(self.publishable_key) <= 1024
                and all(33 <= ord(char) <= 126 for char in self.publishable_key)
            )
        except (TypeError, ValueError):
            valid_url = valid_key = False
        if not valid_url or not valid_key:
            raise AuthenticationUnavailable("Authentication service unavailable")

    @classmethod
    def from_environment(cls, transport: httpx.AsyncBaseTransport | None = None) -> SupabaseAuth:
        """Read server-owned configuration without credential fallbacks.

        Args:
            transport: Optional nondeterministic network boundary replacement.

        Returns:
            Adapter restricted to the approved Supabase project and publishable key.

        Raises:
            AuthenticationUnavailable: Configuration is missing or unsafe.
        """
        return cls(
            os.environ.get("SUPABASE_URL", ""),
            os.environ.get("SUPABASE_PUBLISHABLE_KEY", ""),
            transport,
        )

    async def authenticate(self, token: str) -> VerifiedIdentity:
        """Verify a token through a bounded real Auth user request.

        Args:
            token: Opaque Bearer access token supplied by the caller.

        Returns:
            Canonical identity and strict provider anonymous-account classification.

        Raises:
            AuthenticationRejected: Input is malformed or the provider rejects it.
            AuthenticationUnavailable: Provider transport, response or identity is unsafe.
        """
        try:
            return await asyncio.wait_for(self._authenticate(token), AUTH_TIMEOUT_SECONDS)
        except asyncio.TimeoutError:
            raise AuthenticationUnavailable("Authentication service unavailable") from None

    async def _authenticate(self, token: str) -> VerifiedIdentity:
        """Perform provider verification within the caller's total deadline.

        Args:
            token: Opaque access token.

        Returns:
            Provider-verified public identity.

        Raises:
            AuthenticationRejected: Provider rejects the caller.
            AuthenticationUnavailable: Provider data or transport is unsafe.
        """
        if not isinstance(token, str):
            raise AuthenticationRejected("Authentication required")
        token = bearer_token(["Bearer " + token])
        try:
            async with httpx.AsyncClient(
                transport=self.transport,
                timeout=AUTH_TIMEOUT_SECONDS,
                follow_redirects=False,
                trust_env=False,
            ) as client:
                async with client.stream(
                    "GET",
                    self.url.rstrip("/") + "/auth/v1/user",
                    headers={
                        "apikey": self.publishable_key,
                        "Authorization": "Bearer " + token,
                        "Accept": "application/json",
                        "Accept-Encoding": "identity",
                    },
                ) as response:
                    if response.status_code in (401, 403):
                        raise AuthenticationRejected("Authentication required")
                    if response.status_code != 200:
                        raise AuthenticationUnavailable("Authentication service unavailable")
                    if (
                        response.headers.get("content-encoding", "identity").strip().lower()
                        != "identity"
                    ):
                        raise AuthenticationUnavailable("Authentication service unavailable")
                    if (
                        response.headers.get("content-type", "").split(";", 1)[0].strip().lower()
                        != "application/json"
                    ):
                        raise AuthenticationUnavailable("Authentication service unavailable")
                    body = bytearray()
                    async for chunk in response.aiter_raw():
                        if len(body) + len(chunk) > MAX_RESPONSE_BYTES:
                            raise AuthenticationUnavailable("Authentication service unavailable")
                        body.extend(chunk)

            def reject_constant(value: str) -> None:
                """Reject non-JSON numeric extensions in the provider document.

                Args:
                    value: Decoder numeric constant.

                Raises:
                    ValueError: Nonfinite extensions are not valid JSON.
                """
                raise ValueError("invalid provider JSON constant")

            data = json.loads(
                body.decode("utf-8"),
                object_pairs_hook=_unique_object,
                parse_constant=reject_constant,
            )
            if not isinstance(data, Mapping) or type(data.get("is_anonymous")) is not bool:
                raise ValueError("provider identity fields missing")
            identifier = data.get("id")
            if not isinstance(identifier, str) or str(UUID(identifier)) != identifier:
                raise ValueError("provider identifier is not canonical")
            return VerifiedIdentity(identifier, data["is_anonymous"])
        except AuthenticationRejected:
            raise
        except (httpx.HTTPError, ValueError, TypeError, UnicodeError, RecursionError):
            raise AuthenticationUnavailable("Authentication service unavailable") from None


def auth_transport() -> httpx.AsyncBaseTransport | None:
    """Select the default real network boundary for server authentication.

    Returns:
        None so HTTPX uses its verified-TLS HTTP transport.
    """
    return None


def main() -> int:
    """Run a genuine registered/guest provider gate with explicit caller credentials.

    Returns:
        Zero for verified provider identities, two for missing integration inputs,
        or one for failed verification. Tokens and provider bodies are never printed.
    """
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-provider", action="store_true", required=True)
    parser.parse_args()
    required = (
        "SUPABASE_URL",
        "SUPABASE_PUBLISHABLE_KEY",
        "BGWQ_REGISTERED_ACCESS_TOKEN",
        "BGWQ_REGISTERED_USER_ID",
        "BGWQ_GUEST_ACCESS_TOKEN",
        "BGWQ_GUEST_USER_ID",
    )
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        print("Auth provider verification blocked: missing " + ", ".join(missing), file=sys.stderr)
        return 2

    async def verify() -> None:
        """Verify both genuine provider identities without exposing credentials."""
        provider = SupabaseAuth.from_environment()
        identities = []
        for kind, guest in (("REGISTERED", False), ("GUEST", True)):
            identity = await provider.authenticate(os.environ[f"BGWQ_{kind}_ACCESS_TOKEN"])
            if identity.id != os.environ[f"BGWQ_{kind}_USER_ID"] or identity.is_guest is not guest:
                raise AuthenticationUnavailable("Authentication service unavailable")
            identities.append(identity.id)
        if identities[0] == identities[1]:
            raise AuthenticationUnavailable("Authentication service unavailable")

    try:
        asyncio.run(verify())
    except (AuthenticationRejected, AuthenticationUnavailable):
        print(
            "Auth provider verification failed: identities could not be verified", file=sys.stderr
        )
        return 1
    print("Auth provider verification passed for distinct registered and guest identities")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
