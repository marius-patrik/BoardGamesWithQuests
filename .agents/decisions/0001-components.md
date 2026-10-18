---
status: accepted
---
# Current Python/Tkinter domain model

## Board, moves and rules

`src/model/game/board.py` owns the current mutable board representation. `src/model/game/move.py`, `validator.py` and `rule.py` provide move actions, checks and composable Python rule evaluation. `src/model/game/manager.py` coordinates the constructed `Configuration`, players, turn state, active clocks, move/result events, quest manager, logs and exports. It exposes `make_move`, `get_valid_moves`, `get_state`, `finish_game` and `transcript` rather than the archived JSON engine's `submit_action` and versioned replay API.

## Supporting state

`src/model/game/timer.py`, `clock_fields.py` and variant clock modules manage countdown and increments. `src/model/game/quest.py`, `quests.py` and `src/model/misc/quest_manager.py` manage executable Python quests and rewards. `src/model/misc/` owns notation, metadata and exporters; `src/model/users/` owns user data. These modules do not implement server-backed authentication or persistence.

## Variants and limitations

`src/games/chess/` and `src/games/checkers/` compose boards, pieces and named Python rules through `build_configuration()`. Checkers currently supplies flying kings, not English-draughts short-range kings. The canonical JSON-driven configuration and immutable transactional engine planned for v1.0.0 are not yet connected to this model; implementing them requires replacing the existing executable-configuration path, not adding a competing engine.
