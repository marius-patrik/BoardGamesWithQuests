---
status: published
---
# BoardGamesWithQuests

BoardGamesWithQuests is a Python/Tkinter desktop board-game application. Its `src/chesswithquests/` entry point starts the GUI, `src/controller/` connects user interaction to gameplay, and `src/model/` holds board state, rules, moves, users, clocks, and quests. `src/games/chess/` and `src/games/checkers/` define the available board-game variants. Native GitHub Actions provide development checks and documentation automation.
The platform bootstrap also contains a FastAPI definitions route in `packages/server/`, a React client in `packages/client/`, and a Tauri shell in `packages/native/`. The route currently responds with an empty definitions list; the API does not expose gameplay sessions.
