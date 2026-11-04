# BoardGamesWithQuests v1.0.0 — current dispatch and execution queue

**Checkpoint:** 2026-11-04. **Status:** NO-GO. **Authority:** [GOAL.md](GOAL.md), [PLAN.md](PLAN.md), [#430](https://github.com/marius-patrik/BoardGamesWithQuests/issues/430). Product is draft [PR #271](https://github.com/marius-patrik/BoardGamesWithQuests/pull/271), `feature/product-integration` at `41f15fd86d301026a34cd5e2ad172cfc2e44a258` before this planning update; no protected merge/public release.

## Immediate dispatch wave (one writer + independent read-only agents)

- [ ] **N / native #443, implementation agent:** issue-bound dispatch to existing `qa/443-final-data-acceptance` at `1e49fa588732a8ec307cc8332272b27398ed7b2a`. Latest actual [#41625407817](https://github.com/marius-patrik/BoardGamesWithQuests/actions/runs/41625407817) **FAIL** at workflow level; machine results: **Windows/Linux BLOCKED** by intentionally unimplemented advanced journeys; **macOS ARM64/x64 BLOCKED** at readonly-save step because AX `Replace` button was not exposed. Fix from screenshot/AX evidence; finish J1–J8 without bypass. No `src/` or `data/` edits.
- [ ] **D / WCDF #437/#449/#438, independent read-only agent:** certify complete bundled rules and public session/UI using 91-ply reference, full terminal game, captures, crown, 40-move/threefold intended move, idempotency/replay. Report FAIL examples, no speculative code.
- [ ] **C / FIDE #473/#477/#436, independent read-only agent:** evaluate sound impossibility/witness feasibility, Buchanan dead/live, deterministic UNKNOWN, full durable pending-timeout contract, migration, UI/replay. Produce explicit decision sheet; do NOT implement before policy approval.
- [ ] **Q / test & quality #440/#442/#450:** inventory final acceptance tests, code-quality P0/P1 and finite retain/fix/replace/delete dossier. Read-only until game/native source stabilized.
- [ ] **R / final review #441/#454/#462/#476:** maintainer thread dispositions, genuine GUI screenshots, stale source-generated README and docs-deploy evidence; signing/Apple notarization credentials/policy inventory. Read-only until integration.

## Integration and release gates

- [x] W1 source refactor committed: `data/chess.json`, `data/checkers.json`, `src/main.py`; SHA `a117efab` exact 9/9 original applicable checks PASS. Source layout changes integrated.
- [ ] W1 human review: resolve exactly **five** #271 outstanding inline threads after independent maintainer approval.
- [ ] N #443: 4/4 extracted OS **J1–J8 PASS on a single SHA**, with native result JSON + PNG + app/log + artifact provenance; reconcile signing/notarization policy. Package build does not count.
- [ ] D #437/#449/#438: complete WCDF certification, including actual GUI prospective claim; only then `checkers.playable:true`.
- [ ] C #477: maintainer-approved pending timeout/durability/authority/migration contract.
- [ ] C #473/#436: sound proof/evaluator with safe UNKNOWN, Buchanan dead/live, FIDE rulebook acceptance; only then `chess.playable:true`.
- [ ] Q #440/#442/#450: evidenced P0/P1 cleanup and independent oracle tests, no degraded coverage.
- [ ] R #439/#441/#454/#462/#476: final OS user-data, GUI review, 5 threads, docs/build corrections and dispositions.
- [ ] Exact combined PR #271: full Python 3.10–3.13, clean installed tests, actual Tk, packaging and extracted Windows/macOS ARM64/macOS x64/Linux J1–J8, source-generated docs/diagrams/governance, replay/rollback/security all green on one final SHA.
- [ ] #444 independent release audit GO for exact combined SHA. If FAIL, fix only proven owner defect and re-verify.
- [ ] #445 maintainer approves #271 → `develop`; separately reviews and approves `develop` → `main`, authorizes PrideVer v1.0.0. Independently verify 4 downloadable archives + SHA256, integrity, real play and truthful signing status; close #430 only after all evidence.

## Known live run status and ownership rules

- `feature/product-integration` exact run [#41625688688](https://github.com/marius-patrik/BoardGamesWithQuests/actions/runs/41625688688): native **package workflow failed/cancelled** (macOS ARM64 cancelled; other three jobs passed), despite nine other integration workflows green. NOT full native acceptance.
- Native `qa/443-final-data-acceptance` run [#41625407817](https://github.com/marius-patrik/BoardGamesWithQuests/actions/runs/41625407817): 4 job failures; **Windows/Linux internal classification BLOCKED** after all implemented journeys PASS, **both macOS internal classification BLOCKED** at OS Replace control; all advanced journeys remain NOT EXECUTED. Previous source fix `1e49fa5` did not clear the OS Accessibility requirement.
- Chess Buchanan dead-fortress timeout remains a confirmed wrong win, with independently referenced mating-possible near-twin; no verified sound solution exists.
- Both shipped definitions `playable:false`, `repo.dfconfig` publication disabled, v2 #422 deferred.
- Exclusive writer lock: only lane N touches native harness/workflows; D/C/Q/R evidence read-only concurrently. A shared `src/model/`, `data/` or `src/view/` writer starts only after orchestrator grants ownership against the latest accepted integration SHA.
- **Dispatch labels/comments alone are not execution evidence.** Verify downstream worker result. No auto-merge, protected-branch writes, release, arbitrary fixed ETA or weakening mandatory tests.

**Next checkpoint:** verify issue-bound agent launch and compare its exact committed SHA and four-platform artifacts; do not repeat another broad orientation.
