# ChessWithQuests — Product Requirements Document

**Status:** Draft, awaiting review
**Version:** 0.3

Planning material — current state, work streams, risks, acceptance criteria and
the decision log — lives in `SCRATCHPAD.md`. This document states only what the
product is and requires.

---

## 1. What the product is

A desktop chess application in Python, built as an MVC application, in which the
**configuration surface is the product**. A stock 8×8 game with standard pieces
is one configuration among many: before a game starts, a player chooses the
board size, the starting position, the movement and attack vectors of every
piece, which rules are in force, any custom rules they want to add, the quests
in play, and the time controls.

The application is therefore two products sharing one window:

1. **A configurator** that defines a variant of chess.
2. **A player** that plays the resulting game to a result, under the configured
   rules and real clocks.

---

## 2. Users and what they need

| User | Need |
|---|---|
| **The player** | Configure a variant quickly, then play it without friction: see the board, the turn, both clocks, what has been captured, and what is still to do |
| **The grader** | See an object model that conforms to the supplied Czech architecture diagram, with every deviation from it declared and justified |
| **The maintainer** | Behaviour covered by tests that exercise real code paths, not tests that restate the rulebook |

---

## 3. Binding constraints

`AGENTS.md` is normative for object-model conformance, language and delivery.
This section states only the constraints `AGENTS.md` does not already carry, and
a change that violates any of them does not merge as written.

### 3.1 Libraries

**Standard library plus `tkinter` only. No third-party runtime dependency. No
chess library.**

- FEN, PGN, SAN and all coordinate conversion are hand-rolled and stay
  hand-rolled. `python-chess` is not used.
- `tkinter` is the GUI toolkit and the only one. No PyQt, PySide, wxPython,
  Kivy, pygame or webview shell.
- `tkinter` is standard library and adds no dependency, but it is absent from
  some Linux Python distributions unless `python3-tk` is installed separately.
- Development tooling (`pytest`, `black`, `properdocs`, `mkdocstrings`) is exempt
  and never ships.

### 3.2 Tests

Tests exercise **code invariants** and **feature flow**. Tests do not assert on
rules, rule text, workflow YAML, notes content, README content or any other
repository metadata, and a test that would still pass if the product were
deleted does not belong in the suite.

Two whole categories of test are therefore wrong and must not be replaced like
for like:

- **Import smoke tests.** `importlib.import_module(name) is not None` proves a
  module parses. It proves nothing about behaviour and is deleted outright
  rather than kept in a reduced form.
- **Metadata assertions.** Tests that open `AGENTS.md`, workflow YAML, `notes/`
  or `README.md` and assert substrings police the rulebook, not the product.
  Governance is a review convention here, not an enforced gate.

The tests that survive are reworked to drive real behaviour: a move is played
and its effect asserted, a rule is exercised and its outcome asserted, an
invariant such as "no third-party import in `src/`" or "no hard-coded 8 outside
`Board`'s default" is asserted against the code itself.

---

## 4. Functional requirements

### 4.1 Game configuration

| ID | Requirement |
|---|---|
| FR-1 | The player sets board dimensions in rows and columns. |
| FR-2 | The starting position is either standard or edited square by square before play. |
| FR-3 | Each piece type is configurable with movement vectors, attack vectors and a jump flag. A piece may be added to the palette and placed on the board. |
| FR-4 | The rule set for a game is chosen explicitly: which standard rules are in force, and which custom rules are added. |
| FR-5 | A quest is configurable with a name, a description, a completion condition and a reward. |
| FR-6 | Clocks are configured with an initial time and an increment. |
| FR-7 | A configured game can be saved, reset to defaults, or cancelled. |

### 4.2 Rules

