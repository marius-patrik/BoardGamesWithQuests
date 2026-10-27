# Execution plan — BoardGamesWithQuests v1.0.0

**Last orchestration reconciliation:** 2026-10-27. **Canonical release contract:** [#430](https://github.com/marius-patrik/BoardGamesWithQuests/issues/430). Detailed acceptance belongs in each child issue; this file owns **sequence and active dependencies**, not another specification. One bot-authored draft desktop PR, [#271](https://github.com/marius-patrik/BoardGamesWithQuests/pull/271), targets protected `develop`. The downstream draft [#422](https://github.com/marius-patrik/BoardGamesWithQuests/pull/422) and proposed [v2 design #348](https://github.com/marius-patrik/BoardGamesWithQuests/issues/348) are **deferred until v1.0.0 is published and verified**.

## Product and release gate

Polish the existing Python/Tkinter desktop application and its one JSON-configured authoritative engine and `DesktopSession`. Ship fully usable, rulebook-correct Chess and WCDF English Draughts with clocks, quests, readable results, intended-move claims and mutual draw agreement, persistence, original Canvas renderer and pointer-operated interaction. Release frozen Windows x64, macOS ARM64, macOS x64 and Linux x64 distributions.

**Not v1:** hosted API, web/Tauri, Supabase, extra games, executable rule editor, second renderer/engine, expanded exports or keyboard-controlled board navigation. The latter was explicitly deferred in [#448](https://github.com/marius-patrik/BoardGamesWithQuests/issues/448); preserve normal Tk button/dialog focus and do not claim full keyboard accessibility.

## Verified completed steps

- [x] Governance [#414](https://github.com/marius-patrik/BoardGamesWithQuests/pull/414) merged; source-generated documents govern actual committed code.
- [x] Read-only investigations #432–#435 closed; their findings remain implementation inputs.
- [x] #431 terminal actor/outcome correctness integrated and independently executable-tested.
- [x] #446 recursive evaluator work-metering integrated; #456 aggregate evaluation budgets, late-proposal rollback independently verified and integrated.
- [x] #447 real small-window responsive Tk Canvas acceptance integrated; #448 keyboard-only board mode consciously deferred.
- [x] #451 terminal presentation, session replacement safeguards and game-title lifecycle independently verified and integrated.
- [x] Historical fix, reference and temporary verification refs cleaned (14 obsolete branches, [successful run #40468515823](https://github.com/marius-patrik/BoardGamesWithQuests/actions/runs/40468515823)); the active #438 agent branch remains separate; #439 task branch was deleted after its exact source/test blobs were integrated.
- [x] #439 scoped persistence hardening source and tests independently reviewed and integrated atomically at `520436932d74560fbe4d28e251174fd5cff25aff`, followed by source-generated AST-format commit. **Exact-head governed CI and native #443 acceptance remain open.**
- [x] Independently executed Chess reference candidate #436 (26 reference scenarios plus 99 affected regressions on Python 3.10–3.13); complete exceptional FIDE certification still **OPEN**.
- [x] Independently executed and integrated #437/#449 WCDF short-king, deferred captures, claim configuration and 91-ply referenced game; complete pointer-UI certification still **OPEN**.
- [x] The former `52e76147ab6c7a00cec9bc7db55eb61d5e0e9da9` docs-only baseline passed eight exact-head PR-triggered GitHub Actions workflows. Dispatch B was subsequently integrated (`52043693`; generated diagrams autoformatted at `33de7b4b`). **Current changes require their own new exact-head CI**, and native builds are *not* extracted frozen gameplay. Separate Vercel API/web commit statuses still show provider build-rate-limit failures; required-protection relevance is unresolved.

## Remaining critical path (issue → evidence required)

1. **T08 / #438 — IMPLEMENTED and independently integrated; final certification OPEN.** Versioned draw offers/acceptance/refusal, current and prospective named claims, full legal intended-move selection, replay and actual GUI test suite integrated at `1ddc4f99fe2cdba63f7ffcfdf335b692c23ecafa`; candidate Python 3.10–3.13 and real Tk/Xvfb green. Exact combined-head CI, final GUI verification and FIDE arbiter-procedure scope remain open. Temporary PR #461 closed unmerged; implementation task branch is being pruned after exact blob verification.
2. **T09 / #439 — implementation INTEGRATED; final acceptance pending.** Three-file persistence/security/restart patch from Dispatch B is in #271. Confirm full exact-head Python 3.10–3.13, Xvfb, four native packaging jobs, and separately #443 actual extracted-application save/restart. Do not close before evidence; #438 remains the exclusive session/UI owner.
3. **T06/T07 / #436, #437, #449 — rulebook completion.** Independently certify FIDE 50/75 boundaries, dead/timeout mating potential and newly integrated intended-claim UI; certify WCDF draw agreements/claims against the actual GUI. Explicitly record FIDE Article 9.5.3 arbiter-mediated incorrect-claim sanctions outside dispatched atomic-rejection model. Mark game definitions playable only after all intended full-game gates.
4. **T11 / #441, #452 → #453 → #454 — serial GUI owner.** Shared #438 draw-view implementation now integrated, so #452 can begin against live #271 HEAD. Pointer capture/promotion variants and piece/highlight clarity, then quests/history/player scrolling, finally native ttk/dialog/settings polish and visual review. Keep any #438 corrective work isolated from #452's GUI ownership.
5. **T10/T12 / #440, #442, #450 — evidence-backed quality and test modernization.** Audit-derived dead/duplicate path cleanup only after engine stabilizes; test-by-test RETAIN/ADAPT/REPLACE/DELETE and independently sourced real-session/GUI security tests. Do not mass-delete useful tests or add self-oracle checks.
6. **T13 / #443 — four-OS extracted frozen app acceptance.** Actual pointer gameplay, save/reopen/restart, clock/claim/dialog/terminal, version/hash/source and OS screenshots. Packaging and frozen `--check` alone are insufficient.
7. **T14 / #444 — independent exact-SHA final audit.** Inspect source, docs, semantic rules, reliability, hostile input, screenshots, real binaries, mandatory checks, review state and known limitations. Fix every blocking issue in a bounded task.
8. **T15 / #445 — explicitly authorized promotion/publication.** Obtain maintainer native approval of final #271 SHA before merging to `develop`; separately approve reviewed `develop → main`; verify PrideVer v1.0.0 tag, four public archives and checksums, and real use. No self-merge or unattended auto-approval.

## Ownership and integration discipline

Each writer starts from **live #271 HEAD**, uses a separate named branch/worktree, owns disjoint production paths and unique tests, and returns an exact SHA, complete diff, executed commands/results and blocked checks. The orchestrator independently reviews and integrates acceptable changes into the existing bot-authored PR #271. Verification-only branches/workflows are **not** product code. Agent-issued tasks are **not** executed until an agent actually receives them.

Keep `.agents/GOAL.md`, this plan, `.agents/TODO.md`, `.agents/SCRATCHPAD.md`, current-state source records and generated projections aligned after integrations. The exact V2 future API/DB/DSL contract stays only in #348; source documents describe implementation, not targets.
