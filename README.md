# BoardGamesWithQuests

<<<<<<< HEAD
<<<<<<< HEAD
A JSON-driven two-player board-game platform for orthodox chess, English
draughts and international draughts. One game-neutral Python engine interprets
bounded JSON boards, piece capabilities, rules, quests, clocks and outcomes.
The delivery architecture places authoritative FastAPI play on Vercel Python
Functions, with Supabase authentication, database and Realtime. One
React/Rsbuild web app supplies the browser and remote Tauri 2 desktop UI.
||||||| b45d2e0f
School project of a chess game with customizable pieces, board, and quests.
Forked from class project base.
=======
A desktop board game engine and application in Python, built as an MVC
application, in which **the configuration is the product**. Chess and English
draughts ship as two directories under `src/games/` and share one engine.
>>>>>>> fix/independent-review-findings
||||||| 07086322
School project of a chess game with customizable pieces, board, and quests.
Forked from class project base.
=======
A desktop board game engine and application in Python, built as an MVC
application, in which **the configuration is the product**. Chess and English
draughts ship as two directories under `src/games/` and share one engine.
>>>>>>> tmp155

<<<<<<< HEAD
<<<<<<< HEAD
Three shipped configurations are intentionally non-playable until complete
legal-rule integration passes the behavior suite. The public website and
read-only API catalog do not offer simulated gameplay.
||||||| b45d2e0f
## Project Overview
ChessWithQuests is an extensible modular chess engine and desktop application built in Python following the Model-View-Controller (MVC) architectural pattern. It supports standard chess rules as well as custom board configurations, customizable pieces with configurable movement and attack vectors, and an in-game quest system.
=======
**Status: playable, incomplete.** Chess is playable from the entry point through
a tkinter window, and the settings surface is delivered. The export writers are
prototypes. `PRD.md` states what the product must be and `SCRATCHPAD.md` records
what is built, what is partial, and what is owed — one entry per planned pull
request.
>>>>>>> fix/independent-review-findings
||||||| 07086322
## Project Overview
ChessWithQuests is an extensible modular chess engine and desktop application built in Python following the Model-View-Controller (MVC) architectural pattern. It supports standard chess rules as well as custom board configurations, customizable pieces with configurable movement and attack vectors, and an in-game quest system.
=======
**Status: playable, incomplete.** Chess is playable from the entry point through
a tkinter window, and the settings surface is delivered. The export writers are
prototypes. `PRD.md` states what the product must be and `SCRATCHPAD.md` records
what is built, what is partial, and what is owed — one entry per planned pull
request.
>>>>>>> tmp155

<<<<<<< HEAD
<<<<<<< HEAD
## Source layout

- `packages/engine/` — generic geometry, conditions, effect planning and game state.
- `packages/chess/` — orthodox chess JSON definition and game-owned exports.
- `packages/english_draughts/` — 8×8 draughts JSON definition.
- `packages/international_checkers/` — 10×10 international draughts JSON definition.
- `packages/server/` — FastAPI ASGI boundary; `api/index.py` is the entry point.
- `packages/web/` — React/TypeScript/Rsbuild/Bun browser interface.
- `packages/desktop/` — Tauri remote-WebView wrapper.
- `supabase/migrations/` — reproducible private persistence and access migrations.
- `tests/` — behavioral definition, interpreter, capture, session and read-only HTTP tests.

## Interfaces

The public health and game-catalog API is hosted at
`https://boardgameswithquests-api.vercel.app`.
The browser application is hosted at
`https://boardgameswithquests-web.vercel.app`.

Gameplay and authentication require the remaining G2–G7 implementation;
all public catalog entries expose `playable=false`.

## Contract and contribution rules

- [Product requirements](.agents/notes/PRD.md)
- [Architecture decisions](.agents/notes/object_model.md)
- [JSON rule contract](.agents/notes/json_contract.md)
- [Delivery plan](.agents/notes/PLAN.md)
- [Engineering and behavior test requirements](.agents/AGENTS.md)
- [Reference diagram](.agents/notes/reference_diagram.md)

The game reference diagrams are supplied design inputs; source-derived
diagrams are generated independently. GPL-3.0-only governs the source.

## Behavioral verification

Install the Python package and development requirements, then run `pytest`.
The suite exercises validated JSON, immutable effect contracts, ordered-hop
intents, actor/turn/revision rejection, atomic domain rollback, exact retries,
clock transitions, participant-scoped quests and deterministic session replay.
Closed move/resign/claim_draw/timeout submissions share one domain boundary;
configured position identity and opening side survive replay. Agreed draw
handshakes and SQL terminal-envelope validation remain actionable dependencies.
Synthetic declarative scenarios exercise these contracts without claiming
complete shipped-game legality. HTTP tests cover health and the read-only
catalog; they do not certify multiplayer.

