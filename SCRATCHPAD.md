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
| **Rule set is not configuration data** | `RevizorTahu` inlines each rule and `get_state` hard-codes the outcome ladder. There is nowhere to store a named rule set, so FR-7 to FR-20 are unmet. Not a redesign — the diagram already provides the fields (`Tah.typ tahu`, `Figurka.vektory`, `GameManager.get_stav`) |
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
rest are removed by PR 13.

**Written but never read:** `Board.captured_white:38` ·
`Move.captured_piece:32` · `Move.promotion_piece:33` · `GameManager.players:48` ·
`Board.dimensions:33` · `GameManager.STATE_CHECK:25` ·
`WindowController.title/width/height:28` · `ExportWriter.field:18` ·
`Player.user` / `Player.setUser`

Several of these become live once PR 5 wires the subsystems and PR 17 provides
the view. PR 13 re-checks each one and removes only what is still dead — a
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
| `tests/test_upstream_base_notes.py` | 1 | Deleted with its note. Asserted only that a commit SHA appeared in `notes/upstream_base.md` |
| `tests/test_docs_and_docstrings.py` | 11 of 12 | Metadata and workflow-pin tests go; the docstring-presence and strict-build checks stay |

**53 of 139 tests assert nothing about the product.** Deleted, not reduced.

`tests/test_object_model_notes.py` is deleted even though `notes/object_model.md`
is now carrying deviation records — the requirement is that the deviations are
recorded and approved, not that a test greps for a URL.

### 2.2 Rework

The surviving ~87 tests keep their product coverage and gain:

- **Feature-flow tests.** A whole game driven end to end — configure, play,
  reach a result. No test currently exercises `GameManager.make_move` in a
  sequence, which is why six orphan subsystems went unnoticed.
- **Rule tests.** One per rule, each exercised both enabled and disabled, so
  FR-16 and FR-18 are genuinely covered rather than asserted.
- **Rule-configuration tests.** Each rule driven both on and off through the
  same game, proving the setting — not a code path — is what changes it. Covers
  FR-12 and FR-18.
- **Rule-set profile tests.** The Classic Chess profile plays orthodox chess
  unconfigured; a duplicated-and-edited profile differs in exactly the rules that
  were changed; the default cannot be edited or deleted; profiles survive a
  process restart. Covers FR-16 to FR-20 and FR-29.
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

14 PRs in 4 waves. Independent wherever there is no real dependency.

```
WAVE 1 - no dependencies between these
  PR 2   Flatten src/ to root, amend AGENTS.md 1-2
  PR 3   Governance rules
  PR 4   Board generalisation - kill the hard-coded 8s
  PR 5   Quest conditions as data-driven classes
  (+ PR 11 remove scaffolding, PR 12 packaging - independent, any wave)

WAVE 2 - needs PR 4 (and PR 5 for quests)
  PR 6   Rule + RuleSet + OrthodoxChess + rules/ rulesets/ loading
  PR 7   Standard rules as Rule subclasses

WAVE 3 - needs PR 6 + PR 7
  PR 8   Wire all orphan subsystems incl. QuestManager

WAVE 4 - needs PR 8
  PR 9   View layer, tkinter, with the game-start modal
  PR 10  Settings surface: rule set selector, forms, code editor

WAVE 5 - needs PR 10
  PR 13  Czech aliases + dead code sweep

INDEPENDENT - any wave, any order
  PR 1   PRD + SCRATCHPAD                (in review)
  PR 11  Remove agent scaffolding
  PR 12  Packaging + entry point
  PR 14  Test-suite restructuring
```

Critical path is **5 waves**: `4 -> 6 -> 8 -> 10 -> 13`. Four PRs run
concurrently in wave 1, two in wave 2, two in wave 4.

**Why the flatten goes first.** PR 2 touches all 32 modules, `pyproject.toml`,
`properdocs.yml`, `docs_hooks.py` and `AGENTS.md`. Doing it before anything else
keeps every later diff a real behavioural change rather than an import-path
churn.

**Why PR 14 follows PR 13.** The dead-code sweep and the rename touch the same
modules; merging them avoids a guaranteed conflict and produces one coherent
"rename and clean" review.

**`define_ruleset` is not a PR.** It was proposed, assessed against the diagram,
and rejected — see `notes/object_model.md` section 5.

**Do not remove DarkFactory before the replacement CI is green on `main`.** The
repository must never sit without working required checks.

### 3.1 PR 2 — the flatten, in full

| What | Change |
|---|---|
| `src/model` → `model`, `src/controller` → `controller`, `src/view` → `view` | delete `src/` |
| `pyproject.toml` | `pythonpath = ["src", "."]` → `["."]` |
| ~15 modules | collapse the 3-level `try/except ImportError` fallbacks to plain imports; they existed only because of `src` |
| `AGENTS.md` Rules 1 and 2 | both say "all code in `src/`" |
| `properdocs.yml` | `docs_dir: src` → `docs_dir: .`, with `exclude_docs` extended, since the whole repo becomes the docs tree |
| `docs_hooks.py` | walk only `model/`, `controller/`, `view/` when emitting API pages, rather than scanning everything |
| `tests/test_docs_and_docstrings.py` | walk the package dirs |
| `tests/test_structure.py` | **no change** — its module list is already top-level, never `src.*` |

