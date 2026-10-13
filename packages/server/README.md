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
