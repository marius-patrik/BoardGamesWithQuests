# Server

Python ASGI application: `api/index.py` imports `server.app:app`.
Deploy the Vercel API project with the repository root as its project root,
including the `packages/` Python path and root `pyproject.toml`.

The `/health` route reports availability without pretending game readiness.
The `/games` route reads and validates the three JSON configurations and
returns `playable=false` until complete rules pass independent acceptance.

All mutations must verify the Supabase Auth identity and game participation,
then run generic domain legality through a server-only PostgreSQL transaction.
The private `bgwq` schema holds immutable config snapshots, revisions
and events. No service-role credentials are permitted in browser code.

API address: `https://boardgameswithquests-api.vercel.app`.
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
An exact retry can return a accepted event at the requested revision while the engine state is
the latest snapshot. If `event.revision <= loaded.revision`, return that event
and authoritative state without committing again. New actions commit only when
the event advances the loaded revision. Low-level SQL retries require the
accepted resulting snapshot; pairing a accepted event at the requested revision with the latest state
is invalid. Creation/activation retries similarly recover their persisted UUID
and genesis snapshot instead of generating another timestamp or game UUID.

Run the permanent real PostgreSQL suite with Docker available:

```sh
python -m pytest -q tests/test_private_transactions.py
```

The isolated suite is not hosted Supabase or JWT acceptance. After reviewing and
applying the forward migration, an authorized database connection can execute
`scripts/fixtures/provider_session_atomicity.sql` with error-stop enabled. That
probe rolls back all private test objects and never changes Auth identities or
protected unrelated records. A provider-backed authenticated gameplay adapter,
real HTTP concurrency/restart behavior and authorized Realtime recovery require
separate implementation and acceptance evidence.
