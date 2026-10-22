---
status: published
---
# BoardGamesWithQuests

BoardGamesWithQuests is a local Python/Tkinter board-game application with chess and English-draughts game definitions, a generic JSON-driven game engine, and an interactive two-player board, history, clocks, quests and game selection. The built-in game definitions are trusted versioned JSON assets and currently remain marked `playable: false` pending full reference-game acceptance.

## Application

The `boardgameswithquests` entry point builds the Tkinter window and game chooser. Board clicks flow through `GameController` and a local `DesktopSession` to the canonical revisioned `GameManager`; only detached snapshots and render-only boards reach the widgets. The same game engine owns legal moves, captures, declarative rule/effect evaluation, revisioned actions, clock accounting, quest progress, prioritized outcomes and deterministic replay. Chess and English-draughts use the same engine and declared movement capabilities.

## Player data

Bundled rules and quests cannot be edited through settings. The settings dialog accepts only board square size and coordinate display, and saves validated preferences atomically in the operating system's application-data directory. The interface can export the authoritative game snapshot as replayable JSON.

## Verification and delivery

Source-driven requirements and architecture are published from `.agents/requests/` and `.agents/decisions/`. A dedicated GitHub Actions matrix exercises actual local-session gameplay on Python 3.10–3.13 and Tkinter clicks under Xvfb. The full inherited CI and four real native executable distributions still require acceptance before the disabled release publication may be enabled.

The [Plan](../PLAN.md) and [TODO](../TODO.md) track the remaining functional and release criteria; [Scratchpad](../SCRATCHPAD.md) records investigation evidence.
