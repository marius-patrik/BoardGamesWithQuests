---
status: accepted
---
# Desktop application and UI ownership

`chesswithquests:main` validates game selection and launches a local JSON-backed `DesktopSession`. Its `--check` option loads all installed bundled definitions and accepts/retries/replays real opening moves without needing a display.

`view.app.build_application` constructs Tkinter game selection and gameplay. `GameController` maps clicks to complete legal action intents and submits them with actor IDs and expected revisions. `WindowController` manages status and authoritative timeout polling. The widgets do not own independent game state.

`BoardView` renders detached board projections and legal highlights; `PlayerGameView` handles UI refresh, alternate action choice, game switching, history, atomic JSON snapshot export, replay-verified Open Game recovery and safe callback cancellation. `PlayerView` and `QuestList` render authoritative clock/captures and configured quest progress/rewards. `SettingsDialog` changes only validated persisted presentation preferences.

`desktop-gameplay.yml` verifies these interactions under Xvfb, while `desktop-native-acceptance.yml` builds four self-contained frozen applications. The separate frozen GUI user-path acceptance remains an outstanding release requirement.
