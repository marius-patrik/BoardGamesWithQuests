# SCRATCHPAD

Working notes for ChessWithQuests. This is the plan: current state, work
streams, risks, acceptance criteria and the decision log. The product
requirements themselves live in `PRD.md`.

Not documentation — a planning artifact, same as the PRD.

---

## 1. Current state

`139` tests pass. `black --check` clean. `properdocs build --strict` clean. The
repository is green, and green is misleading.

What exists is a competent chess **model** — board, move, validator,
check/checkmate/stalemate, timer, logger, notation, quest and user types — with
thorough Google-style docstrings and no third-party imports.

### 1.1 Gaps

| Gap | Evidence |
|---|---|
| **The entire view layer** | `src/view/__init__.py` is one docstring line. No GUI, no renderer, no entry point. Tracked in #125 |
| **Rule set is not configuration data** | `RevizorTahu` inlines each rule and `get_state` hard-codes the outcome ladder. There is nowhere to store "which rules are in force", so FR-8 to FR-12 are unmet. Not a redesign — the diagram already provides the fields (`Tah.typ tahu`, `Figurka.vektory`, `GameManager.get_stav`) |
| **Most chess rules absent** | `notes/chess_rules.md:52-111` mandates castling, en passant, promotion, fifty-move, threefold repetition, insufficient material and mutual-agreement draw. Only stalemate is implemented. `King._has_moved` and `Rook._has_moved` are tracked and never read by any rule |
| **Custom board sizes broken** | `move.py:44,46` rejects any move outside a hard-coded 8×8. `board.py:41` silently produces an empty board for any other size. Twelve sites in total |
| **Running application** | No `[project]` table, no build backend, no entry point. The package imports only because pytest sets `pythonpath` |
| **Integration** | `QuestManager`, `UserManager`, `User`, `MetadataWriter`, `ChessNotationWriter` and `WindowController` are never instantiated or imported by any other module |

### 1.2 Why the integration gap matters most

The feature count looks high and the wiring is zero. `GameManager.players` is
created at `manager.py:48` and never read, so players are never linked to users
and never consulted by move execution or state evaluation. Six subsystems were
built as standalone units and never connected to a game.

### 1.3 Correctness defects

| Defect | Location |
|---|---|
| `move.validate()` called without its `board` argument, so its occupancy and friendly-target checks are dead code | `validator.py:282` against `move.py:50-56` |
| Rules engine keyed off piece-type **strings** (`"king"`, `"pawn"`) and `hasattr` duck-typing rather than inheritance. A missed rename degrades check/checkmate to `False` **silently** | `validator.py:64,92,101,159,166,167,187`, `board.py:106` |
| Unknown piece type silently serialised as a pawn | `export_writers.py:89` |
| PGN emits destination-square notation (`e4`) labelled as PGN, not SAN | `export_writers.py:120,126` |
| FEN hard-codes castling rights, en-passant square, halfmove and fullmove | `export_writers.py:101` |
| `get_state` returns a check state that no consumer reads | `manager.py:96`, `window_controller.py:74-79` |
| `ExportWriter.export` returns `""` on an unrecognised format instead of raising | `export_writers.py:155` |
| The only `pass` in `src/` is `GameManager.save_log` | `manager.py:78-80` |
| Leftover demo block in library code | `piece.py:94-97` |

The rules engine being string-coupled dominates the rename risk: any rename
touches string literals and `hasattr` probes, and a missed probe returns
`False` rather than raising. Every naming change must ship tests that fail when
a probe breaks, not only when a name changes.

### 1.4 Dead code to remove

**Never referenced outside their definition:**

`GameManager.start_turn` `manager.py:55` · `GameManager.cancel_move:74` ·
`GameManager.save_log:78` · `MoveValidator.set_board:32` ·
`GameLogger.file_path:58` · `Board.setup_default_board:119` ·
`Timer.add_time:51` · `ChessNotationWriter.export:138` ·
`ExportWriter.export:20` · `Quest.complete:48` ·
`MoveValidator.is_square_attacked:68`

**Aliases with zero references:** `Tower` `tower.py:11` · `Controller`
`controller.py:97` · `Horse`/`Knight` `horse.py:42` ·
`Timer.countdown` `timer.py:49` · `Player.get_color:58` · `Player.get_user:59` ·
`Player.get_elo_rating:57` · `GameManager.possible_moves:72` ·
`UserManager.find_user:50`

