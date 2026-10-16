# BoardGamesWithQuests

BoardGamesWithQuests is a board-game platform under construction. This branch
introduces its package and delivery foundation; it does **not** implement
playable chess, checkers, quests, multiplayer sessions, or a game database.

```text
packages/
  server/
    engine/             Existing Python engine, moved from packages/engine
    api/index.py        FastAPI ASGI bootstrap
    supabase/           Supabase CLI configuration and private schema bootstrap
  web/                  Bun + React + TypeScript + Rsbuild + shadcn/ui + Motion
  native/               Bun + Tauri 2 wrapper of the deployed Vercel website
```

The `chess` and `checkers` packages, Python GUI view/controller and launcher
have been removed at the maintainer's direction. The retained engine is not a
certified game-neutral implementation: game logic, API integration, persistence,
and acceptance remain future work.

## Development

- Python: `python -m pip install -e .` then `uvicorn server.api.index:app --app-dir packages --reload`
- Web: `cd packages/web && bun install && bun run dev`
- Native: `cd packages/native && bun install && bun run tauri dev`.
  The native window loads `https://boardgameswithquests-web.vercel.app`;
  this origin must be reachable.
- Database CLI: `cd packages/server && supabase start` for a local project.

Production automation is staged in `.github/workflows/`. It requires explicit
Vercel/Supabase credentials and protected environment approvals. Native release
builds require platform SDKs and signing, particularly on iOS. Build artifacts
are not evidence that gameplay or store distribution works.

## References

- [Original source UML](https://github.com/marius-patrik/BoardGamesWithQuests/blob/main/.agents/notes/reference_diagram.md)
- [Requirements (awaiting alignment with this migration)](https://github.com/marius-patrik/BoardGamesWithQuests/blob/main/.agents/notes/PRD.md)
- [Tracked implementation plan](https://github.com/marius-patrik/BoardGamesWithQuests/blob/main/.agents/SCRATCHPAD.md)
