---
status: approved
---
# Application components

The installed Python package exposes a `boardgameswithquests` desktop entry point backed by `chesswithquests.main`. The application uses Tkinter for game selection, board display, player controls and settings. Its Python model includes configurable boards, moves, rules, validation, game state, players, users, clocks and quests. Chess and checkers are implemented under `src/games/` and share that model. `.github/tests/` contains application and repository-verification tests. DarkFactory and GitHub Actions own the repository's development and release workflows.
The platform source additionally includes an HTTP definitions-list route at `GET /api/v1/definitions` which returns an empty list, React sign-in and catalog components, and a native WebView/Tauri configuration. Those source components are separate from the Python/Tkinter desktop application and share no duplicated engine implementation.
