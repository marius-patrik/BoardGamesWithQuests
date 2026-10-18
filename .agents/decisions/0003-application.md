---
status: accepted
---
# Current application entry, controllers and Tkinter views

`src/chesswithquests/__init__.py` parses `--game` and `--check`, reports available games and invokes the Tkinter application via `view.app.build_application`. `src/controller/controller.py` selects active-player squares, requests legal destinations from the game manager and attempts moves. `src/controller/window_controller.py` tracks application window and status state.

`src/view/app.py` coordinates window construction and game selection, while `game_view.py`, `player_game_view.py`, `player_view.py` and `quest_view.py` render the board and gameplay panels. `settings_dialog.py`, `code_editor.py` and `start_modal.py` handle settings, executable source editing and game selection. The domain is in-memory and uses the old mutable Python-configured manager, rather than the revisioned JSON transition API; full end-to-end widget and package acceptance remains unverified.
