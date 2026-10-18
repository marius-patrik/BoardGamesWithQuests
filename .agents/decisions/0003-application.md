---
status: accepted
---
# Application entry and controller boundary

## Current entry points

`pyproject.toml` maps the `chesswithquests` GUI script to `engine.app:main`; `python -m engine` delegates to the same function. It parses `--game` and `--check`. The latter prints installed game readiness without opening a display. Normal launch resolves a named/default registered `GameDefinition`, rejects invalid or `playable: false` games, then attempts `tkinter.Tk()` and `engine.view.app.build_application`. Missing Tkinter, display failure and missing view produce separate error paths. The existing `engine.view` package is a placeholder interface, not a completed GUI.

## Controller interactions

`GameController` owns the `GameManager`, selected square and highlighted valid destinations. `select_square` checks active-player piece ownership; `handle_square_click` distinguishes selected/reselected/moved/invalid/none and reports move origin/destination and resulting state. `new_game` replaces the manager and clears UI selection state.

`WindowController` stores nominal window title/dimensions, running state, status message and an active dialog message. It dispatches clicks to `GameController`, updates status text and ticks the active player's clock. It is state/controller logic rather than Tkinter widgets.

## Responsibility boundary

`engine.app` owns startup and game selection; controllers own interaction state. The installed view interface does not provide a playable Tkinter application.