**Trap for PR 12, not PR 2:** a flat layout plus setuptools auto-discovery trips
over `tests/` sitting at the root, so packaging must set
`packages = ["model", "controller", "view"]` explicitly.

## 4. Risks

| Risk | Severity | Mitigation |
|---|---|---|
| `hasattr` and string probes in the rules engine break **silently** on rename | High | §1.3. Naming PRs ship tests that fail when a probe breaks, not only when a name changes |
| The rule set must become data without disturbing the diagram's four `RevizorTahu` operations | Medium | PR 4. Those operations stay exactly as drawn; only the outcome ladder in `get_stav` and move generation in `simulate_Move` gain a data-driven path. Assessed in `notes/object_model.md` section 4 as **not** a deviation |
| The code stack is eight PRs deep; a late rework invalidates the bottom | High | PR 3 and PR 4 are the risky ones and land first, while the stack is short and cheap to restart |
| Removing DarkFactory leaves the repo without CI mid-flight | High | Replacement CI merges and goes green before any removal |
| Generalising rank-relative rules to arbitrary board sizes is harder than it looks — home rank, knight-forward file and castling rook files all derived | High | Land in PR 3, before PR 4, so rule work builds on a correct board abstraction |
| Deleting 52 tests could mask real regressions | Medium | Every deletion is import-only or metadata-only. §2.2 adds behavioural coverage to offset, and PR 14's deletions can merge early and be observed |
| Czech aliases in mkdocstrings may render as data rather than documented API | Medium | Accepted per decision 7. No special handling |
| `python3-tk` absent on some runners | Medium | Assert-and-skip in tests; install in CI in the PR that first imports `tkinter` |
| GUI scope creep from the mockup | Medium | PRD §6 caps it; the mockup is a reference, the diagram governs |
| A per-game rule set multiplies the state space tests must cover | Medium | §2.2 requires each rule tested enabled and disabled, plus composition, rather than a combinatorial sweep |

---

## 5. Definition of done

The project is finished when all of these hold:

**Tests and quality gates**

1. `pytest` green, and **no surviving test asserts only on repository
   metadata**.
2. Every public method in `src/` is reachable from at least one test.
3. `black --check .` clean at line length 100.
4. `python -m properdocs build --strict` clean, zero warnings.
5. No third-party runtime import anywhere in `src/`. Asserted by a test.
6. No hard-coded `8` outside `Board`'s default dimension. Asserted by a test.

**Rules and rule sets**

7. A `Rule` parent class with the four hooks, each defaulting permissively, and a
   `Result` carrying a kind, a precedence and an optional winner.
8. Every rule in `notes/chess_rules.md` implemented against those hooks, each
   driven on and off through one game: castling, en passant, promotion,
   checkmate, stalemate, insufficient material, fifty-move, threefold repetition,
   mutual-agreement draw, and the flag-fall nuance.
9. Logic beyond the orthodox set is expressible without touching the engine: a
   piece that may move to any square, a piece that must capture if able, a game
   that ends when a named piece is lost. Asserted by tests, not by prose.
10. Two rules firing at once resolve by precedence, and the resolution is tested
    with rules written specifically to collide.
11. A rule's configured `value` persists in its profile; its runtime `state`
    resets each game and is never written to disk.
12. `OrthodoxChess` is the default rule set, plays orthodox chess with nothing
    configured, and can be neither edited nor deleted.
13. Rule sets are a multiselect over rule instances with no behaviour of their
    own; created, renamed, duplicated, edited rule by rule and deleted.
14. Rules load **only** from `rules/`. An attempt to load from any other path is
    refused, and that refusal is tested.
15. The editor refuses a rule that fails validation, and the failure is reported
    in the editor rather than at game start.
16. Those rules hold on non-8×8 boards, with rank-relative rules generalised
    rather than disabled.

**Configurable configuration**

15. A custom piece type is definable from settings with its own movement vectors,
    attack vectors and jump flag, placeable on the board, and movable.
16. A quest is buildable from the settings surface using a data-driven condition,
    completes on the intended event and not before, and awards its reward once.

**Runnable product**

17. A game is played end to end from the documented entry point to a result.
18. The GUI covers FR-21 to FR-26. Starting a game shows the modal of FR-27.
    Settings covers FR-29 to FR-35, including rule set management and the editor.
19. CI green across Python `3.10`, `3.11`, `3.12`, `3.13`, depending on no
    external repository's workflow.

**Object model and hygiene**

20. All 15 Czech aliases importable and identical to their canonical objects;
    `Tower`, `Horse` and `Controller` gone.
