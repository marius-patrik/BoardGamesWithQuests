# Server

ASGI: `api/index.py` at the repository root imports `server.app:app`.
Deploy the API Vercel project with the **repository root** as its project root;
the separate web project uses `packages/web`.

There are no gameplay endpoints yet. `/health` explicitly reports
`playable: false`. Public read-only `/games` enumerates installed versioned
JSON definitions with each game's honest `playable` flag. Supabase Auth/JWT authorization, Postgres
transactions, RLS, migrations and Realtime are G4 implementation work.
Python dependencies come from the repository-root `pyproject.toml`.
