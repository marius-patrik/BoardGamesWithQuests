---
status: accepted
---
# Current game configuration and source execution

`src/model/game/games.py` locates the packaged `src/games/` configurations; each game package assembles `Configuration` from Python `board.py`, `rules/`, `pieces/`, `quests/`, `clocks/` and exporter modules. `src/model/game/configuration.py` loads modules with `importlib` and exposes copying/renaming/deletion of configuration directories. `src/model/game/source_validation.py` validates editable Python by executing it, and `src/view/code_editor.py` is reachable from settings. This **is the current implementation**, not the approved target JSON-only model.

Pure helpers from that archived implementation have now been restored as `src/model/game/schema.py`, `conditions.py` and `hooks.py`. They define bounded JSON validation, trusted read-only condition evaluation and immutable effect proposals; none mutates the board or replaces the active Python-loaded `Configuration` or legacy `GameManager` yet. Replacing that runtime is the next integration boundary.

The archived #405 engine instead used validated schema-versioned JSON definitions, bounded conditions/hooks, immutable snapshots, revisioned actions and event replay. Those capabilities are absent from the present desktop working tree and must be integrated into one authoritative engine before replacing source editing. Requirements and architecture will be updated within #271 as the code is actually changed.