21. The settings-layer deviation is recorded in `notes/object_model.md`, and
    section 4 records that customisable rules and quests are **not** a deviation.
22. `notes/chess_rules.md` amended where item 14 departs from it.
23. No dead code from §1.4 remains, and the §1.5 docstring gaps are closed.
24. The `piece.py` demo block is removed.

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
| 25 | Customisable pieces | **In v1.** FR-3 already requires it — piece type, movement vectors, attack vectors, jump flag, colour, `kind`, addable to the palette. An earlier entry here wrongly recorded this as backlog; corrected 2026-10-02 |
| 26 | Rule vs rule set | A **rule** is the one code-driven layer, four hooks, each defaulting permissively. A **rule set** is a multiselect over rule instances with no behaviour of its own. FR-7 to FR-20 |
| 27 | Rule sets as profiles | Settings manages profiles. **`OrthodoxChess`** is the default and cannot be edited or deleted; a variant starts by duplicating it. FR-17 to FR-20 |
| 28 | Persistence | Rules as `.py` under `rules/`, rule sets as JSON under `rulesets/`, both at the repository root. No account needed. FR-20 |
| 29 | Backlog scope | **Pluggable logic only** (#130). Every data-driven configuration concern — rules, rule sets, board, pieces, quests — ships in v1 |
| 30 | Full customisation | Required "in any way", including a piece that may move to any square. Achieved by making **rules the only code-driven layer**, not by adding `Custom*` classes |
| 31 | Rule hook set | `permits_move`, `available_moves`, `outcome`, `on_move_made`. Exhaustive: turn-based logic can only forbid a move or end the game |
| 32 | Result precedence | `Result(kind, precedence, winner)`. Without it two rules firing at once is ambiguous, which would break "any conceivable logic" on the first collision |
| 33 | Rule `value` vs `state` | Configured value persists in the profile; runtime counters reset each game. Otherwise saving a profile would save a game's history |
| 34 | `define_ruleset` | **Rejected.** A rule set is constructed explicitly by multiselect, so the type set is closed and greppable. A registry would add surface for nothing |
| 35 | `CustomBoard` / `CustomPiece` / `CustomQuest` | **Rejected.** Board, piece and quest customisation is already complete via data; these classes would wrap data that is already custom and exist only for symmetry |
| 36 | `src/` flattened to root | `model/`, `controller/`, `view/` at the root. PR 2, first, because it touches every module and every config file |
| 37 | Engine vs rule content | Engine in `model/`, `controller/`, `view/`. Player-authored content in `rules/` (code) and `rulesets/` (data). Keeping them apart keeps authored files out of the source package |
| 38 | Ruleset selector | **Settings only** — "which profile am I editing". The game-start modal is the only place a rule set is chosen for play |
| 39 | Form exposure | **All** data-based configuration is form-exposed. The code editor is for rule *logic* only |
| 40 | Backlog, final | **Exactly one item**: #130, a no-code builder for authoring rule logic. The code editor covers the full hook expressiveness meanwhile |
| 41 | Execution of authored code | Deliberate product property, bounded: rules load only from `rules/`, never an arbitrary path, and the editor validates before a rule joins the vocabulary. PRD 3.3 |

---

## 7. Out-of-scope routing

Nothing is out of scope globally; each item is owned by an issue.

| Item | Owner |
|---|---|
| Reproducing the diagram's typos — `GameVeiw`, `check_Pat`, `intger`, `akutalizuj_hrace`, `Id_uzivatele: hrac` | #123. Recorded as observed, never reproduced |
| Network play, persistence beyond the file log, GUI beyond the mockup's surface | #129 |
| Reinstalling the shared DarkFactory pipeline | Deferred, no issue until requested |
| The `pipeline` remote and empty `.pipeline/` | #126 |
| Pluggable logic for rules, board, pieces, quests | **The only backlog item.** #130, deferred master issue, after this track |
| Generalised and customisable pieces | **Not backlog.** FR-3 and FR-14, shipped in v1 |
| Rule sets as profiles | **Not backlog.** FR-16 to FR-20, shipped in v1 |

### 7.1 Resolved: the stale upstream note

`notes/upstream_base.md` documented an `origin/upstream-base` branch as
"permanently pinned" and protected, with `git diff origin/upstream-base...main`
as the documented command. That branch was deleted in the branch cleanup and
pruned from the remote, so the command failed and the protection claims were
fiction. `tests/test_upstream_base_notes.py` did not catch it, because it
asserted only that two strings were present.

**Resolved by deleting the note** on 2026-10-02, at the user's direction. Its
subject, the branch, no longer existed, and the fork provenance is already
recorded in `README.md`. The accompanying test went with it.

`tests/test_docs_and_docstrings.py` hard-coded the note filename in four places
and would have broken on removal. It now discovers notes from disk, so adding or
removing a note cannot silently invalidate the docs-pipeline tests.

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
