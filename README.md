# BoardGamesWithQuests

A configurable two-player chess and English-draughts game built around a **game-neutral Python engine**. The target application has a single React web GUI, a FastAPI serverless API, Supabase accounts/game storage and a Tauri desktop wrapper that loads the **same hosted web app**.

**Current implementation status and release readiness:** See [.agents/SCRATCHPAD.md](.agents/SCRATCHPAD.md). A successful documentation build alone is not evidence of playable behavior.

## Target packages

```text
packages/
  engine/     Generic Python board/game/rule/quest execution
  chess/      Chess config.json and applicable format writers
  checkers/   WCDF English draughts config.json and applicable writers
  server/     Python FastAPI on Vercel Functions
  web/        React + TypeScript + Rsbuild + Bun + Tailwind + shadcn/ui
  desktop/    Tauri wrapper of the same hosted website
```

Everything configurable about pieces, boards, rules, quests and clocks comes from validated **JSON**. Game-owned code does not become a user-authored Python extension surface. The shared engine must never hardcode chess/checkers special cases. The production target uses **Supabase Auth (registered and guest identities), Postgres and Realtime**; authoritative moves execute in Python on Vercel. No leaderboard, classroom room system or separate desktop GUI is planned.

## Documentation and status

- [Canonical completion plan](.agents/notes/PLAN.md)
- [Product requirements](.agents/notes/PRD.md)
- [Approved deviations from original reference](.agents/notes/object_model.md)
- [Original UML and source reference](.agents/notes/reference_diagram.md)
- [Chess rule baseline](.agents/notes/chess_rules.md)
- [Current implementation status](.agents/SCRATCHPAD.md)
- [Operational development rules](.agents/AGENTS.md)
- [Consolidated Plan issue #129](https://github.com/marius-patrik/BoardGamesWithQuests/issues/129)

Current legacy Python smoke/discovery behavior is not the final web application and is not a gameplay acceptance test. Follow the single plan for implementation and deployment instructions as they become verified.