`Tower`, `Horse` and `Controller` are removed by PR 8 as part of the rename. The
rest are removed by PR 12.

**Written but never read:** `Board.captured_white:38` ·
`Move.captured_piece:32` · `Move.promotion_piece:33` · `GameManager.players:48` ·
`Board.dimensions:33` · `GameManager.STATE_CHECK:25` ·
`WindowController.title/width/height:28` · `ExportWriter.field:18` ·
`Player.user` / `Player.setUser`

Several of these become live once PR 5 wires the subsystems and PR 17 provides
the view. PR 12 re-checks each one and removes only what is still dead — a
write-only attribute may have been written in anticipation of a consumer that
now exists.

### 1.5 Docstring gaps

Two concrete violations of the Google-style requirement:

| Location | Gap |
|---|---|
| `src/model/misc/export_writers.py:20-29` | `ExportWriter.export` returns `str` but its docstring has no `Returns:` section |
| `src/model/game/logger.py:58-60` | `GameLogger.file_path` returns `Optional[str]` but has no `Returns:` section |

Otherwise coverage is complete: 32/32 module docstrings, 23/23 class docstrings,
111/111 method docstrings, and `Args:` present for every non-self parameter.

---

## 2. Test suite restructuring

Current: `139` tests. Target: behaviour-only.

### 2.1 Delete outright

| File | Tests | Why |
|---|---|---|
| `tests/test_structure.py` | 27 | `importlib.import_module(...) is not None`. Proves a module parses, nothing more |
| `tests/test_workflow_rules.py` | 15 | Asserts `AGENTS.md` text, workflow YAML and pipeline pins. Zero product code |
| `tests/test_claude_symlink.py` | 3 | Asserts a symlink target and `.agents/` file existence |
| `tests/test_readme.py` | 1 | Asserts `README.md` contains three URLs |
| `tests/test_chess_rules_notes.py` | 1 | Asserts keywords in `notes/chess_rules.md` |
| `tests/test_object_model_notes.py` | 1 | Asserts a URL and phrases in `notes/object_model.md` |
| `tests/test_reference_diagram_notes.py` | 1 | Asserts a diagram id in `notes/reference_diagram.md` |
| `tests/test_upstream_base_notes.py` | 1 | Asserts a commit SHA in `notes/upstream_base.md` |
| `tests/test_docs_and_docstrings.py` | 11 of 12 | Metadata and workflow-pin tests go; the docstring-presence and strict-build checks stay |

**52 of 139 tests assert nothing about the product.** Deleted, not reduced.

`tests/test_object_model_notes.py` is deleted even though `notes/object_model.md`
is now carrying deviation records — the requirement is that the deviations are
recorded and approved, not that a test greps for a URL.

### 2.2 Rework

The surviving ~87 tests keep their product coverage and gain:

- **Feature-flow tests.** A whole game driven end to end — configure, play,
  reach a result. No test currently exercises `GameManager.make_move` in a
  sequence, which is why six orphan subsystems went unnoticed.
- **Rule tests.** One per rule, each exercised both enabled and disabled, so
  FR-11 is genuinely covered rather than asserted.
- **Rule-configuration tests.** Each rule driven both on and off through the
  same game, proving the setting — not a code path — is what changes it. Covers
  FR-8 and FR-11.
- **Quest tests.** A quest built from each data-driven condition completes on the
  intended event and not before, awards its reward once, and survives being
  checked again after completion.
- **Invariant tests**, asserted against code rather than docs:
  - no third-party runtime import anywhere in `src/`
  - no hard-coded `8` outside `Board`'s default dimension
  - every public method in `src/` reachable from at least one test
  - every Czech alias in PRD §5 importable and identical to its canonical object
  - `black --check` and `properdocs build --strict` clean

### 2.3 Coverage known to be missing today

`GameManager.start_turn`, `cancel_move`, `save_log`, `STATE_CHECK`,
`MoveValidator.set_board`, `is_square_attacked`, `GameLogger.file_path`,
`Board.captured_white`, `Move.captured_piece`, `ChessNotationWriter.export`,
`ExportWriter.export`, `Timer.add_time`, `Board.setup_default_board`, and any
`Board` constructed with non-8×8 dimensions.

