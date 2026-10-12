# Execution Status and Integration Plan

**Checked against `main` on 2026-10-12.** This file records **current status, sequencing and release gates only**. Do not use it as a second PRD, chess rulebook or object-model transcription. Requirements live in [PRD](notes/PRD.md); architecture decisions in [object model](notes/object_model.md); diagram facts in [reference](notes/reference_diagram.md); process in [AGENTS](AGENTS.md). Detailed acceptance criteria and discussions belong to the linked issues and PRs, not duplicated here.

## 1. Status on main

- `packages/engine/` contains partial shared model, controller, and launcher; `packages/chess/` and `packages/checkers/` contain JSON game declarations. The former `src/` and `games/` layouts are gone (merged [#220](https://github.com/marius-patrik/BoardGamesWithQuests/pull/220)).
- The Tkinter view under `packages/engine/view/` is **not** implemented on `main`; the runnable UI exists only in the stacked feature work awaiting review. The current launcher intentionally must not pretend otherwise.
- Full game rules, quest extensions, actual configuration editing and complete end-to-end gameplay are **not integrated on `main`**. JSON fixtures are not equivalent to implemented rule modules.
- The old test suite was retired in [#222](https://github.com/marius-patrik/BoardGamesWithQuests/pull/222). There are **no behavioral gameplay tests on `main`**; syntax, format, docs and CI success do not establish game correctness. Rebuild the suite from scratch in [#239](https://github.com/marius-patrik/BoardGamesWithQuests/issues/239).
- GitHub development releases may exist before the game is finished; do **not** describe them as validated gameplay releases.

## 2. Active dependency chain

The product track is tracked in [#129](https://github.com/marius-patrik/BoardGamesWithQuests/issues/129), UI in [#125](https://github.com/marius-patrik/BoardGamesWithQuests/issues/125), and preparatory work in [#131](https://github.com/marius-patrik/BoardGamesWithQuests/issues/131). Actual open PRs are the authority for merge state and stack base; do not treat this table as a frozen list of GitHub branches.

| Stage | PR(s) as of the audit | Integration dependency |
|---|---|---|
| Core abstractions | [#218](https://github.com/marius-patrik/BoardGamesWithQuests/pull/218), [#217](https://github.com/marius-patrik/BoardGamesWithQuests/pull/217), [#219](https://github.com/marius-patrik/BoardGamesWithQuests/pull/219) | Merge or restack board, quests, then rules with correct package paths. |
| Chess behavior and packaging | [#216](https://github.com/marius-patrik/BoardGamesWithQuests/pull/216), [#215](https://github.com/marius-patrik/BoardGamesWithQuests/pull/215) | Depend on the shared rule layer. |
| Integration and UI | [#214](https://github.com/marius-patrik/BoardGamesWithQuests/pull/214), [#212](https://github.com/marius-patrik/BoardGamesWithQuests/pull/212), [#213](https://github.com/marius-patrik/BoardGamesWithQuests/pull/213) | Complete headless game loop before UI; keep review fixes on top. |
| Stacked subsequent fixes and formats | [#160](https://github.com/marius-patrik/BoardGamesWithQuests/pull/160) through [#209](https://github.com/marius-patrik/BoardGamesWithQuests/pull/209) (selected PRs; see live open list) | Rebase sequentially; don't recreate the retired tests from older branches. |
| Final behavior gate | [#239](https://github.com/marius-patrik/BoardGamesWithQuests/issues/239) | Only after final integrated APIs and UI are stable. |

**Important:** Several older stacked branches still contain pre-#220 paths and tests. Their historical claims of hundreds of passing tests describe old revisions. Neither those results nor the text of a draft PR is proof for current `main`.

## 3. Delivery and reviews

1. Resolve comments and rebase each stacked branch on its actual predecessor; update imports, JSON paths and package discovery for `packages/{engine,chess,checkers}` without retaining parallel legacy directory trees.
2. Integrate independent core types before rules; integrate game-specific rule modules outside the engine, then wire the game manager, controller and view.
3. Verify checkers as an independent sibling that does not require chess-specific engine code. [#163](https://github.com/marius-patrik/BoardGamesWithQuests/pull/163) corrects English-draughts rules; the old flying-king implementation must not be mislabeled as WCDF English draughts.
4. Integrate settings, custom-authored rules/quests, notation, import/export and error handling. Do not duplicate scenario-specific logic in the shared engine.
5. Rebuild a new behavioral suite in #239 against the **final** public APIs, across Python 3.10–3.13 and actual Tkinter UI flows. Independently verify both chess and checkers rule conformance, exporters and complete games.
6. Run all required CI checks and obtain the maintainer's approval before merging. Claims about gameplay depend on behavior tests, not on docs/compile checks.

## 4. Acceptance and release gate

The completion criteria are [PRD §7](notes/PRD.md#7-functional-requirements), [the architecture deviations](notes/object_model.md), and the concrete linked integration issues. Minimum verifiable end-to-end evidence:

- Real installation and game discovery; two independent games load from their sibling packages with no engine game-name switch.
- Correct rules, game outcomes, configurable board dimensions, chained moves, clocks, quests and user tracking on exercised scenarios.
- View interaction through a real window: select, move, update, start, finish and configuration editing (not screenshots or import-only tests).
- Round-trip import/export behavior for applicable formats, especially chess PGN/SAN and FEN; no engine-wide chess-specific formats.
- Exact conformance to the intended architectural relationships or a recorded and approved deviation.
- Fresh automated tests on supported Python versions and passing documentation/CI.

**Do not conflate automatic development tagging/releases with a finished-product certification.** Before marketing a release as playable and correct, #239 and the relevant integration gates must be green.

## 5. Key risks and unblocked decisions

- A green docs pipeline can conceal a nonfunctional UI and absent rules. Treat syntax/docs checks as scaffolding validation only.
- Early branches import from old `src/` or `games/` and can resurrect legacy tests if mechanically rebased. Review diffs against `main` before merge.
- English draughts kings move one step; the flying-king variant is a different ruleset. Verify #163 rather than changing PRD to match the old bug.
- FIDE draw rules distinguish claims from automatic termination; SAN notation and FEN metadata are not plain destination-square strings.
- Do not reintroduce abandoned migration paths or superseded designs as live instructions.

## 6. Document ownership

| Authority | Contains | Must not contain |
|---|---|---|
| `notes/reference_diagram.md` | Literal exported reference diagram facts | Implementation status or duplicate planning |
| `notes/object_model.md` | Approved design deviations | Diagram box inventory or delivery checklist |
| `notes/chess_rules.md` | Standard chess rules baseline | Engine architecture or task estimates |
| `notes/PRD.md` | Final product requirements | Current PR delivery/status claims |
| `SCRATCHPAD.md` | Current status, dependencies and integration gates | Full rulebook, redundant PRD or stale code line-number inventory |
| `AGENTS.md` | Governing repository process | Per-feature implementation notes |
