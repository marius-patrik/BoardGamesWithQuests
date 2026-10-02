# ChessWithQuests — Product Requirements Document

**Status:** Draft, awaiting review
**Version:** 0.1
**Supersedes:** nothing
**Governing object model:** `notes/reference_diagram.md` → the live draw.io diagram
**Visual reference:** `GUI_mockup.svg` (Excalidraw export, repo root)

---

## 1. Product vision

A desktop chess application in Python that supports standard chess rules and
also lets a player bend the rules: configure board size, starting position,
piece movement and attack vectors, quests, and clocks before a game starts.

The application is not a chess engine wrapped in a window. The **configuration
surface is the product**. A stock 8×8 game is one configuration among many.

Three audiences shape the priorities:

1. **The grader.** Object-model conformance to the supplied Czech architecture
   diagram is a hard requirement, not a preference. Deviations must be visible
   and justified.
2. **The player.** The GUI has to be usable, and the mockup is the reference for
   what "usable" means here.
3. **The repository.** Governance, CI and the issue/plan/PR trail are part of
   the deliverable, not overhead to be worked around.

---

## 2. Binding constraints

These are **not** negotiable within this project. Any PR that violates one is
rejected regardless of how good the rest of it is.

### 2.1 Libraries

**Standard library plus `tkinter` only. No third-party runtime dependency. No
chess library.**

Consequences that are easy to get wrong:

- FEN, PGN, SAN and all coordinate conversion are **hand-rolled** and must stay
  hand-rolled. `python-chess` is banned.
- `tkinter` is standard library, so the GUI adds no dependency. It is *not*
  available on every Linux Python; it needs `python3-tk` separately on Debian
  and derivatives. Any CI job that imports `tkinter` must install it or assert
  its absence and skip.
- No GUI toolkit other than `tkinter`: no PyQt, PySide, wxPython, Kivy,
  pygame, or webview shells.
- Dev-time tooling (`pytest`, `black`, `properdocs`, `mkdocstrings`) is exempt;
  it lives in `requirements-dev.txt` and never ships.

### 2.2 Object model

The reference diagram is the source of truth. Czech-to-English translation of
identifiers is canonical and is **not** a deviation. Any other structural
deviation requires explicit user approval recorded in `notes/object_model.md`.

### 2.3 Naming

English is canonical for all identifiers that code *calls*. Czech names from
the diagram exist as **aliases**, so the diagram-to-code mapping is discoverable
from both the code and the generated documentation.

- **No diacritics in Czech aliases.** `HerniPlocha`, `Kun`, `Kral`, `Dama`,
  `Strelec`, `Pesak`, `Vez`. The diagram itself uses both spellings, and ASCII
  avoids every encoding failure mode on Windows consoles, CI logs and doc builds.
- Only classes the diagram names in Czech get an alias. Classes the diagram
  already writes in English need no alias, because the code already matches.

### 2.4 Delivery

Every change arrives as a pull request. Nothing lands unreviewed.

---

## 3. Current state

`139` tests pass, `black --check` is clean, `properdocs build --strict` is
clean. The repository is green. Green is misleading: **52 of the 139 tests
(37%) assert nothing about product behaviour** — 27 are bare import checks and
25 check repository metadata such as `AGENTS.md` text and workflow YAML.

What actually exists: a competent chess **model** — board, move, validator,
check/checkmate/stalemate, timer, logger, notation, quest and user types — with
thorough Google-style docstrings and no third-party imports.

What does not exist:

| Gap | Evidence |
|---|---|
| **The entire view layer** | `src/view/__init__.py` is one docstring line. No GUI, no renderer, no entry point. |
| **Most chess rules** | `notes/chess_rules.md:52-111` mandates castling, en passant, promotion, fifty-move, threefold repetition, insufficient material and mutual-agreement draw. Only stalemate is implemented. `King._has_moved` and `Rook._has_moved` are tracked and never read by any rule. |
| **Custom board sizes** | `move.py:44,46` rejects any move outside a hard-coded 8×8. `board.py:41` silently produces an empty board for any other size. Twelve sites in total. |
| **Running application** | No `[project]` table, no build backend, no entry point. The package imports only because pytest sets `pythonpath`. |
| **Integration** | `QuestManager`, `UserManager`, `User`, `MetadataWriter`, `ChessNotationWriter` and `WindowController` are never instantiated or imported by any other module. Built, never connected. |

