# BoardGamesWithQuests

A configurable desktop board-game application and shared Python engine. Chess
and English draughts are independent game packages using the same engine,
controller and view interfaces.

## Project structure

```text
packages/
  engine/      Shared model, controller, view interfaces and launcher
  chess/       Chess game package
  checkers/    English draughts game package
```

Each game declares board dimensions, starting positions, pieces, clocks and
display settings in its `config.json`. Game-specific rules, quests and
serialization belong to the game package. Installed games are discovered
through Python distribution entry points.

## Installation

Install for development with `python -m pip install -e .`. Run
`python -m engine --check` to inspect registered game packages.

## Documentation

- [Requirements and acceptance criteria](.agents/notes/PRD.md)
- [Reference architecture diagram](.agents/notes/reference_diagram.md)
- [Object-model decisions](.agents/notes/object_model.md)
- [Development automation architecture](.agents/notes/automation_architecture.md)
- [Current progress, integration sequence and release gates](.agents/SCRATCHPAD.md)
