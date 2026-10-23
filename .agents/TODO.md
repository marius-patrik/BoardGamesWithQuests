# TODO — v1.0.0 scoped execution queue

**Parent:** [#430](https://github.com/marius-patrik/BoardGamesWithQuests/issues/430). [PLAN](PLAN.md) owns phases and sequencing; individual linked issues own detailed instructions/acceptance. **Existing engine/GUI must be preserved and polished, not rewritten.**

## Ready now — one fix and independent audits

- [ ] [#431](https://github.com/marius-patrik/BoardGamesWithQuests/issues/431): **Verify agent's isolated terminal patch** `0377a4e` with real pytest/Python 3.10–3.13 before integrating into #271. Tests **not executed** yet; remain blocked until evidence.
- [ ] [#432](https://github.com/marius-patrik/BoardGamesWithQuests/issues/432): Audit every current test, classify retain/adapt/replace/delete, design genuine user-facing release acceptance.
- [ ] [#433](https://github.com/marius-patrik/BoardGamesWithQuests/issues/433): Audit each production file for dead/duplicate/transitional code, readability, architectural ownership and correctness risks.
- [ ] [#434](https://github.com/marius-patrik/BoardGamesWithQuests/issues/434): Audit independent Chess/WCDF rulebook cases and historical GUI/gameplay/quest/clock parity; no new export formats.
- [ ] [#435](https://github.com/marius-patrik/BoardGamesWithQuests/issues/435): Inspect running Tkinter, capture visual evidence and specify exact UX polish corrections (or report environment blocker).

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
