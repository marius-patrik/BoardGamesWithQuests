---
status: published
---
# Source and documentation layout

- `src/chesswithquests/` is the Python/Tkinter application entry point.
- `src/controller/` owns GUI action dispatch; `src/view/` owns Tkinter interface widgets.
- `src/model/` contains the shared game model, validation, rules, clocks, quests, notation and users.
- `src/games/chess/` and `src/games/checkers/` contain the individual game implementations and configuration modules.
- `.agents/notes/`, `.agents/requests/`, `.agents/decisions/` and `.agents/rules/` generate README, PRD, architecture and contributor-rule documents.
- `.github/tests/` owns repository tests and fixtures. `.github/workflows/` and `.github/scripts/` contain CI and source-generated documentation tools.
- Root `README.md` and `CONTRIBUTING.md` link to the generated documents; `.darkfactory/installation.json` records the DarkFactory integration.
