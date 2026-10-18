---
status: published
---
# BoardGamesWithQuests

BoardGamesWithQuests is a configurable board-game project centered on **chess, English draughts (checkers), and gameplay quests**. It keeps the game state and rule evaluation in Python, with game-specific definitions separate from the shared board, move, player, clock and quest models. The target distribution is a locally installed Python/Tkinter application; its release preparation is tracked separately in the [v1.0.0 delivery plan](../roadmap/v1.0.0.md).

## Game definitions and state

The installed `chess` and `checkers` packages each ship a versioned `config.json` containing board dimensions and starting pieces, named piece movement and attack vectors, symbols, clock settings, exports and display colors. Game definitions are validated before use and discovered through Python package entry points. The current configurations explicitly declare `playable: false`; the engine and configuration records do not by themselves certify end-to-end GUI gameplay.

The Python engine provides an 8×8 board model, chess-piece movement and legality helpers, a game manager for turns and terminal-state checks, player/user data models, clocks, event/logging components, quest evaluation and notation/export classes. The controller translates square-selection and move requests into engine operations. A `chesswithquests --check` diagnostic lists installed game packages without opening a window.

## Repository delivery

`.agents/` contains the canonical product, architecture and engineering guidance; GitHub Actions and DarkFactory run tests and produce source-derived documentation. The documented current components are distinct from the release acceptance required for the finished desktop application.
