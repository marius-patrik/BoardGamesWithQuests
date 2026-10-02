# ChessWithQuests — Product Requirements Document

**Status:** Draft, awaiting review
**Version:** 0.8

Planning material — current state, work streams, risks, acceptance criteria and
the decision log — lives in `SCRATCHPAD.md`. This document states only what the
product is and requires.

---

## 1. What the product is

A desktop chess application in Python, built as an MVC application, in which the
**configuration surface is the product**. A stock 8×8 game with standard pieces
is one configuration among many: before a game starts, a player chooses the
board size, the starting position, the movement of every piece, which rules are
in force, the quests in play, and the time controls. Every one of these starts at
the standard chess default and changes only where the player changes it.

The application is two products sharing one window:

1. **A configurator** that defines a variant of chess.
2. **A player** that plays the resulting game to a result, under the configured
   rules and real clocks.

## 2. Users and what they need

| User | Need |
|---|---|
| **The player** | Configure a variant quickly, then play it without friction: see the board, the turn, both clocks, what has been captured, and what is still to do |
| **The grader** | See an object model that conforms to the supplied Czech architecture diagram, with every deviation from it declared and justified |
| **The maintainer** | Behaviour covered by tests that exercise real code paths, not tests that restate the rulebook |

## 3. Constraints

Three things are fixed and are not up for debate.

**Already covered by `AGENTS.md`, which is what governs — this document does not
restate them:** object-model conformance (Rule 3), language (Rule 4), delivery
(Rule 7) and the pull-request review trail (Rule 11).

**Not covered by `AGENTS.md`, stated here:** the three below.

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
invariant such as "no third-party import anywhere under the project source" or
"no hard-coded 8 outside `Board`'s default" is asserted against the code itself.

### 3.3 Execution of user-authored code

The application loads and runs Python written by the player, in the rule editor.
This is a deliberate property of the product, not an accident, and it is bounded
on purpose: rules load **only** from the project's `rules/` directory, never from
an arbitrary path, an environment variable or user input elsewhere. The editor
validates a rule before it is allowed to join the vocabulary, so a syntax error
is caught in the editor rather than at game start.

## 4. Functional requirements

### 4.1 Configurable data

Everything in this section is **data**. None of it requires code to express.

| ID | Requirement |
|---|---|
| FR-1 | The player sets board dimensions in rows and columns. |
| FR-2 | The starting position is either standard or edited square by square before play. |
| FR-3 | Each piece type is configurable with movement vectors, attack vectors, a jump flag, a colour and a `kind` label. A piece may be added to the palette and placed on the board. |
| FR-4 | A quest is configurable with a name, a description, a completion condition drawn from a set of data-driven conditions (capture N pieces, move a piece N times, survive N plies, reach a named square), and a reward. |
| FR-5 | Every quest condition carries a **`when`**: `after_move` or `at_game_end`. Conditions that resolve during play and conditions that only resolve once the game ends share one vocabulary and one evaluation path, rather than quest logic being split across two layers. |
| FR-6 | **Quest scope is split explicitly.** The quests configured *for the current game* are held by the quest manager; quests *this user has completed, ever*, are held by the user. The two are distinct and are never conflated — a quest in play is not the same thing as a quest earned. |
| FR-7 | Clocks are configured with an initial time and an increment. |
| FR-8 | A game is played under exactly one rule set, chosen when the game starts. |

### 4.2 Rules — the only code-driven layer