---

## 3. Work streams and PR topology

Stacked where a real dependency exists; independent and mergeable in any order
otherwise.

```
TRACK 1 - Governance                      (independent of all code)
  PR 1   PRD + SCRATCHPAD                 ◄── in review
  PR 2   Governance rules

TRACK 5 - Repository health
  PR 9   Remove agent scaffolding                    (independent)
  PR 10  Packaging + entry point                     (independent)
  PR 11  Test-suite restructuring                    (deletions standalone;
                                                    additions follow the stack)
  PR 12  Code hygiene: dead code, docstring gaps     (follows PR 8 - see below)

TRACK 2+3+4 - Product code                (one stack)
  PR 3   Generalise the board beyond 8x8        ─┐
  PR 4   Rule set as data + standard rules    │ ordered
  PR 5   Wire the orphan subsystems             ─┘
              │
              ├──▶ PR 6   View layer            ─┐ parallel
              └──▶ PR 7   Settings layer        ─┘
                        │
                        └──▶ PR 8   Czech aliases
                                     │
                                     └──▶ PR 12  Code hygiene
```

**Why this shape.**

PR 3 is first because custom boards are a prerequisite for honest rules.
En passant and castling logic must not be written against a hard-coded 8×8, and
FR-13 needs the home rank and castling files derived before any rule depends on
them.

PR 4 introduces the rule set as configuration data, then implements the standard
rules on top of it. Building them straight into the hard-coded validator would
mean rebuilding them the moment FR-8 to FR-11 land, so the data model lands
first. This is a smaller job than a plugin system: no registry, no callbacks,
no new classes — the diagram's existing fields carry it.

PR 6 and PR 7 do not touch each other and branch from PR 5. Both consume
subsystems that are orphans until PR 5 wires them, so neither can merge before it.

PR 8 is forced last — it adds a symbol to every module in `src/`, so landing it
early guarantees conflicts with everything after it.

PR 12 follows PR 8 rather than running in parallel, because it removes the same
aliases PR 8 touches. The deletions in §2.1 can merge immediately and stand
alone; only the added test coverage depends on the code existing.

**Do not remove DarkFactory before the replacement CI is green on `main`.** The
repository must never sit without working required checks.

---

## 4. Risks

| Risk | Severity | Mitigation |
|---|---|---|
| `hasattr` and string probes in the rules engine break **silently** on rename | High | §1.3. Naming PRs ship tests that fail when a probe breaks, not only when a name changes |
| The rule set must become data without disturbing the diagram's four `RevizorTahu` operations | Medium | PR 4. Those operations stay exactly as drawn; only the outcome ladder in `get_stav` and move generation in `simulate_Move` gain a data-driven path. Assessed in `notes/object_model.md` section 4 as **not** a deviation |
| The code stack is eight PRs deep; a late rework invalidates the bottom | High | PR 3 and PR 4 are the risky ones and land first, while the stack is short and cheap to restart |
| Removing DarkFactory leaves the repo without CI mid-flight | High | Replacement CI merges and goes green before any removal |
| Generalising rank-relative rules to arbitrary board sizes is harder than it looks — home rank, knight-forward file and castling rook files all derived | High | Land in PR 3, before PR 4, so rule work builds on a correct board abstraction |
| Deleting 52 tests could mask real regressions | Medium | Every deletion is import-only or metadata-only. §2.2 adds behavioural coverage to offset, and PR 11's deletions can merge early and be observed |
| Czech aliases in mkdocstrings may render as data rather than documented API | Medium | Accepted per decision 7. No special handling |
| `python3-tk` absent on some runners | Medium | Assert-and-skip in tests; install in CI in the PR that first imports `tkinter` |
| GUI scope creep from the mockup | Medium | PRD §6 caps it; the mockup is a reference, the diagram governs |
| A per-game rule set multiplies the state space tests must cover | Medium | §2.2 requires each rule tested enabled and disabled, plus composition, rather than a combinatorial sweep |

---

## 5. Definition of done

The project is finished when all of these hold:

1. `pytest` green, and **no surviving test asserts only on repository
   metadata**.
