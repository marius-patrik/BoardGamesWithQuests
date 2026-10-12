# BoardGamesWithQuests

A Python board-game engine in active development. Chess and English draughts
are separate game packages sharing an engine, controller and view architecture.

**Current status:** The installable package workspace and declarative game
configurations exist. Neither game's full rules/quests nor the real Tkinter GUI
have been integrated yet. The former placeholder GUI was deliberately removed.
The existing test suite was retired for a from-scratch rewrite after the
development stack is integrated (issue #239). A green compilation/docs pipeline
is not evidence of working gameplay.

```text
packages/
  engine/      Shared engine, controller, GUI contracts and launcher
  chess/       Chess package with root config.json
  checkers/    English draughts package with root config.json
```

Game metadata, boards, piece definitions and movement data, clocks, formats and
appearance are declared in each game's `config.json`. **Rules and quests** are
Python behavior extensions that will be integrated in later pull requests.
Installed games are discovered through Python distribution entry points.

Install for development with `python -m pip install -e .`. Run
`python -m engine --check` to inspect available game packages without starting
a window. The `chesswithquests` console entry point is reserved for the
complete application; it does not pretend the GUI exists while it is unfinished.

## Architecture and documentation

- [Original two-page reference diagram and source](notes/reference_diagram.md)
- [Actual codebase model — generated from tracked Python classes](notes/object_model.md)
- [Requirements and acceptance criteria](PRD.md)
- [Implementation sequencing](SCRATCHPAD.md)
