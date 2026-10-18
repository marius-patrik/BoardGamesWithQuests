# Repository implementation record

This document describes the **code and controls in this branch**, not a desired product specification. All proposed implementation contracts and pending acceptance are maintained exclusively in [issue #348](https://github.com/marius-patrik/BoardGamesWithQuests/issues/348).

## Committed application boundaries

- `packages/server/engine/`: moved legacy Python board-game/controller modules. This is not a generic, multiplayer or authoritative database-backed runtime. `GameController` and `WindowController` remain present.
- `packages/server/api/index.py`: minimal FastAPI application. `GET /api/v1/definitions` returns `[]`; no game detail, authentication proxy, join, action or persistence routes.
- `packages/client/`: Bun/Rsbuild/React browser shell, Supabase Auth integration and an empty-catalog client. No published game definitions or gameplay are implemented.
- `packages/native/`: Tauri 2 project wrapping the external hosted web application. Bundling and code-signing are not claimed operational without platform/provider acceptance.
- `packages/server/supabase/config.toml`: local Supabase CLI initialization only. No deployed app schema/migrations are asserted.
- `.github/workflows/`: package build/test and provider-deployment definitions; the presence of a workflow is not evidence of a successful deployment.

## Verification and changes

Each implementation PR updates the records, tests and documentation affected by **its own implemented change**, checks actual consumer/provider behavior including edge cases, and reports unverified external requirements as **BLOCKED**. Planned schemas, DTOs, operator inventories, future game definitions and desired API graphs must remain in issues until implemented and independently verified.
