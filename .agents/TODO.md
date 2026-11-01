# Current action queue — BoardGamesWithQuests v1.0.0

**Canonical complete execution order and acceptance gates:** [PLAN.md](PLAN.md). Product contract: [GOAL.md](GOAL.md). Master issue: #430. Single integration: draft PR #271. **Release NO-GO.**

## Immediate — W1, sole structure/resource writer (#462)

- [ ] From current #271 head, implement the last three explicit maintainer review changes: move resources to data/chess.json + data/checkers.json, remove games subfolders/namespace; rename src/boardgameswithquests.py -> src/main.py while preserving installed boardgameswithquests command.
- [ ] Update resource discovery/validation, pyproject, native package+manifest, installed distribution tests, all source tests and generated docs. Keep Chess/Draughts JSON semantically identical.
- [ ] Verify the old games initializer is removed and screen.py is the one GameScreen composition (two already substantially addressed PR review threads).
- [ ] Prove Python 3.10–3.13, real Tk, clean editable/wheel/sdist **outside checkout**, four native packaging/frozen --check, exact candidate and combined-head CI; independent maintainer resolves all 5 PR #271 threads; close #462.
- [ ] Do **not** edit native #443 QA branch concurrently. Preserve its current work for one rebase/port after source layout is final.

## After W1 — execute on final source

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