2. Every public method in `src/` is reachable from at least one test.
3. `black --check .` clean at line length 100.
4. `python -m properdocs build --strict` clean, zero warnings.
5. No third-party runtime import anywhere in `src/`. Asserted by a test.
6. No hard-coded `8` outside `Board`'s default dimension. Asserted by a test.
7. Every rule in `notes/chess_rules.md` implemented, each tested both enabled
   and disabled: castling, en passant, promotion, fifty-move, threefold
   repetition, insufficient material, stalemate, mutual-agreement draw, and the
   flag-fall nuance.
8. The rule set is data. Disabling a rule changes a setting and removes no
   source logic; enabling it again restores it.
9. Standard chess is the default rule set, so an unconfigured game plays orthodox
   chess.
12. Castling, en passant and promotion are generated as `Tah.typ tahu` move
    types, not as special cases in the validator.
13. A quest is buildable from the settings surface using a data-driven condition,
    with no Python written by the player.
10. Those rules hold on non-8×8 boards, rank-relative rules generalised rather
    than disabled.
11. A game is played end to end from the entry point to a result.
14. All 15 Czech aliases importable and identical to their canonical objects;
    `Tower`, `Horse` and `Controller` gone.
15. Deviation 3 (settings) and deviation 4 (rule engine) recorded in
    `notes/object_model.md` with approval context.
16. The GUI covers FR-17 to FR-22; settings covers FR-23 and FR-24.
17. CI green across Python `3.10`, `3.11`, `3.12`, `3.13`, depending on no
    external repository's workflow.
18. `notes/chess_rules.md` amended where the generalisation in item 10 departs
    from it.
19. No dead code from §1.4 remains, and the §1.5 docstring gaps are closed.
20. `piece.py` demo block removed.

---

## 6. Decision log

| # | Decision | Outcome |
|---|---|---|
| 1 | Czech aliases with diacritics? | **No** — ASCII only |
| 2 | Which classes get Czech aliases? | **Only those the diagram names in Czech** (PRD §5) |
| 3 | Canonical language | **English canonical**, Czech as aliases |
| 4 | `Tower` | **Dropped.** Not a name this project uses; in no diagram box |
| 5 | `Knight` vs `Horse` | **`Knight` canonical**, `Kun` the Czech alias, `Horse` removed with no legacy alias |
| 6 | `Controller` alias | **Deleted**; `controller.py` renamed to `game_manager_controller.py` |
| 7 | Alias visibility in docs | **No special handling.** If they render, they are visible |
| 8 | Settings layer | **Built**, deviation 3 recorded in `notes/object_model.md` |
| 9 | Rank-relative rules on custom boards | **Generalised.** Everything that can be generalised should be |
| 10 | Metadata-asserting tests | **All deleted** |
| 11 | Import smoke tests | **All deleted**, not reduced |
| 12 | Remaining tests | **Reworked** to test real features, not arbitrary expectations |
| 13 | Third-party libraries | **None** beyond `tkinter`; no chess library |
| 14 | Bot-authored pull requests | **Dropped** |
| 15 | PR topology | **Stacked where necessary, independent where possible** |
| 16 | Mockup fidelity | **Reference, not spec** |
| 17 | PRD home | **`PRD.md`** at root — a planning artifact, not documentation |
| 18 | Plan home | **`SCRATCHPAD.md`** at root, same PR as the PRD |
| 19 | Rules architecture | **Level 1 — the rule set is data**, with standard chess as the default. Every rule disableable per game by setting a value. Assessed in `notes/object_model.md` section 4 as **not** a deviation: the diagram already provides `Tah.typ tahu`, `Figurka.vektory` and `GameManager.get_stav` |
| 20 | PRD scope | Current state, out-of-scope, work streams, risks, acceptance criteria and decisions live in this file, not the PRD |
| 21 | Where the PRD points for governance | `AGENTS.md` stays normative for object model, language, delivery and the review trail. The PRD states only libraries and tests, which `AGENTS.md` does not cover. Confirmed on 2026-10-02 that the existing rules already cover it, so nothing was added |
| 22 | Pluggable classes | **Deferred.** A master issue covers a pluggable class per layer — rules, board, pieces, quests — landing after this track. Level 1 everywhere in the meantime |
| 23 | Quest conditions | **Data-driven and settings-configurable.** `condition_fn` callbacks are replaced by conditions a form can build. Pluggable quest logic deferred with 22 |
| 24 | Mockup reference | Lives in `SCRATCHPAD.md`, not the PRD. The PRD describes the product; the mockup guides implementation |
| 25 | Customisable pieces | Already data-driven via `Figurka` vectors, so diagram-supported. **Backlog** for now — not in the current FRs |

