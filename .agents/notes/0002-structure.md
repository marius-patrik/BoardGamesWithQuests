---
status: published
---
# Source and repository layout

| Path | Responsibility |
| --- | --- |
| `src/chesswithquests/` | Application entry point, CLI arguments and bundled-resource diagnostics |
| `src/model/game/definition.py`, `schema.py` | Strict versioned JSON game definitions and immutable snapshots of configuration |
| `src/model/game/manager.py`, `session.py` | Authoritative revisioned game transitions/replay and local two-player desktop session |
| `src/model/game/{board,move,validator,capture_geometry,capture_policy}.py` | Generic board, complete action intents, geometry and capture search |
| `src/model/game/{hooks,conditions,board_queries,snapshot_queries,outcomes}.py` | Bounded declarative rules, trusted queries and terminal proposals |
| `src/model/game/persistence.py` | Bounded atomic saved-game export and replay-verified import |
| `src/model/game/preferences.py` | Validated user display preferences and atomic OS-specific persistence |
| `src/controller/` | Player input, action routing, selection state and window lifecycle |
| `src/view/` | Tkinter board, history, players, quests, settings and game chooser |
| `src/games/{chess,checkers}/config.json` | Immutable shipped rules and starting positions in versioned JSON |
| `.github/tests/`, `.github/workflows/` | Central tests, native packaging, governance and guarded release automation |
| `.agents/{notes,requests,decisions,rules}/` | Canonical sources of generated README, PRD, ARCHITECTURE and AGENTS |
| `.agents/{GOAL,PLAN,TODO,SCRATCHPAD}.md` | Goal, execution plan, current queue and investigation evidence |

Source-derived diagrams in `.agents/architecture/diagrams/` are generated from tracked code. Native builds target Windows x64, Linux x64 and both macOS architectures.
