---
status: published
---
# Source and documentation layout

- `packages/engine/app.py` exposes the Python application entry point, game selection and installation diagnostics.
- `packages/engine/controller/` implements board-selection and move-action coordination.
- `packages/engine/model/game/` contains the board, configuration loader, game manager, move validator, turn and clock logic, quest and logging primitives.
- `packages/engine/model/pieces/`, `model/users/` and `model/misc/` contain chess piece classes, user/player state and notation/export helpers.
- `packages/chess/config.json` and `packages/checkers/config.json` are installed game configuration assets; the Python entry-point group `boardgameswithquests.games` discovers them.
- `.agents/notes/`, `.agents/requests/`, `.agents/decisions/` and `.agents/rules/` generate the README, PRD, architecture and contributor-rules documents.
- `.agents/architecture/diagrams/` contains source-derived Mermaid diagrams; `.agents/reference/` retains reference drawings and artwork.
- `.agents/agents/` and `.agents/skills/` contain reusable guidance. `.agents/roadmap/` contains explicitly prospective, non-normative delivery planning, including the [v1.0.0 delivery plan](../roadmap/v1.0.0.md).
- `.github/scripts/`, `.github/workflows/` and `.github/tests/` contain documentation tools, CI/release automation and repository verification.
- Root `README.md` and `CONTRIBUTING.md` link to generated documents. `.darkfactory/installation.json` records the DarkFactory integration.
