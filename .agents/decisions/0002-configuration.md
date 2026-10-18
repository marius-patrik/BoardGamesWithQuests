---
status: accepted
---
# Game configuration and package discovery

## Decision: installed entry points own the game registry

`pyproject.toml` installs the `engine`, `chess`, `checkers` packages under `packages/`. The `boardgameswithquests.games` entry-point group registers named game packages. `engine.model.game.configuration` iterates registered entry points using `importlib.metadata`, loads each package's `config.json` through `importlib.resources` and returns immutable `GameDefinition` dataclasses. It rejects duplicate/mismatched names, malformed records, and multiple declared defaults.

## Current configuration format

A `schema_version: 1` definition has `name`, `title`, boolean `default` and `playable`, `board` with row/column dimensions and starting-piece placements, `pieces` with colors/symbols/movement and attack vectors/jump/repeat flags, `clock` with starting/increment seconds, `exports` and `appearance`. The loader checks valid dimensions (1–256), unique in-bounds positions, declared pieces, two colors, nonzero integer vectors, nonnegative times and field types.

`packages/chess/config.json` describes initial chess pieces and vector metadata. `packages/checkers/config.json` describes English-draughts men and kings and their layout. Both describe 8×8 boards; both currently set `playable: false`. Configuration discovery/validation is implemented; transforming this metadata into a complete playable rules engine is **not** yet implemented.

## Ownership consequence

`engine.model.game.games` supplies available/default game names and package paths. Game-specific data remains with installed packages; shared validation belongs to the engine. A future implementation must update this decision if the JSON/runtime ownership changes.
