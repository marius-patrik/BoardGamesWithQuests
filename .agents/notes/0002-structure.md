---
status: published
---
# Current source layout

| Path | Responsibility |
| --- | --- |
| `packages/engine/app.py`, `__main__.py` | CLI diagnostics, game selection and guarded GUI entry |
| `packages/engine/controller/` | Square/move actions, window status, dialog and clock-control state |
| `packages/engine/model/game/` | Board, moves, chess validator, game manager, players, clock, quest, logging, game JSON loading |
| `packages/engine/model/pieces/` | Chess piece classes |
| `packages/engine/model/misc/` | Quest management, metadata, notation and chess export |
| `packages/engine/model/users/` | User profiles, ratings and activity |
| `packages/chess/`, `packages/checkers/` | Installed game metadata and `config.json` assets |
| `.agents/notes/`, `requests/`, `decisions/`, `rules/` | Authored README, PRD, architecture and AGENTS sources |
| `.agents/GOAL.md`, `PLAN.md`, `TODO.md`, `SCRATCHPAD.md` | Authored project outcome, plan, current tasks and temporary findings |
| `.agents/architecture/diagrams/`, `.agents/reference/` | Source-derived Mermaid and original reference assets |
| `.github/tests/`, `scripts/`, `workflows/` | Tests, generation, CI, documentation deployment and desktop release infrastructure |

`.agents/` and `.github/` are physical root directories. Root `README.md` and `CONTRIBUTING.md` link to generated sources. `repo.dfconfig` and `.darkfactory/installation.json` record DarkFactory configuration/integration.
