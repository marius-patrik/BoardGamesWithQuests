---
status: accepted
---
# Python desktop application architecture

## Application entry and user interface

`src/chesswithquests/` owns process startup. `src/view/` creates Tkinter windows and widgets; `src/controller/` translates user actions into model operations.

## Game model and implementations

`src/model/` owns reusable game state, legal-move validation, rule and quest processing, player profiles and clocks. `src/games/chess/` and `src/games/checkers/` compose variant-specific boards, pieces, rules and exports against the shared model.

## Documentation and automation

`.agents/` contains approved governance sources and generated reader documents. `.github/scripts/`, `.github/tests/` and `.github/workflows/` own source-derived documentation, repository verification and GitHub automation.