The last row is the most misleading. The feature count looks high; the wiring
is zero. `GameManager.players` is created and never read, so players are never
linked to users and never consulted by move execution or state evaluation.

---

## 4. Scope

### 4.1 In scope

1. Object-model naming: Czech aliases over English canonical names.
2. The view layer: `GameView`, `PlayerView`, `PlayerGameView` from the diagram.
3. The settings layer: `SettingsView`, `SettingsController` and a settings
   model. **This is a registered Rule 3 deviation** — the mockup requires it and
   the diagram does not contain it. Recorded in `notes/object_model.md`.
4. Removal of 8×8 hard-coding so custom boards genuinely work.
5. The missing chess rules.
6. Wiring the six orphan subsystems into a running game loop.
7. A runnable application entry point and real packaging metadata.
8. Test density: replace metadata and import assertions with behavioural tests.
9. CI: remove the stale DarkFactory dependency, drop bot-authored PR machinery.

### 4.2 Out of scope

- **Matching the mockup pixel-for-pixel.** It is a reference for layout, content
  and data bindings — not a spec to reproduce exactly. Where the mockup and the
  diagram disagree, the diagram wins.
- Network play, persistence beyond the existing file log, and any GUI beyond
  the mockup's described surface.
- Reinstalling the shared DarkFactory pipeline. Explicitly deferred.
- Reproducing the diagram's typos. `GameVeiw`, `check_Pat`, `intger`,
  `akutalizuj_hrace` and `Id_uzivatele: hrac` are recorded as observed, not
  reproduced.

---

## 5. The Czech alias table

English canonical; Czech alias; module. Twelve Czech-named classes plus the
quest type and the two view classes.

| Diagram | Canonical | Czech alias | Module |
|---|---|---|---|
| `Figurka` | `Piece` | `Figurka` | `model.pieces.piece` |
| `Pěšák` | `Pawn` | `Pesak` | `model.pieces.pawn` |
| `Věž` | `Rook` | `Vez` | `model.pieces.rook` |
| `Kůň` | `Horse` | `Kun` | `model.pieces.horse` |
| `Střelec` | `Bishop` | `Strelec` | `model.pieces.bishop` |
| `Dáma` | `Queen` | `Dama` | `model.pieces.queen` |
| `Král` | `King` | `Kral` | `model.pieces.king` |
| `HerníPlocha` | `Board` | `HerniPlocha` | `model.game.board` |
| `Tah` | `Move` | `Tah` | `model.game.move` |
| `Hrac` | `Player` | `Hrac` | `model.game.player` |
| `RevizorTahu` | `MoveValidator` | `RevizorTahu` | `model.game.validator` |
| `Uzivatel` | `User` | `Uzivatel` | `model.users.user` |
| `Kwest` | `Quest` | `Kwest` | `model.game.quest` |
| `HracView` | `PlayerView` | `HracView` | `view` |
| `HracGameView` | `PlayerGameView` | `HracGameView` | `view` |

Three open points in this table, flagged rather than silently decided:

1. **`Rook` would carry three names** — `Vez` (Czech), `Tower` (existing alias,
   absent from the diagram, currently dead code) and `Knight`-style English.
   Proposal: drop `Tower`, since the diagram has no such class.
2. **`Knight` versus `Kun`.** `Knight` is the international English name for the
   piece and is used by an existing test. It is not in the diagram. Proposal:
   keep it as a convenience alias alongside `Kun`.
3. **`Controller = GameController`.** `Controller` is in no diagram box.
   Proposal: delete, and rename the module to `game_manager_controller.py` to
   match the diagram's `GameManagerController` and the sibling
   `window_controller.py`.

### Making aliases visible in the documentation

Module-level aliases render in mkdocstrings as data attributes rather than as
documented API, so "visible in docs" needs explicit handling:

- Each alias is defined immediately after its canonical class with a comment
  naming the diagram box it satisfies.
- `notes/object_model.md` gains the full mapping table above, so the generated
  documentation carries the diagram-to-code correspondence as prose.
- A test asserts the alias table in `notes/object_model.md` matches the aliases
  actually importable from `src/`, so the two cannot drift.

---

## 6. Work streams and PR topology

Stacked where a real dependency exists; independent and mergeable in any order
otherwise.

