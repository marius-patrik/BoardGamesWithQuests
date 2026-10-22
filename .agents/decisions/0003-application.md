---
status: accepted
---
# Desktop entry, controllers and Tkinter view ownership

`chesswithquests:main` validates game selection and builds a local `DesktopSession` with two participants. `view.app.build_application` constructs the Tkinter game window and selector; `GameController` maps player square clicks to legal complete intents and submits them with expected revisions; `WindowController` owns window status and timeout polling.

The Tkinter `BoardView` renders detached board projections and selected/legal destinations, while `PlayerGameView` owns UI refresh, game switching, move-choice dialogs, history, JSON snapshot export and shutdown callback cancellation. `PlayerView` and `QuestList` display clock/capture status and immutable quest descriptions/progress. `SettingsDialog` edits only allowlisted persisted presentation preferences.

`desktop-gameplay.yml` exercises these widgets under Xvfb; publication acceptance still requires complete game behavior and real frozen native executables.