| ID | Requirement |
|---|---|
| FR-8 | Rules are **pluggable, not hard-coded into the validator**. A rule is a named unit that inspects game state and reports whether it is satisfied, so adding or removing a rule does not require changing the engine core. |
| FR-9 | Every rule in `notes/chess_rules.md` ships as a rule: castling, en passant, promotion, the fifty-move rule, threefold repetition, insufficient material, stalemate, mutual-agreement draw, and loss on time only where the opponent retains mating material. |
| FR-10 | **A custom rule can be added at runtime**, expressed as a condition over game state with an effect when satisfied. Adding one requires no change to the engine core and no rule enumerating it in advance. |
| FR-11 | **Any rule, standard or custom, can be disabled for a given game.** A disabled rule is not evaluated and cannot end that game. |
| FR-12 | Rules compose: several may be satisfied at once, and the game's result reflects all enabled rules together. |
| FR-13 | Board size is not restricted to 8×8, and FR-9 holds on whatever board the player configured. Rank-relative rules are **generalised, not disabled**: the home rank and the castling and knight-forward files are derived from the configured board, so en passant and castling work at any size rather than being switched off outside 8×8. |
| FR-14 | Clocks run, apply increment, and end the game on expiry. |
| FR-15 | Moves can be selected, previewed as highlights, made and cancelled. |
| FR-16 | Game actions available: new game, draw, resign. |

### 4.3 Game view

| ID | Requirement |
|---|---|
| FR-17 | The board renders with coordinates, the active player's squares highlighted, and legal-move highlights on selection. |
| FR-18 | Each player panel shows identity, ELO, clock, and captured and lost pieces. |
| FR-19 | The turn is indicated, including check. |
| FR-20 | Move history is visible and exportable. |
| FR-21 | Status and alerts appear in a footer. |
| FR-22 | Quests appear as side cards showing progress and reward. |

### 4.4 Settings

| ID | Requirement |
|---|---|
| FR-23 | A settings surface configures board, position, pieces, rules, custom rules, quests and clocks, and its changes apply when a new custom game is created. |
| FR-24 | Settings can be reset to defaults, saved or cancelled. |

### 4.5 Users, notation and persistence

| ID | Requirement |
|---|---|
| FR-25 | A user has a username, display name, email, ELO rating and completed quests. |
| FR-26 | Users can be registered, looked up, and linked to the player they control. |
| FR-27 | The transcript can be exported as FEN, PGN and algebraic notation, with a PGN header roster. |

### 4.6 Application

| ID | Requirement |
|---|---|
| FR-28 | The package is installable and declares its metadata and runtime dependencies, of which there are none beyond the standard library. |
| FR-29 | The application starts from a documented entry point and a complete game can be played to a result. |

---

## 5. Naming requirements

Czech aliases required, English canonical, no diacritics:

| Diagram | Canonical | Czech alias |
|---|---|---|
| `Figurka` | `Piece` | `Figurka` |
| `Pěšák` | `Pawn` | `Pesak` |
| `Věž` | `Rook` | `Vez` |
| `Kůň` | `Knight` | `Kun` |
| `Střelec` | `Bishop` | `Strelec` |
| `Dáma` | `Queen` | `Dama` |
| `Král` | `King` | `Kral` |
| `HerníPlocha` | `Board` | `HerniPlocha` |
| `Tah` | `Move` | `Tah` |
| `Hrac` | `Player` | `Hrac` |
| `RevizorTahu` | `MoveValidator` | `RevizorTahu` |
| `Uzivatel` | `User` | `Uzivatel` |
| `Kwest` | `Quest` | `Kwest` |
| `HracView` | `PlayerView` | `HracView` |
| `HracGameView` | `PlayerGameView` | `HracGameView` |

`Knight` is the canonical name for the L-shaped jumping piece, not `Horse`;
`Kun` is its Czech alias. `Tower` is not a name this project uses and has no
counterpart in the diagram.

---

## 6. Visual reference

`GUI_mockup.svg` is the reference for the game's layout, content and data
bindings. The implementation is not required to reproduce it exactly. Where the
mockup and the reference diagram disagree, the diagram governs.
