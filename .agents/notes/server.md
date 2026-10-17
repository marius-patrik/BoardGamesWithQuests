# Server

`engine/` holds the moved Python engine, including its existing `controller/`.
`GameController` coordinates selections and moves; the retained
`WindowController` manages  and is .
Neither controller , authenticated multiplayer
commands, so those operations must not assume persistent in-memory instances.
 `api/index.py` is the ASGI entrypoint
for the separately deployed Vercel API project. It exposes only a real HTTP
health request; no game, authentication, or Supabase-backed route is implemented.

`supabase/` holds CLI configuration and a non-destructive private-schema
. No user or game tables are created until the database
contract is approved. The hosted Supabase project must not be reset or modified
by ordinary PR checks.

Local API:

```sh
python -m pip install -e .
uvicorn server.api.index:app --app-dir packages --reload
```

Run Supabase CLI commands from `packages/server` so the nested `supabase/`
directory is discovered. Provider deployment requires dedicated CI credentials
and approval; no credentials are stored in this repository.
