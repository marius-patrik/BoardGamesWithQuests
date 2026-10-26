## Verified implementation status (2026-10-26)

- [x] [#431](https://github.com/marius-patrik/BoardGamesWithQuests/issues/431) — terminal-outcome patch corrected, integrated, exact-head Python 3.10–3.13 / real Xvfb green; CLOSED.
- [x] [#446](https://github.com/marius-patrik/BoardGamesWithQuests/issues/446) — duplicated unmetered equality removed; accepted budget/atomicity regression and exact integrated CI; CLOSED.
- [x] [#447](https://github.com/marius-patrik/BoardGamesWithQuests/issues/447) — responsive Tkinter layout/controls/Canvas with live compact-window screenshots and real Xvfb acceptance; CLOSED. Native frozen UX still pending #443.
- [ ] [#456](https://github.com/marius-patrik/BoardGamesWithQuests/issues/456) — independently reproduce and meter halfmove-reset, quest and named-draw evaluation under aggregate budget; verify rejection **after partially mutated candidate**, replay and rollback.
- [ ] [#448](https://github.com/marius-patrik/BoardGamesWithQuests/issues/448) — keyboard board focus/navigation/play through existing controller; after #447 (now complete).
- [ ] #436–#438/#449 complete independently verified FIDE/WCDF gameplay, clocks and quests; #439 persistence; #440 other real source-quality issues; #442/#450 replace nonproving tests with user-behavior acceptance.
- [ ] #451–#454 complete terminal/game lifecycle, rendering/choices, quest/history hierarchy and native ttk/dialog polish **sequentially** after #448.
- [ ] #443 actual extracted frozen interactive four-OS validation; #444 independent final audit; #445 maintainer-approved merge/promotion/PrideVer publication.

**Source verified at:** `dfb35fb3e1a1f4cb42fc5889c79c4dda3162e67e`. The following docs update is not gameplay code; full CI must run again at resulting current HEAD.

# TODO — v1.0.0 scoped execution queue

**Parent:** [#430](https://github.com/marius-patrik/BoardGamesWithQuests/issues/430). [PLAN](PLAN.md) owns phases and sequencing; individual linked issues own detailed instructions/acceptance. **Existing engine/GUI must be preserved and polished, not rewritten.**

## Ready now — one fix and independent audits

- [x] [#431](https://github.com/marius-patrik/BoardGamesWithQuests/issues/431): Terminal fix integrated and exact-head Python 3.10–3.13/Xvfb validated; CLOSED.
- [x] [#432](https://github.com/marius-patrik/BoardGamesWithQuests/issues/432): Audit every current test, classify retain/adapt/replace/delete, design genuine user-facing release acceptance.
- [x] [#433](https://github.com/marius-patrik/BoardGamesWithQuests/issues/433): Audit each production file for dead/duplicate/transitional code, readability, architectural ownership and correctness risks.
- [x] [#434](https://github.com/marius-patrik/BoardGamesWithQuests/issues/434): Audit independent Chess/WCDF rulebook cases and historical GUI/gameplay/quest/clock parity; no new export formats.
- [x] [#435](https://github.com/marius-patrik/BoardGamesWithQuests/issues/435): Complete GUI/UX audit delivered, 13 frozen screenshots and full specification inspected; implementation remains #441/#447/#448/#451–#454.

## Received audit evidence and newly scoped corrections (2026-10-23)

- [x] **Audit delivered** #432 — all-test inventory and replacement contract; **implementation pending** [#450](https://github.com/marius-patrik/BoardGamesWithQuests/issues/450), then parent #442.
- [x] **Audit delivered** #433 — whole-codebase 26-finding report; **metered equality corrected and integrated** [#446](https://github.com/marius-patrik/BoardGamesWithQuests/issues/446) (unmetered shadowed equality), broader #440.
- [x] **Audit delivered** #434 — FIDE/WCDF parity; **gameplay fixes pending** [#449](https://github.com/marius-patrik/BoardGamesWithQuests/issues/449) and parent #436–#438.
- [x] **Full GUI audit received and inspected** #435 — exact frozen Linux evidence ZIP: 41,761-byte report + 13 PNGs; all 26 UX findings routed in #435 and parent #441. The read-only audit #435 is closed. Responsive layout [#447](https://github.com/marius-patrik/BoardGamesWithQuests/issues/447) integrated; implement [#448](https://github.com/marius-patrik/BoardGamesWithQuests/issues/448) board keyboard → [#451](https://github.com/marius-patrik/BoardGamesWithQuests/issues/451) lifecycle/terminal → [#452](https://github.com/marius-patrik/BoardGamesWithQuests/issues/452) visual board/route choice → [#453](https://github.com/marius-patrik/BoardGamesWithQuests/issues/453) quests/history → [#454](https://github.com/marius-patrik/BoardGamesWithQuests/issues/454) dialogs/ttk/native polish. **#447 is implemented and integrated; #448 and #451–#454 remain pending.**
- [x] **Candidate executable verification** #431 — original regression + 128 affected tests pass on each Python 3.10–3.13, 11 Xvfb pass, [Actions run 39936337058](https://github.com/marius-patrik/BoardGamesWithQuests/actions/runs/39936337058).
- [x] **#431 integrated** into #271 with exact-head CI; verification-only workflow was not imported.

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
