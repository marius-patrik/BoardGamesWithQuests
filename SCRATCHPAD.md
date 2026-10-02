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
| **The entire view layer** | `src/view/__init__.py` is one docstring line. No GUI, no renderer, no entry point. |
| **Most chess rules** | `notes/chess_rules.md:52-111` mandates castling, en passant, promotion, fifty-move, threefold repetition, insufficient material and mutual-agreement draw. Only stalemate is implemented. `King._has_moved` and `Rook._has_moved` are tracked and never read by any rule. |
| **Custom board sizes** | `move.py:44,46` rejects any move outside a hard-coded 8×8. `board.py:41` silently produces an empty board for any other size. Twelve sites total. |
| **Running application** | No `[project]` table, no build backend, no entry point. The package imports only because pytest sets `pythonpath`. |
| **Integration** | `QuestManager`, `UserManager`, `User`, `MetadataWriter`, `ChessNotationWriter` and `WindowController` are never instantiated or imported by any other module. |

### 1.2 Why the integration gap matters most

The feature count looks high and the wiring is zero. `GameManager.players` is
created at `manager.py:48` and never read, so players are never linked to users
and never consulted by move execution or state evaluation. Six subsystems were
built as standalone units and never connected to a game.

### 1.3 Correctness defects

| Defect | Location |
|---|---|
| `move.validate()` called without its `board` argument, so its occupancy and friendly-target checks are dead code | `validator.py:282` against `move.py:50-56` |
| Rules engine keys off piece-type **strings** (`"king"`, `"pawn"`) and `hasattr` duck-typing rather than inheritance. A missed rename degrades check/checkmate to `False` **silently** | `validator.py:64,92,101,159,166,167,187`, `board.py:106` |
| Unknown piece type silently serialised as a pawn | `export_writers.py:89` |
| PGN emits destination-square notation (`e4`) labelled as PGN, not SAN | `export_writers.py:120,126` |
| FEN hard-codes castling rights, en-passant square, halfmove and fullmove | `export_writers.py:101` |
| `get_state` returns a check state that no consumer reads | `manager.py:96`, `window_controller.py:74-79` |
| The only `pass` in `src/` is `GameManager.save_log` | `manager.py:78-80` |
| Leftover demo block in library code | `piece.py:94-97` |

### 1.4 The rules engine is string-coupled, and that dominates the rename risk

Any rename touches string literals and `hasattr` probes, not just identifiers.
A missed probe does not raise — it returns `False`, so check and checkmate
quietly stop working. Every naming change must therefore ship with tests that
fail when a probe breaks, not merely when a name changes.

---

## 2. Test suite restructuring

Current: `139` tests. Target: behaviour-only.

### 2.1 Delete outright

| File | Tests | Why |
|---|---|---|
| `tests/test_structure.py` | 27 | `importlib.import_module(...) is not None`. Proves a module parses, nothing more. |
| `tests/test_workflow_rules.py` | 15 | Asserts `AGENTS.md` text, workflow YAML and pipeline pins. Zero product code. |
| `tests/test_claude_symlink.py` | 3 | Asserts a symlink target and `.agents/` file existence. |
| `tests/test_readme.py` | 1 | Asserts `README.md` contains three URLs. |
| `tests/test_chess_rules_notes.py` | 1 | Asserts keywords in `notes/chess_rules.md`. |
| `tests/test_object_model_notes.py` | 1 | Asserts a URL and phrases in `notes/object_model.md`. |
| `tests/test_reference_diagram_notes.py` | 1 | Asserts a diagram id in `notes/reference_diagram.md`. |
| `tests/test_upstream_base_notes.py` | 1 | Asserts a commit SHA in `notes/upstream_base.md`. |
| `tests/test_docs_and_docstrings.py` | partial | The 11 metadata and workflow-pin tests go; the docstring-presence and strict-build checks stay. |

**52 of 139 tests assert nothing about the product.** Deleted, not reduced.

### 2.2 Rework

The surviving ~87 tests keep their product coverage and gain:

- **Feature-flow tests.** A whole game driven end to end — configure, play,
  reach a result. Currently no test exercises `GameManager.make_move` in a
  sequence, which is why six orphan subsystems went unnoticed.
- **Rule tests.** One per rule in `notes/chess_rules.md`, including the
  currently-unimplemented ones.
- **Invariant tests.** Asserted against the code, not the docs:
  - no third-party import anywhere in `src/`
  - no hard-coded `8` outside `Board`'s default dimension
  - every public method in `src/` is reachable from a test
  - every Czech alias in PRD §5 is importable and is the same object as its
    canonical name
  - `black --check` and `properdocs build --strict` still pass

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
TRACK 1 - Governance                 (independent of all code)
  PR 1   PRD + SCRATCHPAD            ◄── in review
  PR 2   Governance rules

TRACK 5 - Repository health          (independent of all code)
  PR 9   Remove agent scaffolding
  PR 10  Packaging + entry point
  PR 11  Test-suite restructuring

