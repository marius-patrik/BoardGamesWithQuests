---
status: approved
---
# Repository components

The Python application entry point, controller and game model are under `packages/engine/`. The model includes boards, moves, game management, validators, quests, players, users and chess piece implementations. The game-specific `packages/chess/config.json` and `packages/checkers/config.json` files provide JSON configuration assets.

The repository provides source-derived Mermaid diagrams and documentation through `.agents/` and `.github/scripts/`. GitHub Actions under `.github/workflows/` run development checks, documentation builds and other repository automation. `.github/tests/` contains test and acceptance assets. `repo.dfconfig` configures the existing DarkFactory integration.
