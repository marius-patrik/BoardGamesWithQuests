---
status: approved
---
# Implemented desktop components

- `chesswithquests:main` exposes the installed `boardgameswithquests` GUI script, interactive game chooser and a `--check` installed-product diagnostic that loads bundled definitions and validates real opening submission, idempotent retry and replay.
- `src/model/game/definition.py` validates strict version-2 trusted JSON rulebooks. The source-controlled chess and English-draughts definitions reside under `src/games/{chess,checkers}/config.json` and currently declare `playable: false`.
- `src/model/game/manager.py` alone owns authoritative revisioned game state, participant/turn authorization, bound legal actions, effect preparation, accepted-action events, clocks, quest scores, terminal arbitration and deterministic replay. Rejections do not partially mutate authoritative game state. `session.py` provides the local game lifecycle through snapshot, legal actions, submit, reset, recovery and timeout polling.
- `Board`, `Piece`, `Move`, `MoveValidator` and `CaptureEnumerator` implement generic rectangular boards, data-derived movement geometry, immutable complete action intents and bounded captures. `schema.py`, `hooks.py`, `conditions.py`, `board_queries.py`, `snapshot_queries.py` and `outcomes.py` own the inert rule vocabulary and trusted bounded queries/effects/outcome proposals.
- `src/controller/` forwards square selection and action submission through `DesktopSession`; `src/view/` displays detached game state, legal choices, player clocks, quest progress and history, plus atomic replayable JSON game export and an Open Game action that validates and reconstructs saved sessions without losing the current game on failure. Game-owned rules/quests cannot be edited from the UI.
- `preferences.py` accepts only board-size/coordinate visibility preferences and stores them atomically in an OS-specific application-data directory, independently of immutable built-in rules.
- `.github/tests/` centralizes repository-owned tests; `desktop-gameplay.yml` runs local-session behavior on Python 3.10–3.13 and actual Tkinter interactions under Xvfb. `desktop-native-acceptance.yml` invokes the four-OS executable packaging matrix without publishing a release.