The executable `scripts/probe_g1_semantics.py` and
`scripts/probe_json_contract.py` supplement the permanent suite with primitive
expressiveness checks. Real Supabase transactions and authorization, public
multiplayer HTTP requests, two-browser gameplay, Realtime recovery, Tauri and
classroom shared-IP capacity each require their own integration gate. A passing
local suite does not certify those external requirements or a complete game.

The private SQL commit boundary accepts exact nine-field move events and exact
ten-field terminal events (`resign`, `claim_draw`, `timeout`) in version-1
snapshots. Terminal commits preserve position and rule/quest state, charge only
the running clock without increment, and atomically append one configured
result. Rule legality and outcome arbitration remain engine responsibilities.
Run the mandatory PostgreSQL suites with the integrated terminal engine:

```sh
PYTHONPATH=packages python -m pytest -q tests/test_private_transactions.py tests/test_private_transactions_adversarial.py tests/test_terminal_transactions.py
```

These tests require Docker access and fail explicitly when PostgreSQL cannot
start. They verify local private transactions, not hosted multiplayer acceptance.

## Source documentation

Install Graphviz and the Python package with its development requirements:

```sh
python -m pip install -e . -r requirements-dev.txt
mkdocs build --strict
```

MkDocs, Material and mkdocstrings generate every documentation page, homepage
and navigation entry from tracked Python package source and Google-style
docstrings. `python .github/scripts/build_docs.py` provides the same strict
build through an ephemeral source directory. No static documentation pages,
manual indices or documentation source directories are committed. Authoritative
specifications remain in `.agents/notes/` and are linked to the checked-out Git
revision rather than copied into the site. Architecture diagrams are generated
from source, and supplied reference figures remain available as required assets.