```
TRACK 1 — Governance                      (independent of all code)
  PR 1   PRD                              ◄── you are here
  PR 2   Governance rules

TRACK 5 — Repository health              (independent of all code)
  PR 9   Remove agent scaffolding
  PR 10  Packaging + entry point
  PR 11  Test-density overhaul

TRACK 2+3+4 — Product code               (one stack)
  PR 3   Custom board sizes          ─┐
  PR 4   Missing chess rules           │  strictly ordered
  PR 5   Wire orphan subsystems       ─┘
             │
             ├──▶ PR 6   View layer          ─┐  parallel
             └──▶ PR 7   Settings layer      ─┘
                        │
                        └──▶ PR 8   Czech aliases  (touches every module; must be last)
```

**Why this shape.** PR 3 is first because custom boards are a prerequisite for
honest chess rules — en passant and castling logic must not be written against a
hard-coded 8×8. PR 6 and PR 7 branch from PR 5 and do not touch each other.
PR 8 is forced last: it adds a symbol to every module in `src/`, so landing it
early guarantees merge conflicts with everything after it.

**Independence.** PRs 1, 2, 9, 10 and 11 touch no product code and can merge at
any time in any order, including while the code stack is still in flight.

---

## 7. Risks

| Risk | Severity | Mitigation |
|---|---|---|
| The code stack is six PRs deep; a late rework invalidates the bottom | High | PR 3 and PR 4 are the risky ones and land first, while the stack is short and cheap to restart |
| Czech aliases in mkdocstrings may not render usefully | Medium | Section 5 specifies the three-part mitigation; validated in the alias PR, which is last and cheapest to revise |
| Rules engine keys off piece-type **strings** (`"king"`, `"pawn"`) and `hasattr` duck-typing, not inheritance | High | Any rename touches these string literals and `hasattr` probes. A missed one fails *silently* — check/checkmate quietly degrade to `False`. The alias PR must include tests that fail if a probe breaks |
| `python3-tk` absent on some runners | Medium | Assert-and-skip in tests; install in CI in the same PR that first imports `tkinter` |
| Removing DarkFactory leaves the repo with no working CI mid-flight | High | PR 3 (CI) merges before any DarkFactory removal. Never leave `main` without green required checks |
| GUI scope creep from the mockup | Medium | Section 4.2 caps it; the mockup is a reference, not a spec |

---

## 8. Acceptance criteria

The project is finished when all of the following hold:

1. `pytest` passes with **no test asserting only repository metadata** replacing
   behavioural coverage; behavioural tests cover every public method.
2. `black --check .` clean at line length 100.
3. `python -m properdocs build --strict` clean, zero warnings.
4. **No third-party runtime import anywhere in `src/`.** Enforced by a test.
5. **No hard-coded 8** outside `Board`'s default dimension. Enforced by a test.
6. Every rule in `notes/chess_rules.md` is implemented and tested, including
   castling, en passant, promotion and all five draw conditions.
7. `python -m chesswithquests` starts a window and a complete game can be played
   to a result.
8. All 15 Czech aliases importable; `notes/object_model.md` mapping table
   matches `src/` exactly.
9. The settings deviation is recorded in `notes/object_model.md` with approval
   context.
10. The GUI implements the mockup's described surface: board with highlights,
    player panels with clocks, captured/lost pieces, turn indicator, move
    history with export, status footer, quest cards, and the settings tab.
11. CI green across Python `3.10`, `3.11`, `3.12`, `3.13`, with no dependency on
    any external repository's workflow.
12. `notes/chess_rules.md` is amended where this PRD deliberately departs from
    it.

---

## 9. Decisions taken, and by whom

Recorded so a reviewer can see what is settled and what is not.

| Decision | Outcome |
|---|---|
| Czech aliases use diacritics | **No diacritics** — ASCII only |
| Which classes get Czech aliases | **Only those the diagram names in Czech** (Section 5) |
| English or Czech as canonical | **English canonical**, Czech as aliases |
| Build the settings layer? | **Yes**, and record the Rule 3 deviation |
| PRD location | **`PRD.md` at repo root** — a PRD is a planning artifact, not documentation, so Rule 2 does not apply |
| Third-party libraries | **None** beyond `tkinter`; no chess library |
| Bot-authored pull requests | **Dropped** |
| Pull request topology | **Stacked where necessary, independent where possible** |
| Mockup fidelity | **Reference, not spec** |

Still open, and wanted before PR 3 starts:

- The three flagged alias questions in Section 5.
- Whether `notes/chess_rules.md` is amended for the custom-board scope, or
  whether every rule it lists must hold on non-standard boards.
