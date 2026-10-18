# BoardGamesWithQuests

The repository contains a Python board-game engine under `packages/server/engine/`, a minimal FastAPI endpoint under `packages/server/api/`, a React/TypeScript browser shell in `packages/client/`, and a Tauri wrapper in `packages/native/`. The existing chess/checkers-specific Python modules remain within the moved engine; they are **not** a completed declarative rule interpreter.

The **only implemented HTTP endpoint** is `GET /api/v1/definitions`, which deliberately returns an empty JSON array. There is no published catalog, game session service, durable game state, transactional action processing, or completed multiplayer implementation. The browser shell provides Supabase Auth integration when configured, but the built-in game catalog is empty. The native shell loads the hosted browser app; signed platform releases and provider availability require separate verification. The Supabase CLI configuration has no application migration installed by this PR.

## Local verification

```bash
python -m pip install -e .
python -m pip install -r requirements-dev.txt
pytest -q tests/test_api_catalog.py tests/test_controller_interaction.py
uvicorn server.api.index:app --app-dir packages --reload
```

From `packages/client/`, run `bun install --frozen-lockfile`, `bun run typecheck` and `bun run build`. From `packages/native/`, run `bun install --frozen-lockfile` and `bun run verify-config`. Local native builds additionally need the platform's Tauri/Rust system dependencies.

**Requested product behavior, prospective API/schema/DSL/game contracts, and unfinished acceptance criteria are kept only in [issue #348](https://github.com/marius-patrik/BoardGamesWithQuests/issues/348)**. The configuration and workflows in this PR do not establish that the Vercel web/API deployments, Supabase production instance, native distribution or public Pages site are available.
