---
status: approved
---
# Application components

The installed Python package exposes a `boardgameswithquests` desktop entry point backed by `chesswithquests.main`. The application uses Tkinter for game selection, board display, player controls and settings. Its Python model includes configurable boards, moves, rules, validation, game state, players, users, clocks and quests. Chess and checkers are implemented under `src/games/` and share that model. `.github/tests/` contains application and repository-verification tests. DarkFactory and GitHub Actions own the repository's development and release workflows.
