---
status: published
---
# BoardGamesWithQuests

BoardGamesWithQuests currently contains a recoverable Python/Tkinter desktop board-game application with chess and checkers code, configurable rules, quests, clocks, game history, settings, and notation/export helpers. The shipped `src/` tree is the current implementation; the planned JSON-only rule system and complete release are **not yet implemented**.

## Current application

`src/chesswithquests/` owns startup and installation checks. `src/controller/` handles square selections and game control. `src/model/` implements board state, move validation, rule composition, clocks, players, quests, and export helpers. `src/view/` owns Tkinter windows, board/player/quest panels and settings. `src/games/chess/` and `src/games/checkers/` provide Python-authored game compositions.

## Important implementation boundary

Game settings still load executable Python configuration modules, with a source editor and validator exposed through the UI. This contradicts the desired JSON-only game definition model and must be replaced before v1.0.0. Pure JSON schema, condition and hook helpers have been restored from the archived work under `src/model/game/`, but they are not connected to the running game manager or Tkinter. The full revisioned JSON engine from #405 is still being reconciled. Source test success does not establish full GUI or packaged application acceptance.

## Delivery and governance

The [Plan](../PLAN.md) records recovery and verification steps, [TODO](../TODO.md) tracks open actions, and [Scratchpad](../SCRATCHPAD.md) stores current evidence. Approved [requirements](../PRD.md) and accepted [architecture](../ARCHITECTURE.md) describe the actual code. GitHub Actions and DarkFactory provide checks and a disabled-until-ready desktop release pipeline.
