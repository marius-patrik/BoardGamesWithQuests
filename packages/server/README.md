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
Behavioral acceptance: `tests/`, the live HTTP CI job and the private
Supabase transaction fixture.

## Private game lifecycle

The database contract lives in [.agents/notes/json_contract.md](../../.agents/notes/json_contract.md).
`bgwq.create_game` records a pending creator and validated JSON definition;
`bgwq.activate_game` fills the second participant once using a canonical engine
snapshot. Foreign keys enforce existing Supabase Auth UUIDs without granting
service-role reads of Auth records. There is no separate room subsystem.
Activation produces a database genesis event at revision `0`, distinct from the
empty engine history. Domain actions begin at revision `1`.

`bgwq.commit_revision` accepts the verified actor, expected revision, engine-
validated resulting snapshot and accepted event. Its atomic state/event commit
checks identity, turn, immutable configuration, event metadata and request
fingerprint. Creation, activation and domain actions use separate key scopes;
conflicting same-scope reuse fails without mutation.

After loading a snapshot, reconstruct the engine and validate the request.
An exact retry can return an accepted event at the requested revision while the engine state is
the latest snapshot. If `event.revision <= loaded.revision`, return that event
and authoritative state without committing again. New actions commit only when
the event advances the loaded revision. Low-level SQL retries require the
accepted resulting snapshot; pairing an accepted event at the requested revision with the latest state
is invalid. Creation/activation retries similarly recover their persisted UUID
and genesis snapshot instead of generating another timestamp or game UUID.

Run the permanent real PostgreSQL suite with Docker available:

```sh
python -m pytest -q tests/test_private_transactions.py
```

The isolated suite is not hosted Supabase or JWT acceptance. After reviewing and
applying the forward migration, an authorized database connection can execute
`scripts/fixtures/provider_session_atomicity.sql` with error-stop enabled. That
probe rolls back all private test rows and never changes Auth identities or
protected unrelated records. A provider-backed authenticated gameplay adapter,
real HTTP concurrency/restart behavior and authorized Realtime recovery require
separate implementation and acceptance evidence.

## Internal durable adapter

`server.persistence.GameStore` provides async `create`, `join`, `read` and
`submit` operations over the private lifecycle functions. Callers supply a
provider-verified canonical UUID, a stable bounded action ID, validated
`GameDefinition`, canonical game UUID, expected revision, `Move`, and explicit
trusted epoch milliseconds as applicable. It does not verify JWTs. Reads are
participant-scoped. Creation retries recover the persisted UUID; joining retries
recover the persisted genesis snapshot, even after moves. Accepted move retries
return the accepted event with authoritative state without committing again. Concurrent
new transitions use one compare-and-swap and surface `Conflict`; callers must
refetch before making another decision.

Configure server-only `BGWQ_DATABASE_DSN` with `sslmode=verify-full` and one explicit
network hostname or IP address. Socket, omitted, multiple and hostaddr endpoints
are rejected, as are service/options overrides and ambient PGHOSTADDR/PGSERVICE
configuration. Connections
are operation-local with GSS encryption disabled to require TLS, and prepared
statements disabled for transaction pooling,
3-second connect and statement/lock bounds and a 10-second active-operation
deadline including pure work. Cancellation drains psycopg cancellation (up to
five seconds each for sending cancellation and waiting for query termination),
then allows three seconds for rollback before forcibly closing the connection.
This cleanup tail can extend response time beyond ten seconds. An I/O failure or
lost commit acknowledgement can leave the result indeterminate: refetch or retry
the exact same key and request; never allocate a new key or blindly replay.
All engine construction, replay, JSON decoding and serialization run in two fixed
pure worker slots with no waiting queue. Capacity exhaustion fails explicitly.
The active-operation deadline includes creation canonicalization. Timed-out or cancelled
workers cannot access SQL or publish a result; their slots remain reserved until
their computation finishes. Active reads and activation recovery validate canonical
replay plus row identity, configuration and revision before returning state.
Only explicit loopback test DSNs may use `local_test=True, sslmode=disable`.
Public exceptions redact database diagnostics. No cache holds authoritative state.
Catalog and gameplay readiness remain false; no playable route exposes the store.

Run genuine adapter acceptance (Docker and OpenSSL required, no skips or mock DB):

```sh
python -m pip install -e . -r requirements-dev.txt
python -m pytest -q tests/test_persistence_adapter.py
```

The fixture binds an ephemeral host port to `127.0.0.1` and connects as a real
`service_role` login. Its Auth rows are isolated FK fixtures, not verified tokens.
Root must independently run these tests before integration. Dependency or Docker
failure blocks this gate; compilation alone provides no behavioral evidence.

A read-only hosted probe needs `BGWQ_DATABASE_DSN`, `SUPABASE_URL`,
`SUPABASE_PUBLISHABLE_KEY`, `BGWQ_REGISTERED_ACCESS_TOKEN`,
`BGWQ_REGISTERED_USER_ID`, and `BGWQ_PROVIDER_GAME_ID` for an existing game in
which that verified identity participates:

```sh
PYTHONPATH=packages python -m server.persistence --verify-provider
```

Missing inputs fail explicitly. The probe makes no provider writes and certifies
only identity verification plus a participant-scoped real database read. Hosted
mutation, authenticated HTTP, Realtime and complete gameplay gates remain open.
