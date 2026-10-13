# BoardGamesWithQuests

A JSON-driven two-player board-game platform for orthodox chess, English
draughts and international draughts. One game-neutral Python engine interprets
bounded JSON boards, piece capabilities, rules, quests, clocks and outcomes.
FastAPI serves authoritative play from Vercel Python Functions; Supabase
provides authentication, database and Realtime. The React/Rsbuild web app is
also the UI for a remote Tauri 2 desktop wrapper.

Three shipped configurations are intentionally non-playable until complete
legal-rule integration passes the behavior suite. The public website and
read-only API catalog do not offer simulated gameplay.

## Source layout

- `packages/engine/` — generic geometry, conditions, effect planning and game state.
- `packages/chess/` — orthodox chess JSON definition and game-owned exports.
- `packages/english_draughts/` — 8×8 draughts JSON definition.
- `packages/international_checkers/` — 10×10 international draughts JSON definition.
- `packages/server/` — FastAPI ASGI boundary; `api/index.py` is the entry point.
- `packages/web/` — React/TypeScript/Rsbuild/Bun browser interface.
- `packages/desktop/` — Tauri remote-WebView wrapper.
- `supabase/migrations/` — reproducible private persistence and access migrations.
- `tests/` — externally observable domain/API/database behavior verification.

## Interfaces

The public health and game-catalog API is hosted at
`https://boardgameswithquests-api.vercel.app`.
The browser application is hosted at
`https://boardgameswithquests-web.vercel.app`.

Gameplay and authentication require the remaining G2–G7 implementation;
all public catalog entries expose `playable=false`.

## Contract and contribution rules

- [Product requirements](.agents/notes/PRD.md)
- [Architecture decisions](.agents/notes/object_model.md)
- [JSON rule contract](.agents/notes/json_contract.md)
- [Delivery plan](.agents/notes/PLAN.md)
- [Engineering and behavior test requirements](.agents/AGENTS.md)
- [Reference diagram](.agents/notes/reference_diagram.md)

The game reference diagrams are supplied design inputs; source-derived
diagrams are generated independently. GPL-3.0-only governs the source.
