# Server

Python ASGI application: `api/index.py` imports `server.app:app`.
Deploy the Vercel API project with the repository root as its project root,
including the `packages/` Python path and root `pyproject.toml`.

The public `/health` route reports availability without claiming game readiness.
The public `/games` route validates the shipped JSON configurations and returns
`playable=false` until complete rules pass independent acceptance.

## Verified identity

`GET /me` accepts exactly one `Authorization: Bearer <access-token>` header.
The scheme is case-insensitive with exactly one ASCII space separator. Tokens
contain visible ASCII without whitespace and are bounded to 16 KiB.
The server verifies each token with `GET /auth/v1/user` on the configured
Supabase project; it never trusts unchecked JWT claims, query/body identity
fields or user-editable metadata. Registered and anonymous guest accounts use
the same boundary. The response contains exactly `{id, is_guest}` with a
canonical UUID and strict boolean, excluding email and provider metadata.

Configure `SUPABASE_URL=https://wdthdcdoqdtywngwvddk.supabase.co` and
`SUPABASE_PUBLISHABLE_KEY` with the project's modern `sb_publishable_...` key.
Only the configured publishable key is accepted. Verification uses verified
TLS, a 5-second total verification deadline and HTTP I/O timeouts, no redirects or environment proxy credentials,
and a maximum uncompressed response body of 64 KiB. Requests explicitly
require identity encoding; compressed responses are rejected before body reads.
The total deadline cancels slow streams and closes the provider response. Missing/malformed credentials
and provider rejection return a generic 401 with a Bearer challenge. Missing
configuration, outages and malformed provider responses return a generic 503;
provider bodies and caller tokens are never returned. Identity responses and
errors prohibit caching with `Cache-Control: no-store` and vary by Authorization.

`tests/test_auth_behavior.py` exercises real application HTTP requests and the
actual provider adapter. Only its external network transport is replaced.
Genuine registered/guest provider acceptance requires distinct live identities:
set `BGWQ_REGISTERED_ACCESS_TOKEN`, `BGWQ_REGISTERED_USER_ID`,
`BGWQ_GUEST_ACCESS_TOKEN` and `BGWQ_GUEST_USER_ID`, then run:

```sh
PYTHONPATH=packages python -m server.auth --verify-provider
```

The command issues real provider requests without creating or deleting accounts.
Missing credentials exit with an explicit blocked result; failed verification
exits unsuccessfully. No mock or read-only catalog check satisfies this gate.

## Gameplay boundary

Gameplay mutations require verified identity, actual game participation,
generic domain legality and a server-only atomic PostgreSQL commit. The private
`bgwq` schema holds immutable configuration snapshots, revisions and events.
Gameplay routes remain unavailable until real database/auth/participant gates
pass. Retained unrelated records and Auth identities are protected from cleanup.

API address: `https://boardgameswithquests-api.vercel.app`.
Real persistence, two-participant authorization, realtime recovery and classroom
guest capacity require their separate provider/browser integration gates.