---

## 7. Out-of-scope routing

Nothing is out of scope globally; each item is owned by an issue.

| Item | Owner |
|---|---|
| Reproducing the diagram's typos — `GameVeiw`, `check_Pat`, `intger`, `akutalizuj_hrace`, `Id_uzivatele: hrac` | #123. Recorded as observed, never reproduced |
| Network play, persistence beyond the file log, GUI beyond the mockup's surface | #129 |
| Reinstalling the shared DarkFactory pipeline | Deferred, no issue until requested |
| The `pipeline` remote and empty `.pipeline/` | #126 |
| Pluggable classes for rules, board, pieces, quests | Deferred master issue, after this track |
| Generalised and customisable pieces beyond the data model | **Backlog.** The data model already supports it; no FRs are written for it in this track |

### 7.1 Contradiction found and outstanding

`notes/upstream_base.md` documents an `origin/upstream-base` branch as
"permanently pinned" and protected, with a diff command that reads
`git diff origin/upstream-base...main`. **That branch no longer exists** — it was
deleted in the branch cleanup and pruned from the remote, so the documented diff
command fails and the described branch protection is fiction.

`tests/test_upstream_base_notes.py` does not catch this, because it asserts only
that the strings `"upstream-base"` and `"a98e36d"` appear in the file.

The `upstream` remote itself still resolves, and the base commit `a98e36d` still
exists in its history, so the fork provenance is recoverable. This needs
resolving: restore the branch, or rewrite the note to point at the remote
directly. The note is currently the one document in the repository that is
simply untrue.

---

## 8. Visual reference

`GUI_mockup.svg` at the repository root is the reference for the game's layout,
content and data bindings. **It is not a spec to reproduce exactly.** Where the
mockup and the reference diagram disagree, the diagram governs.

It is an Excalidraw export of roughly 275 text nodes, and it is more than
wireframes: it is a design *plus* a gap analysis, carrying live `file:line`
bindings into the current source.

### Navigation

Tabs: GAME, SETTINGS, QUESTS, OPTIONS, ELO.

### GAME tab

Board with algebraic coordinates; player panels with clocks; captured, lost and
active columns; a turn indicator including check; NEW / DRAW / RESIGN actions;
move history with export; a status footer; quest cards reading
`QUESTS / First Blood - 10 XP`.

Bound by the mockup to `WindowController.on_square_clicked()` /
`GameController.handle_square_click()`, `GameManager.players / active_player`,
`GameManager.make_move() -> Move.execute()`, `GameManager.get_state()`,
`GameLogger.get_moves()` / `ChessNotationWriter.export()`,
`WindowController.status_message / set_status()` and
`QuestManager.get_quests() / check_quests()`.

### SETTINGS tab

Board configuration (rows, columns, a custom-size limit), starting position
(standard or edit), piece configuration with a move-vector / attack-vector /
can-jump table and an *Add piece* action, quest configuration, gameplay inputs,
and save / reset / cancel.

Bound to `Board.dimensions / rows / cols`, `Board(setup_pieces=False)` /
`set_piece_at()` / `replace_piece()`, `getDirections()` /
`getAttackDirections()` / `canJump()`, quest fields and `QuestManager`
register/get/check, `Timer.initial_time`, `new_game()` / `reset_time()` /
`reset_selection()` / `close_dialog()`.

### Gaps the mockup states about itself

- *"The renderer is proposed; green rows are controller hooks, blue rows are
  model data, and orange rows are partial integrations."*
- *"No SettingsView or SettingsController"*, and *"No Settings model/controller/
  view exists yet."*
- *"Move.validate() hard-codes 8; FEN writer assumes 8."*

It labels its own rows HOOK / MODEL / PROPOSED / PARTIAL / LIMIT.

All three gaps are independently confirmed by this audit and are covered by the
current track: the settings layer by PR 7, the hard-coded 8 by PR 3.

### Note on staleness

The mockup's `file:line` bindings were accurate when it was drawn and will drift
as the code changes. They are a starting point for implementation, not a contract
to hold the source to.
