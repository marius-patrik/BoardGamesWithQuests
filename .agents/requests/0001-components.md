---
status: approved
---
# Implemented desktop application requirements

- The installed `boardgameswithquests` Python entry point opens the Tkinter game chooser and board; `--game` selects a bundled game and `--check` reports installed game assets without a display.
- `src/model/game/definition.py` validates schema-versioned, bounded inert JSON and constructs detached starting boards from declared generic piece capabilities. The bundled chess and English-draughts definitions remain marked `playable: false` until complete acceptance.
- The sole authoritative transition manager in `src/model/game/manager.py` accepts participant identity, exact action intent, expected revision and stable action ID. It isolates state preparation, validates legal moves and declarative hooks/effects, rejects inconsistent actions, increments revisions once, stores events and verifies snapshot replay. `src/model/game/session.py` exposes game creation/switch, snapshots, legal actions, submission, timeout polling, reset and recovery without HTTP or a database.
- `src/model/game/{board,move,validator,capture_geometry,capture_policy}.py` owns rectangular game boards, immutable JSON action intents and generic bounded geometric moves/capture routes. `{hooks,conditions,board_queries,snapshot_queries,outcomes}.py` owns the closed rule vocabulary, work-bounded read-only queries and deterministic outcome arbitration.
- `src/controller/` routes player square selection and action submission through the local session. `src/view/` renders detached board projections, legal-destination highlights, game switching, player clocks, quests, JSON history export, settings and error/terminal messages.
- `src/model/game/preferences.py` accepts only non-executable board-size/coordinate preferences; `settings_dialog.py` persists them under the OS application-data directory with strict type/range validation, symlink rejection and atomic replacement. The player-facing UI does not expose rules or quests for editing.
- Declarative game quests can earn once-only participant scores; the JSON game definitions currently declare first-move and first-capture rewards, shown in Tkinter progress cards.
- `.github/tests/` holds the acceptance and regression tests. `desktop-gameplay.yml` exercises the public local session on Python 3.10–3.13 and real Tkinter interaction via Xvfb; this does not establish completion of every chess/draughts rule, four native packages or the final release.
