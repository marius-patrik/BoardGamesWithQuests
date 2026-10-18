---
status: accepted
---
# Current game configuration and source execution

`src/model/game/games.py` locates the packaged `src/games/` configurations; each game package assembles `Configuration` from Python `board.py`, `rules/`, `pieces/`, `quests/`, `clocks/` and exporter modules. `src/model/game/configuration.py` loads modules with `importlib` and exposes copying/renaming/deletion of configuration directories. `src/model/game/source_validation.py` validates editable Python by executing it, and `src/view/code_editor.py` is reachable from settings. This **is the current implementation**, not the approved target JSON-only model.

The archived #405 engine instead used validated schema-versioned JSON definitions, bounded conditions/hooks, immutable snapshots, revisioned actions and event replay. Those capabilities are absent from the present desktop working tree and must be integrated into one authoritative engine before replacing source editing. Requirements and architecture will be updated within #271 as the code is actually changed.