TRACK 2+3+4 - Product code            (one stack)
  PR 3   Custom board sizes, generalised rules   ─┐
  PR 4   Missing chess rules                     │ ordered
  PR 5   Wire orphan subsystems                  ─┘
              │
              ├──▶ PR 6   View layer          ─┐ parallel
              └──▶ PR 7   Settings layer      ─┘
                        │
                        └──▶ PR 8   Czech aliases
```

**Why this shape.** PR 3 is first because custom boards are a prerequisite for
honest chess rules; en passant and castling must not be written against a
hard-coded 8×8. PR 6 and PR 7 do not touch each other and branch from PR 5. PR 8
is forced last — it adds a symbol to every module in `src/`, so landing it early
guarantees conflicts with everything after it.

**Independence.** PRs 1, 2, 9, 10 and 11 touch no product code and can merge at
any time in any order, including while the code stack is in flight. PR 11 does
depend on PR 3–7 landing first for full coverage, but the deletions in §2.1 can
merge immediately and stand alone.

**Do not remove DarkFactory before the replacement CI is green on `main`.** The
repository must never sit without working required checks.

---

## 4. Risks

| Risk | Severity | Mitigation |
|---|---|---|
| `hasattr` and string probes in the rules engine break **silently** on rename | High | §1.4. Naming PRs ship tests that fail when a probe breaks, not only when a name changes |
| The code stack is six PRs deep; a late rework invalidates the bottom | High | PR 3 and PR 4 are the risky ones and land first, while the stack is short and cheap to restart |
| Removing DarkFactory leaves the repo without CI mid-flight | High | Replacement CI merges and goes green before any removal |
| Generalising en passant and castling to arbitrary board sizes is harder than it looks — home rank, knight-forward file and castling rook files all have to be derived | High | Land in PR 3, not PR 4, so the rule work builds on a correct board abstraction |
| Czech aliases in mkdocstrings may render as data rather than documented API | Medium | Accepted. If they render, they are visible; no special handling |
| `python3-tk` absent on some runners | Medium | Assert-and-skip in tests; install in CI in the PR that first imports `tkinter` |
| GUI scope creep from the mockup | Medium | PRD §7 caps it; the mockup is a reference, the diagram governs |
| Deleting 52 tests could mask real regressions | Medium | Deletions are all import-only or metadata-only; §2.2 adds behavioural coverage to offset |

---

## 5. Acceptance criteria

1. `pytest` green, and **no surviving test asserts only on repository
   metadata**.
2. Every public method in `src/` is reachable from at least one test.
3. `black --check .` clean at line length 100.
4. `python -m properdocs build --strict` clean, zero warnings.
5. No third-party runtime import anywhere in `src/`. Asserted by a test.
6. No hard-coded `8` outside `Board`'s default dimension. Asserted by a test.
7. Every rule in `notes/chess_rules.md` implemented and tested, including
   castling, en passant, promotion, all five draw conditions, and the
   flag-fall nuance.
8. Those rules hold on non-8×8 boards, with rank-relative rules generalised
   rather than disabled.
9. A game can be played end to end from the entry point to a result.
10. All 15 Czech aliases importable and identical to their canonical objects.
11. The settings deviation is recorded in `notes/object_model.md` with approval
    context.
12. The GUI covers PRD FR-13 through FR-18; settings covers FR-19 and FR-20.
13. CI green across Python `3.10`, `3.11`, `3.12`, `3.13`, depending on no
    external repository's workflow.
14. `notes/chess_rules.md` amended where the generalisation in item 8 departs
    from it.

---

## 6. Decision log

| # | Decision | Outcome |
|---|---|---|
| 1 | Czech aliases with diacritics? | **No** — ASCII only |
| 2 | Which classes get Czech aliases? | **Only those the diagram names in Czech** (PRD §5) |
| 3 | Canonical language | **English canonical**, Czech as aliases |
| 4 | `Tower` | **Dropped.** Not a name this project uses; in no diagram box |
| 5 | `Knight` vs `Horse` | **`Knight` is canonical**, `Kun` is the Czech alias, `Horse` removed with no legacy alias |
| 6 | `Controller` alias | **Deleted**; `controller.py` renamed to `game_manager_controller.py` to match the diagram's `GameManagerController` |
| 7 | Alias visibility in docs | **No special handling.** If they render, they are visible |
| 8 | Settings layer | **Built**, deviation recorded in `notes/object_model.md` |
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

---

## 7. Out-of-scope routing

Nothing is out of scope globally; each item is owned by an issue.

| Item | Owner |
|---|---|
| Reproducing the diagram's typos — `GameVeiw`, `check_Pat`, `intger`, `akutalizuj_hrace`, `Id_uzivatele: hrac` | Naming issue. Recorded as observed, never reproduced |
| Network play, persistence beyond the file log, GUI beyond the mockup's surface | Final completion issue |
| Reinstalling the shared DarkFactory pipeline | Deferred, no issue until requested |
| Keeping `Notes`-related docs hooks working after the metadata tests go | Docs, handled by the strict-build check |
