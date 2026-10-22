---
status: published
---
# BoardGamesWithQuests

BoardGamesWithQuests provides a local Python/Tkinter chess and English-draughts application using immutable JSON game rules, two-player actions, clocks, quests, game history, settings and replayable JSON exports. Both shipped game definitions remain marked `playable: false` until full reference-game acceptance is verified.

## Desktop runtime

`src/chesswithquests/` owns startup, bundled-resource diagnostics and the installed application entry point. `src/model/game/` owns one revisioned, deterministic game engine and its local `DesktopSession`. `src/controller/` translates player clicks into legal actions. `src/view/` owns the Tkinter board, player and quest panels, game chooser and preferences.

Game positions, movement, captures, conditions, effects, quests and outcomes come from strictly validated source-controlled JSON rulebooks. The executable Python rule packages, dynamic configuration loader and player-facing code editor are absent from the desktop application.

## Local player experience

The application renders detached authoritative state, supports mouse-driven moves, displays available destinations and handles configured capture/promotion choices. Accepted actions update clock/turn ownership, quests and history atomically. Settings change only board-square size and coordinate display through validated, persistent JSON preferences. The application atomically exports full replayable session JSON and can reopen a saved game after duplicate-property, size and deterministic-replay validation.

## Delivery

`--check` validates installed game resources and performs a real opening action/idempotency/replay diagnostic without opening Tkinter. Source-driven documentation and diagrams and the dedicated real-GUI Xvfb acceptance workflow are tracked in `.github/`. Native Windows, macOS and Linux packaging is automated; final behavioral/native release acceptance and PrideVer publication remain pending.

[Plan](../PLAN.md) · [TODO](../TODO.md) · [Scratchpad](../SCRATCHPAD.md).
