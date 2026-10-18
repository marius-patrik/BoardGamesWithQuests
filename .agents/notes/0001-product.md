---
status: published
---
# BoardGamesWithQuests

BoardGamesWithQuests combines a Python board-game model, configurable chess and English-draughts definitions, controllers, clocks, and quest-related models. The repository's first delivery target is a self-contained Python/Tkinter desktop app; the current branch contains the engine and installed game metadata, **not** the completed graphical app. The existing [Plan](../PLAN.md) governs delivery.

## Current capabilities

The shared engine includes a chess board and piece classes, move validation, turn/game-state coordination, players/users, per-player countdowns, quest evaluation, move logging and notation/export helpers. The `chess` and `checkers` packages install 8×8 declarative JSON configurations with placements and piece vectors; both currently declare `playable: false`. The `chesswithquests --check` command reports registered games without opening a window.

## Documentation and verification

Current requirements are generated into the [PRD](../PRD.md) from approved `requests/`; the [Architecture](../ARCHITECTURE.md) derives from accepted `decisions/`. Outcomes, actions and investigation live in [Goal](../GOAL.md), [Plan](../PLAN.md), [TODO](../TODO.md) and [Scratchpad](../SCRATCHPAD.md). GitHub Actions and DarkFactory own tests, documentation builds and guarded release infrastructure. Passing engine checks does not itself establish complete playable desktop functionality.
