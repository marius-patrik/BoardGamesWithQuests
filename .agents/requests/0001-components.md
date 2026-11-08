---
status: approved
---
# Current Python engine requirements

## Installed package and CLI

- `pyproject.toml` packages `engine`, `chess` and `checkers` from `packages/` with Python >=3.10 and declares `chesswithquests = engine.app:main`.
- `engine.app` accepts `--game` and `--check`; `--check` reports installed package names and readiness without creating a Tk window. Normal startup resolves a default or explicitly named game, fails closed on invalid/unplayable definitions and handles unavailable Tk or view code with distinct errors.
- Both currently installed JSON game definitions explicitly set `playable: false`, so these entry points are not a claim of working GUI gameplay.

## Discovery and game configuration

- Installed packages register through `boardgameswithquests.games`. An entry-point name must match the discovered `config.json` name, duplicates must be rejected, and no more than one default game can be declared.
- The implemented validator requires `schema_version: 1`, nonempty name/title, boolean default/playable flags, integer board dimensions between 1 and 256, nonempty piece definitions, distinct in-bounds starting squares, valid piece IDs and white/black team names.
- Each declared piece requires symbols for both colors, nonzero integer movement/attack coordinate vectors and boolean jump/repeat properties. Clocks require nonnegative integer initial/increment seconds; exports are string identifiers and appearance an object.
- The chess and English-draughts JSON files provide separate 8×8 layouts and piece metadata. Their declarations do not automatically instantiate complete game rules or gameplay.

## Actual engine and controller behavior

- `Board` owns a piece matrix and captured-piece collections; its built-in 8×8 setup creates the standard chess position. `Move` records origin/target/capture/promotion data; `Move.validate` currently assumes 8×8 coordinates.
- `MoveValidator` calculates chess move legality, attacked squares and check/checkmate/stalemate. `GameManager` coordinates board, two players, active turn, timer, validator and logger; successful moves are executed/logged and toggle the active player. `GameManager.save_log` is presently a no-op.
- `Timer` provides player clocks, reset, tick, increments and expiry. `Quest` represents condition-based completion and reward points; `QuestManager` registers, evaluates and optionally credits completed quests to users.
- `GameController` routes square selections and attempted moves; `WindowController` holds running/status/dialog state and clock ticks. These are controller-side functions, not proof of a completed Tkinter widget tree.
- Chess notation/metadata/export classes are part of the installed model, but existence of an export class does not prove end-to-end export acceptance.

## Known scope boundary

The model retains chess-specific assumptions and lacks a playable installed GUI. It is not yet a complete generic draughts or arbitrary-board engine. Current requirements must be updated in the owning implementation PR whenever those capabilities actually change.
