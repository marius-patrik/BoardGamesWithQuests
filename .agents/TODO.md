# TODO — v1.0.0 scoped execution queue

**Parent:** [#430](https://github.com/marius-patrik/BoardGamesWithQuests/issues/430). [PLAN](PLAN.md) owns phases and sequencing; individual linked issues own detailed instructions/acceptance. **Existing engine/GUI must be preserved and polished, not rewritten.**

## Ready now — one fix and independent audits

- [ ] [#431](https://github.com/marius-patrik/BoardGamesWithQuests/issues/431): **Verify agent's isolated terminal patch** `0377a4e` with real pytest/Python 3.10–3.13 before integrating into #271. The isolated candidate tests passed; integration/exact-head tests pending.
- [ ] [#432](https://github.com/marius-patrik/BoardGamesWithQuests/issues/432): Audit every current test, classify retain/adapt/replace/delete, design genuine user-facing release acceptance.
- [ ] [#433](https://github.com/marius-patrik/BoardGamesWithQuests/issues/433): Audit each production file for dead/duplicate/transitional code, readability, architectural ownership and correctness risks.
- [ ] [#434](https://github.com/marius-patrik/BoardGamesWithQuests/issues/434): Audit independent Chess/WCDF rulebook cases and historical GUI/gameplay/quest/clock parity; no new export formats.
- [ ] [#435](https://github.com/marius-patrik/BoardGamesWithQuests/issues/435): Inspect running Tkinter, capture visual evidence and specify exact UX polish corrections (or report environment blocker).

## Received audit evidence and newly scoped corrections (2026-10-23)

- [x] **Audit delivered** #432 — all-test inventory and replacement contract; **implementation pending** [#450](https://github.com/marius-patrik/BoardGamesWithQuests/issues/450), then parent #442.
- [x] **Audit delivered** #433 — whole-codebase 26-finding report; **verified urgent correction pending** [#446](https://github.com/marius-patrik/BoardGamesWithQuests/issues/446) (unmetered shadowed equality), broader #440.
- [x] **Audit delivered** #434 — FIDE/WCDF parity; **gameplay fixes pending** [#449](https://github.com/marius-patrik/BoardGamesWithQuests/issues/449) and parent #436–#438.
- [ ] **Audit summary received, full files missing** #435 — agent reports 26 UX findings/13 screenshots; retrieve and inspect ZIP/Markdown/image files. Known fixes pending [#447](https://github.com/marius-patrik/BoardGamesWithQuests/issues/447) adaptive sizing, then [#448](https://github.com/marius-patrik/BoardGamesWithQuests/issues/448) keyboard/focus; remainder #441 after full report.
- [x] **Candidate executable verification** #431 — original regression + 128 affected tests pass on each Python 3.10–3.13, 11 Xvfb pass, [Actions run 39936337058](https://github.com/marius-patrik/BoardGamesWithQuests/actions/runs/39936337058).
- [ ] **Still outstanding:** integrate verified #431 candidate `0377a4e` into #271 only with authorization and exact-head CI; verification-only workflow stays isolated.

## Dependency gated implementation

- [ ] [#436](https://github.com/marius-patrik/BoardGamesWithQuests/issues/436): Complete/reference-verify Chess through the existing JSON/session engine.
- [ ] [#437](https://github.com/marius-patrik/BoardGamesWithQuests/issues/437): Complete/reference-verify English Draughts through the same engine.
- [ ] [#438](https://github.com/marius-patrik/BoardGamesWithQuests/issues/438): Finalize clocks, quests, rewards and session terminal transitions.
- [ ] [#439](https://github.com/marius-patrik/BoardGamesWithQuests/issues/439): Harden preferences, saved session, hostile storage, process restart and lifecycle.
- [ ] [#440](https://github.com/marius-patrik/BoardGamesWithQuests/issues/440): Apply evidence-based source cleanup without parallel authorities or feature regressions.
- [ ] [#441](https://github.com/marius-patrik/BoardGamesWithQuests/issues/441): Polish existing Tkinter layout/interactions with before/after screenshots and real GUI acceptance.
- [ ] [#442](https://github.com/marius-patrik/BoardGamesWithQuests/issues/442): Replace ineffective tests with independent game, public session, real GUI and negative-boundary acceptance.
- [ ] [#443](https://github.com/marius-patrik/BoardGamesWithQuests/issues/443): Exercise **extracted frozen GUI** and representative gameplay on all four native platforms; verify hashes/version/resources.
- [ ] [#444](https://github.com/marius-patrik/BoardGamesWithQuests/issues/444): Independently inspect exact-head code, final CI, current-state docs/diagrams, UX and native release evidence.
- [ ] [#445](https://github.com/marius-patrik/BoardGamesWithQuests/issues/445): Obtain maintainer approvals, protected merge/promotion, publish via PrideVer and verify public playable v1.0.0 downloads.

**Out of scope:** export feature expansion, a second engine/GUI, post-release FastAPI/Supabase/React/Tauri. **Future design:** [#348](https://github.com/marius-patrik/BoardGamesWithQuests/issues/348), implementation deferred #422. Task-specific DF dispatch requested [DarkFactory #2694](https://github.com/marius-patrik/DarkFactory/issues/2694).
