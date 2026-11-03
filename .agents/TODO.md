# Current action queue — BoardGamesWithQuests v1.0.0

**Canonical complete execution order and acceptance gates:** [PLAN.md](PLAN.md). Product contract: [GOAL.md](GOAL.md). Master issue: #430. Single integration: draft PR #271. **Release NO-GO.**

## W1 — SOURCE DONE; human review still open (#462)

- [x] Canonical `data/chess.json`, `data/checkers.json`, `src/main.py` layout; byte-identical game JSON, resource resolver, setuptools and native packaging migrated.
- [x] Candidate acceptance and **exact merged PR #271 HEAD `a117efaba454433b1caa19607fd45498178f9933`** passed all 9 workflows (full Python 3.10–3.13, real Tk, clean editable/wheel/sdist, four native PACKAGE builds).
- [x] Old source initializer gone; single `GameScreen` composition preserved.
- [ ] **Maintainer-only gate:** inspect/accept and resolve the five original PR #271 review threads; close #462 when accepted. Do not falsely mark review complete.

## W2 — ACTIVE extracted-native acceptance (#443)

- [x] Recovered the 1,913-line four-platform frozen GUI harness on isolated `qa/443-final-data-acceptance`, adapted to flat `data/` and `src/main.py`, with native manifests, macOS ad-hoc re-sealing and fail-closed result JSON.
- [x] Inspected **completed** exact run [#41512854619](https://github.com/marius-patrik/BoardGamesWithQuests/actions/runs/41512854619), SHA `3aed0dc43d2c72ac7f7e560ec1c8e1ceaf024d0f`: Windows/Linux BLOCKED for mandatory unfinished journeys; macOS ARM64/x64 FAIL when readonly-save overwrite confirmation remained visible despite Return. All four passed earlier implemented game captures, preferences, lifecycle and both game save→restart→open→continue; macOS failed late, during failure recovery.
- [x] Produced narrow QA-only macOS Accessibility Replace correction on same branch at `1e49fa588732a8ec307cc8332272b27398ed7b2a`. New exact-head [native CI #41625407817](https://github.com/marius-patrik/BoardGamesWithQuests/actions/runs/41625407817) **QUEUED at checkpoint**; candidate is not accepted or integrated.
- [ ] Inspect #41625407817 all four job logs and native-result/screenshots, confirm the overwrite confirmation closes and original read-only file stays intact; correct remaining confirmed failures on the same QA branch.
- [ ] Implement and verify all missing J1–J8 advanced native journeys without skip/waiver, with WIN/macOS ARM64/macOS x64/Linux exact-SHA evidence; document Windows signing, Apple Developer ID, notarization, Gatekeeper and distribution-policy dependencies separately.
- [ ] Only after independent full QA acceptance, selectively integrate into existing draft PR #271 and rerun exact combined-head checks.

## Remaining fixed release gates — after W1

- [ ] **W2 native #443:** port recovered qa/443-n1b-macos-recovery test/workflow, diagnose run #41304444805 ARM64 board visibility and x64 unchanged chess persisted move, then pass native J1–J8 on Windows/macOS ARM64/macOS x64/Linux extracted apps on the same exact SHA. Signing trust status truthful.
- [ ] **W3 WCDF #437/#449:** independently confirm 91-ply full game, legal routes, crowning, 40-move/threefold and all terminal claims, complete session/GUI paths; enable checkers playable only after passing.
- [ ] **W4 Chess #477/#473/#436:** review/approve full durable pending-timeout design; sound checkable mate possibility/impossibility (Buchanan dead/live adversarial cases), safe unknown resolution, persistence/replay; enable chess playable only after complete FIDE correctness. If mathematically infeasible under v1 domain, release remains blocked; no deceptive shortcut.
- [ ] **W5 quality/test #440/#442/#450:** concrete P0/P1 code cleanup and behavior-by-behavior test replacement, no general refactor or removing tests before replacement proof.
- [ ] **W6 GUI/review #454/#462:** final real screenshot visual signoff and all PR threads resolved.
- [ ] **W7 audit #444:** one final exact-SHA independent GO report, full four-OS evidence matrix.
- [ ] **W8 release #445:** maintainer-approved PR #271 -> develop; second reviewed develop -> main; PrideVer-enable only with authorization; publish and independently verify four downloadable v1.0.0 archives, hashes and source SHA.

## Current independently verified facts (2026-11-01)

- PR #271 source SHA before this planning commit: f685c6b276fa015749550c62c65fd97a1a6f2d13, 9/9 applicable CI workflows green; **not** full frozen native acceptance.
- Five PR #271 review threads unresolved; latest maintainer requests supersede the earlier games/ / boardgameswithquests.py refactor layout.
- #443 exact isolated N1B native run #41304444805: Windows/Linux BLOCKED (explicit incomplete gate), macOS ARM64 FAIL board observation, macOS x64 FAIL chess persisted move not visibly changing square (6,4).
- Chess #473/#477 still has a known FIDE dead-position/timeout correctness blocker. WCDF #437/#449 requires final independent certification.
- Both bundled configurations currently have playable: false; Python release publication is disabled.
- No protected branch changes or release authorization implied by updating these records.

**Execution rule:** Complete the next bounded work package with actual code+tests+evidence and independently integrate it, rather than generating another broad agent plan.