| ID | Requirement |
|---|---|
| FR-9 | **Rules are the only place in the product where logic is written in code.** Board, pieces, quests and clocks are data; rule behaviour is the single extension point. |
| FR-10 | A rule implements four hooks, each with a permissive default: `permits_move(position, move) -> bool` (default `True`), `available_moves(position, piece) -> Iterable[Move]` (default empty), `outcome(position) -> Optional[Result]` (default `None`), and `on_move_made(position, move) -> None` (default no-op). |
| FR-11 | **These hooks are exhaustive for turn-based game logic**, which can only forbid a move or end the game. Anything else is either a special case of one of them or a defect. |
| FR-12 | **No rule owns behaviour.** The validator asks and rules answer: a rule may permit or forbid, never cause; a rule may propose an outcome, never impose one. This is what keeps arbitrary rules from corrupting each other. |
| FR-13 | An outcome is a `Result` carrying a kind (win, loss, draw), a **precedence**, and an optional winner. Decisive outcomes outrank draws; equal precedence resolves by a declared order. Without this, two rules firing at once is ambiguous. |
| FR-14 | A rule's **configured `value` is persisted** in the rule set profile. Its **runtime `state`** — counters, position history — resets each game and is never persisted. Without this split, saving a profile would save a game's history. |
| FR-15 | Every rule in `notes/chess_rules.md` is expressible in those hooks: castling, en passant, promotion, check, checkmate, stalemate, insufficient material, the fifty-move rule, threefold repetition, mutual-agreement draw, and loss on time only where the opponent retains mating material. |
| FR-16 | Logic beyond the orthodox set is expressible without extending the engine: a piece that may move to any square satisfies `available_moves`; a piece that must capture if able satisfies `permits_move`; a game that ends when a named piece is lost satisfies `outcome`. |
| FR-17 | Board size is not restricted to 8×8, and FR-13 holds on whatever board the player configured. Rank-relative rules are **generalised, not disabled**: the home rank and the castling and knight-forward files are derived from the configured board. |
| FR-18 | A **rule set is a multiselect over rule instances** and has no behaviour of its own. |
| FR-19 | `OrthodoxChess` ships as the default rule set, with every standard rule at its orthodox value. |
| FR-20 | The default rule set is selected whenever nothing else is, so an unconfigured game is orthodox chess. It can be neither edited nor deleted — a variant starts by duplicating it. |
| FR-21 | Rule sets are created, renamed, duplicated, edited rule by rule, and deleted. |
| FR-22 | Rule sets persist to `rulesets/*.json`; rules are Python files under `rules/`. Both survive a restart without an account. |

### 4.3 Game view

| ID | Requirement |
|---|---|
| FR-23 | The board renders with coordinates, the active player's squares highlighted, and legal-move highlights on selection. |
| FR-24 | Each player panel shows identity, ELO, clock, and captured and lost pieces. |
| FR-25 | The turn is indicated, including check. |
| FR-26 | Move history is visible and exportable. |
| FR-27 | Status and alerts appear in a footer. |
| FR-28 | Quests appear as side cards showing progress and reward. |

### 4.4 Game start

| ID | Requirement |
|---|---|
| FR-29 | Starting a game presents a modal offering a **rule set selector**, a **Settings** button and a **Start** button. |
| FR-30 | The selector here means *"which rule set to play"*. It is the only place a rule set is chosen for play, and it does not affect which rule set the settings screen is editing. |

### 4.5 Settings surface

| ID | Requirement |
|---|---|
| FR-31 | A selector in the corner chooses **which rule set is being edited**. It appears in settings only, and means *"which profile am I editing"*. |
| FR-32 | Below the selector are sections, one per configurable data layer: **Rules, Board, Pieces, Quests, Clocks**. |
| FR-33 | **All data-based configuration is form-exposed.** No layer requires the code editor to be configured. |
| FR-34 | The Rules section offers a multiselect with a checkbox and a value field per rule — the data parts of a rule are forms, like every other layer. |
| FR-35 | The Rules section offers a **code editor** for authoring new rule logic, which writes a file under `rules/`. |
| FR-36 | The editor validates a rule before it may join the vocabulary, reporting errors in the editor rather than failing at game start. |
| FR-37 | Settings can be saved, reset to the shipped defaults, or cancelled. |

### 4.6 Users, notation and persistence

| ID | Requirement |
|---|---|
| FR-38 | A user has a username, display name, email, ELO rating and completed quests. |
| FR-39 | Users can be registered, looked up, and linked to the player they control. |
| FR-40 | The transcript can be exported as FEN, PGN and algebraic notation, with a PGN header roster. |
| FR-41 | The game log directory is **configurable**. It defaults to `logs/` at the repository root, is created on demand, and is git-ignored. A configured directory is honoured rather than silently redirected. |

### 4.7 Application

| ID | Requirement |
|---|---|
| FR-42 | The package is installable and declares its metadata and runtime dependencies, of which there are none beyond the standard library. |
| FR-43 | The application starts from a documented entry point and a complete game can be played to a result. |

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

## 6. Repository layout

The package sits at the repository root. There is no `src/` directory.

```
model/  controller/  view/    the engine
rules/                         rule logic, one Rule subclass per file
rulesets/                      rule set profiles, JSON
tests/  notes/  theme/         tests, design notes, documentation theme
```

**Engine and rule content are separated.** `model/`, `controller/` and `view/`
hold the engine; `rules/` and `rulesets/` hold the content the player authors.
Keeping them apart means player-authored files stay out of the source package,
and a reviewer can read every rule and profile the project ships or has been
given without reading the engine.

Rules are code and rule sets are data, so they are kept in directories named for
what they are rather than mixed into either.
