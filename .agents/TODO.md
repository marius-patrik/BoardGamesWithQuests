# Current action queue — Python/Tkinter v1.0.0

## 2026-10-31 — Dispatch I failed closed / #477 unknown-timeout contract

- [x] Confirm Dispatch I is a proof/blocker report only, branch `game/473-sound-unwinnability` unchanged `b0dcec95eac33b882f2ee0c0ac5cdb84927a3329`; previous 147 pass/1 true red per Python from G is not new Dispatch I CI. Source unchanged; don't merge red test as a fix.
- [ ] **#473:** sound legal-successor proof/witness with budget and near-twin adversarial oracle; no hardcoded FEN, no blind CHA Rust engine dependency, no full-FIDE claim without mathematical correctness.
- [ ] **#477:** newly created read-only source-backed design for `unknown` terminal outcome, versioned pending/adjudication state, clocks, action idempotency, event replay, restart, legal resolution, and OS GUI feedback. This missing contract BLOCKS safe production implementation. Maintainer chooses policy.
- [ ] Leave Chess `playable:false`, #436/#473/#477 OPEN; do not publish or merge protected branches.
- [ ] Continue GUI #454 serial, native #443, WCDF #437/#449, structural #462 only after source owners hand off.


## 2026-10-31 — H integration and final GUI dispatch

- [x] **#453 source changes accepted:** candidate `fba5d5674f6d2f6dee660c5d79d6e9583b9368c4` quest cards/definition-aware cache/individual nested scrolling, player/material/clock hierarchy, 115-event incremental history; 63 actual GUI tests and 22 screenshots, Python 3.10–3.13 321 governed test cases per version. Four candidate workflows PASSED.
- [x] Five owned source/test/screenshot file blobs safely integrated into #271 at `6bf2a001b490d8a34cbf8bc3fe264cd1a8a96fa2`; AST/UML auto-regenerated on combined source at `0a173933b930f6e47b1dc3be7f14c36d98cdd8ba`; no interfering engine/packaging changes.
- [ ] **#453 issue closure GATE:** exact latest combined-head quality, real Tk screenshot and four-OS PACKAGE jobs must pass; frozen native app interaction is separate #443.
- [ ] **#454 next exclusive GUI owner:** prepared `ux/454-native-final-polish` at `0a173933...`; native ttk theme, cross-platform dialogs/focus, correct preferences, measured redraw, concise I/O messages, visual and pointer regression. Never rename files before #462.
- [ ] **#473 P0** isolated Chess sound-unwinnability correction (FIDE fortress red) still pending, no speculative shortcut; #437/#449 WCDF final certification, #462 all 10 maintainer path/source-review threads and #443 frozen OS acceptance remain OPEN.


## 2026-10-31 — #452 closed; #473 must resolve FIDE correctness

- [x] **#452 source GUI DONE / issue CLOSED:** Combined exact PR #271 HEAD `b9e1db9961cac9c044ad171a48c254fbd6fbe74d` has all nine applicable workflows completed SUCCESS. Preserved original board and 2 sided player/quest GUI; native extracted interactions remain #443.
- [x] **#436 / Dispatch G read-only/test-only verification:** candidate `b0dcec95eac33b882f2ee0c0ac5cdb84927a3329` adds four independent FIDE tests; all Python 3.10–3.13 147 passed and 1 **FAIL** at dead fortress timeout; real Xvfb 52 passed; near-twin mating possibility and mate-v-75-move precedence pass. CI run [41138925199](https://github.com/marius-patrik/BoardGamesWithQuests/actions/runs/41138925199). No production fix; keep failing witness isolated until corrected (do NOT weaken assertion or poison unrelated PR #271 CI).
- [ ] **NEW #473 P0 sound unwinnability:** agent branch `game/473-sound-unwinnability` exists at original G tip with 4 tests and generated AST; work on mathematically sound, bounded generic queries with `unwinnable/winnable/unknown` semantics, asymmetric FIDE 6.9 timeout and 5.2.2 two-sided dead. May use CHA-Solver only as researched reference after move-equivalence/native footprint evidence. No heuristic or hardcoded puzzle. Return BLOCKED if cannot implement a sound fix; do not mark Chess playable.
- [ ] **#453 exclusive GUI** owner continues in prepared `ux/453-quest-history-polish`; after that #454, and then #462 source-tree renames. Native acceptance #443 incomplete and isolated.
- [ ] Finish WCDF #437/#449; independent #444 audit; protected approval/promotion/release #445 still blocked.


## 2026-10-30 — Independently accepted #452 GUI source integration

