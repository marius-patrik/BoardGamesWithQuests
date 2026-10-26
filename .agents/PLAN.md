# Execution plan — BoardGamesWithQuests v1.0.0

**Last orchestration reconciliation:** 2026-10-26. **Canonical release contract:** [#430](https://github.com/marius-patrik/BoardGamesWithQuests/issues/430). Detailed acceptance belongs in each child issue; this file owns **sequence and active dependencies**, not another specification. One bot-authored draft desktop PR, [#271](https://github.com/marius-patrik/BoardGamesWithQuests/pull/271), targets protected `develop`. The downstream draft [#422](https://github.com/marius-patrik/BoardGamesWithQuests/pull/422) and proposed [v2 design #348](https://github.com/marius-patrik/BoardGamesWithQuests/issues/348) are **deferred until v1.0.0 is published and verified**.

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
- [x] Independently executed Chess reference candidate #436 (26 reference scenarios plus 99 affected regressions on Python 3.10–3.13); complete exceptional FIDE certification still **OPEN**.
- [x] Independently executed and integrated #437/#449 WCDF short-king, deferred captures, claim configuration and 91-ply referenced game; complete pointer-UI certification still **OPEN**.
- [x] Last **code baseline** `1f6816da13e9d3f73f450c1e2bf8635fe12db860`: eight PR-triggered GitHub Actions workflows completed with success, including Python matrix, Xvfb and all four native **package builds**. This is **not** frozen interactive acceptance. Independent Vercel API/web commit statuses show failure from provider build-rate-limits; whether required for protected integration must be checked. Any subsequent commit requires exact-new-HEAD verification.

## Remaining critical path (issue → evidence required)

1. **T08 / #438 — shared draw and lifecycle owner.** Implement revisioned two-participant draw offer/accept/reject and full legal intended-move claim selection, including cancellation, authorization, clocks/quests, replay and actual GUI. Only this task may edit shared engine/claim-view files while active.
2. **T09 / #439 — concurrent isolated persistence owner.** Verify/fix atomic preferences and saved-game JSON, hostile paths, process restart and non-destructive failed import. No concurrent view/session/manager writes with #438.
3. **T06/T07 / #436, #437, #449 — rulebook completion.** FIDE 50/75 boundaries, dead/timeout mating potential and intended-claim cases; real WCDF claim/agreement route and complete acceptance; mark game definitions playable only after the appropriate full-game gates.
4. **T11 / #441, #452 → #453 → #454 — serial GUI owner.** Pointer capture/promotion variants and piece/highlight clarity; all quests/history/player scrolling; native ttk/dialog/settings polish and visual review. Avoid overlapping `player_game_view.py` edits with #438.
5. **T10/T12 / #440, #442, #450 — evidence-backed quality and test modernization.** Audit-derived dead/duplicate path cleanup only after engine stabilizes; test-by-test RETAIN/ADAPT/REPLACE/DELETE and independently sourced real-session/GUI security tests. Do not mass-delete useful tests or add self-oracle checks.
6. **T13 / #443 — four-OS extracted frozen app acceptance.** Actual pointer gameplay, save/reopen/restart, clock/claim/dialog/terminal, version/hash/source and OS screenshots. Packaging and frozen `--check` alone are insufficient.
7. **T14 / #444 — independent exact-SHA final audit.** Inspect source, docs, semantic rules, reliability, hostile input, screenshots, real binaries, mandatory checks, review state and known limitations. Fix every blocking issue in a bounded task.
8. **T15 / #445 — explicitly authorized promotion/publication.** Obtain maintainer native approval of final #271 SHA before merging to `develop`; separately approve reviewed `develop → main`; verify PrideVer v1.0.0 tag, four public archives and checksums, and real use. No self-merge or unattended auto-approval.

## Ownership and integration discipline

Each writer starts from **live #271 HEAD**, uses a separate named branch/worktree, owns disjoint production paths and unique tests, and returns an exact SHA, complete diff, executed commands/results and blocked checks. The orchestrator independently reviews and integrates acceptable changes into the existing bot-authored PR #271. Verification-only branches/workflows are **not** product code. Agent-issued tasks are **not** executed until an agent actually receives them.

Keep `.agents/GOAL.md`, this plan, `.agents/TODO.md`, `.agents/SCRATCHPAD.md`, current-state source records and generated projections aligned after integrations. The exact V2 future API/DB/DSL contract stays only in #348; source documents describe implementation, not targets.
