---
status: approved
---
# Current desktop application components

- `pyproject.toml` installs the Python source from `src/` and exposes the `boardgameswithquests` GUI script backed by `chesswithquests:main`, requiring Python 3.10+. `--check` lists game configurations without opening Tkinter.
- `src/view/` contains the Tkinter application, board display, game selection, player/quest panels and settings. `src/controller/` mediates UI square selections and move attempts.
- The current `src/model/game/configuration.py` discovers per-game Python packages and constructs configurations by dynamically importing rule, quest, piece and clock modules. It implements configuration copy, rename, delete and value persistence. `src/model/game/source_validation.py` executes user-authored source for validation, and `src/view/code_editor.py` exposes editing. **Current implemented behavior is not JSON-only and is not a secure declarative game configuration boundary.**
- `src/model/game/{schema,conditions,hooks}.py` now validate and evaluate bounded declarative JSON rules without executing user Python. They produce pure effect proposals but are not yet the active game transition interface; their targeted tests are **foundation checks**, not playable-app acceptance.
- `src/model/game/manager.py` coordinates game state, moves, turns, clocks, quests and supported exports via Python `Configuration`, `MoveValidator` and `Rule`. It does not expose #405's revisioned JSON `submit_action` API, immutable snapshots or replay coordinator.
- Chess and checkers are assembled under `src/games/` from Python board, piece, rule, clock, quest and export components. The checkers source explicitly documents flying kings despite its English-draughts label; it is not yet a verified English-draughts implementation.
- `.github/tests/` contains game and integration tests, but graphical tests may skip without a display. The four-platform PyInstaller/release pipeline exists in workflow source but the current native GUI packages have not been accepted or published.
