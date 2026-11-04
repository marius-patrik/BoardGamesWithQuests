# BoardGamesWithQuests v1.0.0 — finite manual-dispatch queue

**Canonical plan:** [PLAN.md](PLAN.md). **Source authority:** [GOAL.md](GOAL.md), issue #430. **No DarkFactory issue-agent runs.** User manually dispatches copyable prompts from ChatGPT. Do not create duplicate dispatch issues. Product integration is PR #271; v2 only #348.

## Active manual prompts, in order

- [ ] **A / #443 native** — user launches one isolated QA writer on `qa/443-final-data-acceptance` at last SHA `1e49fa588732a8ec307cc8332272b27398ed7b2a`. Fix reproduced Mac OS overwrite-dialog automation and finish J1–J8 with four-platform per-journey evidence. No production source writes.
- [ ] **B / #437 WCDF** — independently verify actual bundled complete game, capture chains/crown, draw claims, replay, GUI; read-only initially, narrow patch only after failing external oracle.
- [ ] **C / #473 + #477 + #436 Chess** — independently reproduce dead/live FIDE defect; choose sound checkable proof/witness/UNKNOWN method and approved minimal pending/timeout policy if required. Small scoped code patch only after decision, never a new engine.
- [ ] **D / #438 + #439** — verify clocks/quests/terminal and saved game/security against exact integrated source and native QA; fix only actual defects.
- [ ] **E / #441** — real Tk final screenshots, select/claim/promotion/quests/history/layout/dialog/resize, targeted UI repairs only.
- [ ] **F / #440 + #442** — one final targeted code-quality owner, then independent suite deduplication/coverage owner; preserve all acceptance.
- [ ] **G / #462 + #476** — five open maintainer inline threads, final flat paths/packaging, correct docs source and actual default-branch Docs Deployment. No fake resolution.
- [ ] **H / #444** — one independent exact-SHA final GO audit after A–G.
- [ ] **I / #445** — separately approved `#271→develop→main` release, PrideVer v1.0.0 and verified four public binaries.
- [ ] **J / #445** — AFTER release: preserve v2 history/rebase, close v2 draft PR #422 unmerged, delete old v1 branches safely, close all v1/ops issues; leave only `main`, `develop`, `feat/independent-server-web-native-bootstrap` and sole OPEN issue #348.

## Verified starting evidence (not release certification)

- PR #271 pre-plan commit `a752a82bafc5d2ae0ef0a7710811fcd7815f2112`, ten applicable workflows PASS, including four **package** jobs. No final extracted-app J1–J8 evidence.
- Native QA `1e49fa5`, [#41625407817](https://github.com/marius-patrik/BoardGamesWithQuests/actions/runs/41625407817): Windows/Linux internal BLOCKED unfinished advanced scenarios, Mac ARM64/x64 internal BLOCKED native overwrite control. No current four-OS pass.
- Chess #473 known FIDE timeout failure Buchanan dead fortress, near-twin mate possible; no accepted proof fix. Both JSON definitions `playable:false`, PrideVer Python publishing disabled.
- #437 WCDF source already implemented, prospective draw GUI present. #441 UX source already substantially integrated. #438 draw/clocks source integrated and #439 persistence hardening integrated; final acceptance only.
- Duplicate issues **CLOSED and linked**: #489→#443, #490/#449→#437, #491→#473, #492→#477, #450→#442, #454→#441, #429/#487→#488; #488 closed not planned because no approved DarkFactory fleet upgrade. #476 remains distinct unverified deployment failure.
- Current draft v2 PR #422 depends on `feature/product-integration`; final cleanup must preserve v2 changes before removing v1 integration branch. **Do not delete any branches before accepted evidence/release.**

**Manual agent final handoff:** actual baseline/full final SHA, changed files, exact executable tests, independent outcomes, screenshots/logs if native, blocked/failed cases and recommendation. Orchestrator verifies accepted work; no task passes on generic agent summary alone.
