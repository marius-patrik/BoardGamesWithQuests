# Current action queue — Python/Tkinter v1.0.0

**Reconciled 2026-10-27.** Canonical parent: [#430](https://github.com/marius-patrik/BoardGamesWithQuests/issues/430). Implementation branch: bot-authored draft [#271](https://github.com/marius-patrik/BoardGamesWithQuests/pull/271). This queue is not evidence that an agent has been dispatched. Check the live issue and PR head before executing any item.

## Start now (two independent ownership domains)

- [ ] **[P0] #438 draw / claims lifecycle — AGENT A DISPATCHED:** One writer for `src/model/game/manager.py`, bounded engine/session/hook modules, and narrowly necessary `src/view/player_game_view.py`/controller interactions. Complete authorized mutual draw offers and pointer-selected canonical intended-move claims; prove replay/rollback/idempotency/clock/quest with actual Tk GUI. Coordinate #452/#453 view ownership.
- [x] **[P0] #439 persistence/security SOURCE INTEGRATED:** Independent three-file review and atomic blob integration in #271 at `52043693` (agent candidate `8c84d395`); subprocess Chess/Draughts/settings and hostile-file tests included; no conflicting manager/session/view writes.
- [ ] **[P0] #439 ACCEPTANCE PENDING:** Verify final exact-head governed matrix and native #443 extracted package file/restart behavior before issue closure.
- [ ] **[P0] Orchestrator integration:** Review independent task diffs against newest #271 HEAD, re-run behavioral and Xvfb checks, reconcile generated docs and issue states. Do not merge protected branches.

## After first integration

- [ ] [#436](https://github.com/marius-patrik/BoardGamesWithQuests/issues/436): Finish FIDE exceptional terminal/timeout and 50/75 threshold/intended-move evidence; real Chess GUI. Avoid a parallel generic engine writer.
- [ ] [#437](https://github.com/marius-patrik/BoardGamesWithQuests/issues/437) / [#449](https://github.com/marius-patrik/BoardGamesWithQuests/issues/449): Final WCDF playable certification, actual agreement/prospective claims and capture chooser UI after #438/#452.
- [ ] [#452](https://github.com/marius-patrik/BoardGamesWithQuests/issues/452): Human-readable pointer route/promotion choices, pieces, targets, screenshots (after #438 releases view ownership).
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