CI requires behavioral tests on Python 3.10–3.13, formatting, Rust quality
checks, web quality checks, production web compilation and strict documentation.
The aggregate quality gate rejects missing discovery, unsupported mandatory
commands and absent, skipped or failed execution evidence. GitHub Actions
deploys the documentation from reviewed `main` through the Pages workflow.
||||||| b45d2e0f
## Documentation & Architecture
- **Online Documentation**: [ChessWithQuests Documentation](https://marius-patrik.github.io/ChessWithQuests/) (autogenerated dynamically from source docstrings via MkDocs)
- **Reference Architecture Diagram**: [Draw.io Architecture Diagram](https://app.diagrams.net/#G19OY7iySOQWRAZDFKy1r-7tJKG_L-_Qn8#%7B%22pageId%22%3A%22C5RBs43oDa-KdzZeNtuy%22%7D) (details the Model-View-Controller architecture and class hierarchy)
=======
## What works today

Every item below is exercised by a test in `tests/`.

| Capability | Where it lives |
|---|---|
| A board of any dimensions, with bounds checking, moving, capture recording and piece replacement | `src/model/game/board.py` |
| Moves carrying a start square, a target square, a move type and an optional promotion piece, validated and executed atomically | `src/model/game/move.py` |
| Legal move generation per piece and per side, refusing any move that leaves the mover's own piece attacked | `src/model/game/validator.py` |
| Thirteen orthodox chess rules as `Rule` subclasses — castling, en passant, promotion, check, checkmate, stalemate, insufficient material, the fifty-move rule, threefold repetition, mutual agreement, flag fall, bishop colour confinement, and which piece kind is royal | `src/games/chess/rules/` |
| A rule layer of five hooks — `permits_move`, `available_moves`, `outcome`, `on_move_made`, `status` — with an outcome type carrying a kind, a precedence and a winner | `src/model/game/rule.py` |
| A configuration loaded from a directory as a package in its own right, so a copy composes its own board, pieces, rules, clocks and quests | `src/model/game/configuration.py` |
| A full game loop from `new_game()` to a result, driving the quest manager, the user manager, the clocks, the transcript and the logger | `src/model/game/manager.py` |
| Twenty built-in quest classes, twelve judged a move at a time and eight judging the finished game | `src/model/game/quests.py` |
| English draughts: twelve pieces a side, flying kings, mandatory capture including chains, crowning without removal, a win by immobilisation or by losing every piece — held to the published perft counts | `src/games/checkers/` |
| A capture chain as one move, carried by `HopMove(Move)` rather than by the engine's own `Move` | `src/games/checkers/moves.py` |
| A tkinter window: a start modal with a configuration selector, Settings and Start; the board drawn from White's side with coordinates, symbols, selection and legal-move highlights; player panels with clocks and captured pieces; the turn; a notated move history; a status footer; quest cards with progress | `src/view/` |
| A settings surface: a corner selector for which configuration is being edited, sections for Board, Pieces, Rules, Quests and Clocks built from declared fields, create/rename/duplicate/delete, and a code editor for rule and quest source | `src/view/settings_dialog.py`, `src/view/code_editor.py`, `src/model/game/field.py` |
| Configuration copy, rename and delete, all of which refuse the default configuration | `src/model/game/configuration.py` |
| Fifteen Czech aliases, each the same object as its canonical English class | throughout; `PRD.md` section 5 lists them |
| An installable package with a `python -m chesswithquests` entry point | `pyproject.toml`, `src/chesswithquests/` |

## What is partial

- **Export is the largest hole.** `ChessNotationWriter` still switches on a
  format-name string instead of there being one writer class per format. FEN
  writes `- - 0 1` for castling rights, the en passant square, the halfmove clock
  and the fullmove number. PGN movetext is destination squares rather than SAN,
  and its header falls back to placeholder strings. The stenographic writer emits
  coordinate pairs with no compression. No configuration ships a per-format
  writer, and `src/games/checkers/` ships no writer at all.
- **`pyproject.toml` does not ship `src/games/checkers`.** The package list names
  `games.chess` and its subpackages and omits the second configuration, so a clean
  install finds chess and not draughts.
- **`src/controller/controller.py` is not renamed** to `game_manager_controller.py` to
  match the diagram's `GameManagerController`.

## Not built yet

- No FEN import, so nothing round-trips a position.
- No keyboard-navigation guarantee for the view layer.
- No network play, and no persistence of a game in progress. Neither is in the
  reference diagram.

## Documentation and architecture

- **Generated documentation**: [ChessWithQuests Documentation](https://marius-patrik.github.io/ChessWithQuests/)
  — every page is emitted from the source docstrings at build time by
  `properdocs` with `mkdocstrings`; this file is its overview page. Nothing about
  the documentation is stored: `docs_dir` points at a generated, git-ignored
  directory and `.github/scripts/docs_hooks.py` builds the whole navigation from
  the source tree.
- **Reference architecture diagram**:
  [Draw.io diagram](https://app.diagrams.net/#G19OY7iySOQWRAZDFKy1r-7tJKG_L-_Qn8#%7B%22pageId%22%3A%22C5RBs43oDa-KdzZeNtuy%22%7D)
  — the class hierarchy and the Model-View-Controller split the object model
  follows. Every deviation from it is registered in `notes/object_model.md`.
- **Product requirements**: `PRD.md`.
- **Implementation state and remaining work**: `SCRATCHPAD.md`.
- **Notes**: `notes/chess_rules.md`, `notes/object_model.md`,
  `notes/reference_diagram.md`.

## Development

Python 3.10 or newer. The runtime uses the standard library and `tkinter`, and
nothing else; `python-chess` is banned and FEN, PGN, SAN and coordinate
conversion are hand-rolled. The tools below are development dependencies and
never ship:

```
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
```

Everything runs from the repository root — `pyproject.toml` configures `pytest`
with `pythonpath = ["."]`, and the package is also installable with `pip install .`:

```
python -m pytest -q
python -m black --check .
python -m properdocs build --strict
```

`tkinter` needs a display. Tests stay within `tkinter.Tcl()` and `ttk.Style()`,
which work without one, or run under `xvfb-run`.
>>>>>>> fix/independent-review-findings
||||||| 07086322
## Documentation & Architecture
- **Online Documentation**: [ChessWithQuests Documentation](https://marius-patrik.github.io/ChessWithQuests/) (autogenerated dynamically from source docstrings via MkDocs)
- **Reference Architecture Diagram**: [Draw.io Architecture Diagram](https://app.diagrams.net/#G19OY7iySOQWRAZDFKy1r-7tJKG_L-_Qn8#%7B%22pageId%22%3A%22C5RBs43oDa-KdzZeNtuy%22%7D) (details the Model-View-Controller architecture and class hierarchy)
=======
## What works today

Every item below is exercised by a test in `tests/`.

| Capability | Where it lives |
|---|---|
| A board of any dimensions, with bounds checking, moving, capture recording and piece replacement | `src/model/game/board.py` |
| Moves carrying a start square, a target square, a move type and an optional promotion piece, validated and executed atomically | `src/model/game/move.py` |
| Legal move generation per piece and per side, refusing any move that leaves the mover's own piece attacked | `src/model/game/validator.py` |
| Thirteen orthodox chess rules as `Rule` subclasses — castling, en passant, promotion, check, checkmate, stalemate, insufficient material, the fifty-move rule, threefold repetition, mutual agreement, flag fall, bishop colour confinement, and which piece kind is royal | `src/games/chess/rules/` |
| A rule layer of five hooks — `permits_move`, `available_moves`, `outcome`, `on_move_made`, `status` — with an outcome type carrying a kind, a precedence and a winner | `src/model/game/rule.py` |
| A configuration loaded from a directory as a package in its own right, so a copy composes its own board, pieces, rules, clocks and quests | `src/model/game/configuration.py` |
| A full game loop from `new_game()` to a result, driving the quest manager, the user manager, the clocks, the transcript and the logger | `src/model/game/manager.py` |
| Twenty built-in quest classes, twelve judged a move at a time and eight judging the finished game | `src/model/game/quests.py` |
| English draughts: twelve pieces a side, flying kings, mandatory capture including chains, crowning without removal, a win by immobilisation or by losing every piece — held to the published perft counts | `src/games/checkers/` |
| A capture chain as one move, carried by `HopMove(Move)` rather than by the engine's own `Move` | `src/games/checkers/moves.py` |
| A tkinter window: a start modal with a configuration selector, Settings and Start; the board drawn from White's side with coordinates, symbols, selection and legal-move highlights; player panels with clocks and captured pieces; the turn; a notated move history; a status footer; quest cards with progress | `src/view/` |
| A settings surface: a corner selector for which configuration is being edited, sections for Board, Pieces, Rules, Quests and Clocks built from declared fields, create/rename/duplicate/delete, and a code editor for rule and quest source | `src/view/settings_dialog.py`, `src/view/code_editor.py`, `src/model/game/field.py` |
| Configuration copy, rename and delete, all of which refuse the default configuration | `src/model/game/configuration.py` |
| Fifteen Czech aliases, each the same object as its canonical English class | throughout; `PRD.md` section 5 lists them |
| An installable package with a `python -m chesswithquests` entry point | `pyproject.toml`, `src/chesswithquests/` |

## What is partial

- **Export is the largest hole.** `ChessNotationWriter` still switches on a
  format-name string instead of there being one writer class per format. FEN
  writes `- - 0 1` for castling rights, the en passant square, the halfmove clock
  and the fullmove number. PGN movetext is destination squares rather than SAN,
  and its header falls back to placeholder strings. The stenographic writer emits
  coordinate pairs with no compression. No configuration ships a per-format
  writer, and `src/games/checkers/` ships no writer at all.
- **`pyproject.toml` does not ship `src/games/checkers`.** The package list names
  `games.chess` and its subpackages and omits the second configuration, so a clean
  install finds chess and not draughts.
- **`src/controller/controller.py` is not renamed** to `game_manager_controller.py` to
  match the diagram's `GameManagerController`.

## Not built yet

- No FEN import, so nothing round-trips a position.
- No keyboard-navigation guarantee for the view layer.
- No network play, and no persistence of a game in progress. Neither is in the
  reference diagram.

## Documentation and architecture

- **Generated documentation**: [ChessWithQuests Documentation](https://marius-patrik.github.io/ChessWithQuests/)
  — every page is emitted from the source docstrings at build time by
  `properdocs` with `mkdocstrings`; this file is its overview page. Nothing about
  the documentation is stored: `docs_dir` points at a generated, git-ignored
  directory and `.github/scripts/docs_hooks.py` builds the whole navigation from
  the source tree.
- **Reference architecture diagram**:
  [Draw.io diagram](https://app.diagrams.net/#G19OY7iySOQWRAZDFKy1r-7tJKG_L-_Qn8#%7B%22pageId%22%3A%22C5RBs43oDa-KdzZeNtuy%22%7D)
  — the class hierarchy and the Model-View-Controller split the object model
  follows. Every deviation from it is registered in `notes/object_model.md`.
- **Product requirements**: `PRD.md`.
- **Implementation state and remaining work**: `SCRATCHPAD.md`.
- **Notes**: `notes/chess_rules.md`, `notes/object_model.md`,
  `notes/reference_diagram.md`.

## Development

Python 3.10 or newer. The runtime uses the standard library and `tkinter`, and
nothing else; `python-chess` is banned and FEN, PGN, SAN and coordinate
conversion are hand-rolled. The tools below are development dependencies and
never ship:

```
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
```

Everything runs from the repository root — `pyproject.toml` configures `pytest`
with `pythonpath = ["."]`, and the package is also installable with `pip install .`:

```
python -m pytest -q
python -m black --check .
python -m properdocs build --strict
```

`tkinter` needs a display. Tests stay within `tkinter.Tcl()` and `ttk.Style()`,
which work without one, or run under `xvfb-run`.
>>>>>>> tmp155