- [x] #452 D2 complete candidate `98b08ba0`: genuine two player+quest side panels, filled light/dark Chess vector Canvas pieces, colored crowned Draughts, real full-route/promote dialogs, accurate single-hop jumps and capture-highlight markers, 12 actual before/after Tk screenshots and >6 independent quests.
- [x] Candidate exact-source workflows [visual #40697531451](https://github.com/marius-patrik/BoardGamesWithQuests/actions/runs/40697531451), [Python+Tk #40697531555](https://github.com/marius-patrik/BoardGamesWithQuests/actions/runs/40697531555), [four OS packaging #40697531788](https://github.com/marius-patrik/BoardGamesWithQuests/actions/runs/40697531788), [full quality #40697533964](https://github.com/marius-patrik/BoardGamesWithQuests/actions/runs/40697533964) all SUCCESS.
- [x] #452 seven scoped source/test/workflow files integrated in #271 at `e295f1230dbcd63d5d81dcf8e084e0194590b5f2`; generated diagrams refreshed on combined tree at `54d1635a86aa2027548a1dbc7e0212db31d3fb77`; did NOT overwrite Chess fix or canonical governance records.
- [ ] #452 current integrated-HEAD UI/tests/governance must PASS before closing issue; detached Windows/macOS/Linux native executable acceptance remains issue #443.
- [ ] Dispatch #453 focused long-quest, scrolling/cache and history/player panels after #452 integration; no conflicting #454 / #462 files during its ownership.
- [ ] Dispatch #436 proof-driven FIDE fortress/timeout correctness on engine+Chess tests **without** GUI writes; forbid hard-coded FEN, simplistic material heuristics, or FIDE procedural overclaim.
- [ ] Once #453/#454/native owners finish, execute maintainer #462 atomic import/resource/module move and resolve 10 review threads, rerun four OS extraction.


## New active status — 2026-10-27 (E/C/F/D2)

- [x] #436 narrowly verified same-colour-promoted-bishops FIDE correction and three dedicated acceptance tests integrated at `2c22e18dd52bb554e9b5ac4a1c0eb8feba3dfaf6` (candidate Python 3.10–3.13 and Tk pass).
- [ ] #436 **TRUE RED ISSUE:** Buchanan FIDE fortress timeout returns win instead of draw, [CI #40480361409](https://github.com/marius-patrik/BoardGamesWithQuests/actions/runs/40480361409). Requires follow-up bounded correctness design; keep `playable:false`.
- [ ] #443 native QA: extracted app Chess/Draughts opening moves proven on all four OS, but candidate latest run #40480277365 remains failed; settings missing on Linux/macOS; Windows further journeys blocked. No candidate integration yet.
- [x] #462 read-only structural plan received; DO NOT perform cross-package rename while active GUI/native writers overlap.
- [x] #452 interrupted D branch inventoried: tip `adb2e2a7c72ffec4da92fd3b9e0d64466ec1c34e`, nine changed files; filled-color pieces, left/right per-player quests, pointer choices implemented; real Tk screenshots+tests pass and native packaging pass; #463 temp verification PR closed unmerged.
- [ ] #452 dispatch D2 **RECOVERY** based on exact old D tip using `ux/452-board-interaction-recovery`: finish real UI evidence and UX concerns, compare with latest integration source after #436 E and reconcile CI; do not rebuild working GUI; preserve #438 draw functionality.
- [ ] #453/#454 quest/history/final Tk polish serial after D2; #462 structural moves only once GUI/native files are unowned.


## New maintainer acceptance requirements — 2026-10-27

- [ ] **[P0] #452 — currently dispatched:** Replace top/bottom player panels and global right quest list with **left Player 1 + own quests | centered original Canvas board | right Player 2 + own quests** (reference `.agents/reference/images/GUI_mockup.svg`). BOTH white and black use solid filled icon silhouettes distinguished by actual light/dark piece colors with contrast outlines; solid Draughts discs, clearly crowned kings. Agent D may own necessary `player_view.py`/`quest_view.py` parts for the initial layout. Real screenshot/GUI tests at 840×640, 1100×760 and 1440×900.
- [ ] **[P0] #453 — after #452, NOT parallel:** verify >6 quests per participant, accurate participant identity/XP/progress, individual scroll, game-switch cache invalidation, long capture/100+ move history, without reverting two-side composition.
- [ ] **[P0] #462 — maintainer-required source/module refactor:** Ten new unresolved #271 threads map to exact operations in #462. Read-only rename/import/resource/entrypoint plan may begin now; **implementation waits until #436/#452/#443 handoff**, then preserve all Python/Tk/native/extracted archive gates and finally resolve verified review threads.
- [ ] **[P0] #271 maintainer review:** 54 total threads, 10 new unresolved as of 2026-10-27; reviewer CHANGES_REQUESTED. Keep all new findings open until actual code+CI verification, then obtain new native review approval.


**Reconciled 2026-10-27.** Canonical parent: [#430](https://github.com/marius-patrik/BoardGamesWithQuests/issues/430). Implementation branch: bot-authored draft [#271](https://github.com/marius-patrik/BoardGamesWithQuests/pull/271). This queue is not evidence that an agent has been dispatched. Check the live issue and PR head before executing any item.

## Start now (two independent ownership domains)

- [x] **[P0] #438 authoritative draw lifecycle SOURCE INTEGRATED:** Candidate `9993c38b` independently reviewed; ten source/test/workflow blobs integrated into #271 at `1ddc4f99` with no overlap with #439. Explicit pending offers/replies, no-op clocks/quests, claim eligibility and pointer-selected canonical intended moves. Candidate exact SHA gameplay 3.10–3.13/Tk Xvfb green; verification PR #461 closed unmerged.
- [ ] **[P0] #438 CERTIFICATION PENDING:** Exact combined-head governed Actions, extracted-native #443 acceptance, and limited FIDE Article 9.5.3 tournament-arbiter procedure clarification under #436.
- [x] **[P0] #439 persistence/security SOURCE INTEGRATED:** Independent three-file review and atomic blob integration in #271 at `52043693` (agent candidate `8c84d395`); subprocess Chess/Draughts/settings and hostile-file tests included; no conflicting manager/session/view writes.
- [ ] **[P0] #439 ACCEPTANCE PENDING:** Verify final exact-head governed matrix and native #443 extracted package file/restart behavior before issue closure.
- [x] **[P0] Orchestrator source integration:** Both #438 and #439 independently reviewed and incorporated into sole draft #271; no protected branch merged. Combined-head generated AST/UML regenerated by CI.
- [ ] **[P0] Orchestrator verification:** Verify all governed checks on latest combined SHA; handle any failing tests and close task branches after blob identity evidence.

## After first integration

- [ ] [#436](https://github.com/marius-patrik/BoardGamesWithQuests/issues/436): Finish FIDE exceptional terminal/timeout, 50/75 thresholds, integration of intended moves and real Chess GUI; independently clarify unimplemented FIDE 9.5.3 arbiter-mediated invalid claim sanctions vs atomic-rejection v1 contract. #438 engine ownership is released.
- [ ] [#437](https://github.com/marius-patrik/BoardGamesWithQuests/issues/437) / [#449](https://github.com/marius-patrik/BoardGamesWithQuests/issues/449): Final WCDF playable certification, actual agreement/prospective claims and capture chooser UI after #438/#452.
- [ ] [#452](https://github.com/marius-patrik/BoardGamesWithQuests/issues/452): **Ready for an independent GUI owner** after #438 integration. Human-readable pointer route/promotion choices, pieces, targets and real screenshots; coordinate with any #438 corrective work.
- [ ] [#453](https://github.com/marius-patrik/BoardGamesWithQuests/issues/453): Quests/history/player hierarchy, 100+ moves/quests and scroll behavior (after #452).
- [ ] [#454](https://github.com/marius-patrik/BoardGamesWithQuests/issues/454): ttk/native dialogs, settings, focus, measured redraw (last GUI batch).
- [ ] [#440](https://github.com/marius-patrik/BoardGamesWithQuests/issues/440): Audit-sourced code-quality cleanup without functional rewrite (after shared engine stabilizes).
- [ ] [#450](https://github.com/marius-patrik/BoardGamesWithQuests/issues/450) / [#442](https://github.com/marius-patrik/BoardGamesWithQuests/issues/442): Evidence-mapped test redesign, real public-boundary acceptance, no premature test deletion (coordinate test-file ownership).
- [ ] [#443](https://github.com/marius-patrik/BoardGamesWithQuests/issues/443): Actual extracted frozen UI journeys on all four systems; source/binary/checksum proof.
- [ ] [#444](https://github.com/marius-patrik/BoardGamesWithQuests/issues/444): Independent final release audit, exact HEAD.
- [ ] [#445](https://github.com/marius-patrik/BoardGamesWithQuests/issues/445): Only after independent PASS and separate explicit maintainer approvals, merge/promote/publish and verify public PrideVer v1.0.0.

## Verified completed, not to be reassigned

- [x] #414 governance merged.
- [x] Read-only #432/#433/#434/#435 audits completed (implementation recommendations remain routed above).
- [x] #431 terminal outcome/actor fix; #446 recursive equality metering; #456 aggregate budget and rollback; #447 responsive layout; #451 lifecycle UI — all verified/integrated.
- [x] #448 keyboard board navigation explicitly deferred (`not_planned`) and not a v1 gate.
- [x] Chess #436 independently verified base reference test module and game fixture integrated; **full FIDE certification remains open**.
- [x] WCDF #437/#449 scoped rules/config and acceptance tests integrated; **full user-playable certification remains open**.
- [x] 14 obsolete task/verification branches deleted with exact SHA and open-PR/protection safeguards (Actions #40468515823). Current active/ref branches retained.

## Open release caveats

- Neither Chess nor Draughts is yet `playable:true`; active v1 release remains **NO-GO**.
- Existing Actions green at prior code SHA does **not** prove final-head or frozen GUI acceptance. Two unrelated Vercel commit statuses fail with build-rate-limit indication; confirm actual branch required checks.
- PR #271 is DRAFT and has an outstanding CHANGES_REQUESTED review disposition; all 44 currently enumerated review threads are resolved, but resolved threads do not equal approval.
- PR #422 is downstream/deferred V2, not to be folded into v1; source-level future contract belongs to #348.
