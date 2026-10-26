## v1 release scope refinement — 2026-10-26

Maintainer decided **keyboard-controlled board play is not needed for v1**. [#448](https://github.com/marius-patrik/BoardGamesWithQuests/issues/448) is closed `not_planned`; cancel dispatch 04A and do not make it a release prerequisite. Continue with existing pointer-operated board and normal Tk buttons/dialogs. Do not claim keyboard-only board accessibility. Original #435 audit remains evidence of the deferred limitation.

**Run dispatch 04B [#456](https://github.com/marius-patrik/BoardGamesWithQuests/issues/456)** for aggregate evaluator budget correctness and late-proposal rollback. If another independent GUI agent is available, start [#451](https://github.com/marius-patrik/BoardGamesWithQuests/issues/451) on disjoint view-owned files. Then rulebook completion #436–#438/#449, UI #452–#454, source/test/persistence QA #439/#440/#442/#450, actual frozen four-OS use #443, final approval #444 and publishing #445. Avoid optional features, unnecessary test churn and blind engine/GUI rewrite.

---

## Implementation status — 2026-10-26

**Current PR #271 source HEAD at this update:** `dfb35fb3e1a1f4cb42fc5889c79c4dda3162e67e` (draft; not merged). **#431**, **#446** and **#447** are **closed after exact-head integration and verification**. All four audit issues #432–#435 are closed; investigations are complete, not the resulting development.

- **#431:** generic timeout actor binding and WCDF terminal precedence corrected, integrated and Python 3.10–3.13 + real Tkinter/Xvfb CI green.
- **#446:** removed the shadowed unmetered `ConditionEvaluator._equal`; independently executed before/after budget tests, all affected Python versions and both games passed. **Remaining** halfmove/quest/claim evaluator paths without aggregate work bindings have a concrete separate corrective contract [#456](https://github.com/marius-patrik/BoardGamesWithQuests/issues/456) and must be verified including rollback after partial proposed mutation.
- **#447:** preserved Canvas, added adaptive compact window/board sizing, toolbar, player clocks and scrollable panels. Actual Linux/Xvfb screenshot evidence under `.github/tests/evidence/ux447/`; 20 real Tkinter tests passed on exact integrated head. This is **not** complete visual polish; [#448](https://github.com/marius-patrik/BoardGamesWithQuests/issues/448) keyboard board mode is deferred, continue with #451–#454 sequentially.
- **Exact-head CI:** [Desktop gameplay 40293032053](https://github.com/marius-patrik/BoardGamesWithQuests/actions/runs/40293032053), [governed Python quality 40293032351](https://github.com/marius-patrik/BoardGamesWithQuests/actions/runs/40293032351), [native packaging 40293031824](https://github.com/marius-patrik/BoardGamesWithQuests/actions/runs/40293031824), governance all passed on the code SHA above. Package **build/smoke** is not real extracted Windows/macOS/Linux GUI/gameplay acceptance (#443).
- **Next required work:** #456 owns engine manager/hook evaluation files; GUI #451 can run in parallel on separate view/controller files. **#448 keyboard board mode is not planned for v1.** Keep isolated branches and exclusive writers. Source cleanup and full FIDE/WCDF reference verification remain separate #436–#440/#449/#450, independently reviewed before integration.

**Docs-only edit caveat:** this PLAN/TODO synchronization changes the PR commit, so prior CI evidence applies to the *code SHA above*; re-run and verify all required checks on the new docs HEAD before next integration. Do not publish/merge without maintainer approval.

---

# Plan — Python/Tkinter v1.0.0

**Canonical release epic:** [#430](https://github.com/marius-patrik/BoardGamesWithQuests/issues/430). **Exact, scoped task contracts:** [#431–#445](https://github.com/marius-patrik/BoardGamesWithQuests/issues/430). **Bot-authored integration PR:** [#271](https://github.com/marius-patrik/BoardGamesWithQuests/pull/271) → `develop`. **Release:** independently approved `develop → main` → PrideVer v1.0.0. **Future multiplayer v2:** [issue #348](https://github.com/marius-patrik/BoardGamesWithQuests/issues/348) / deferred PR #422.

The implementation baseline is the **existing playable Tkinter GUI** and the substantially recovered historical JSON game engine, now integrated as `src/model/game/manager.py` + `DesktopSession`. Complete and refine this code **in place**, never reconstruct it. The final product must be clean/readable (no dead, duplicate or historical compatibility paths), rulebook-correct, visually polished and actually downloadable/playable as frozen Windows/macOS/Linux apps. Expanded exports and server/database/web/Tauri are outside the v1 scope.

**Contract precedence:** issue #430 is the integrated product/release definition of done. Its child issues own exact methods, file scopes, dependencies and behavioral acceptance. This PLAN records phase sequencing/current work, not a second implementation spec. The actual committed code/accepted decisions remain the authority for shipped behavior; issue #348 holds desired v2 contracts only.

## Scope, critical dependencies and current queue

| Gate | Scoped issue | Work | Dependency / permitted overlap |
|---|---|---|---|
| A1 | [#431](https://github.com/marius-patrik/BoardGamesWithQuests/issues/431) | **Correct timeout semantics and integrate** | **DONE** — integrated at `43fa5dd`; source quality/CI passed |
| A2 | [#432](https://github.com/marius-patrik/BoardGamesWithQuests/issues/432) | Test/CI inventory and authoritative acceptance design | Completed read-only audit; #450 implements |
| A3 | [#433](https://github.com/marius-patrik/BoardGamesWithQuests/issues/433) | Whole-source code quality, dead/duplicate architecture audit | Completed read-only audit; #446 then #440 |
| A4 | [#434](https://github.com/marius-patrik/BoardGamesWithQuests/issues/434) | FIDE/WCDF gameplay correctness + historical feature parity audit | Completed read-only audit; #449/#436–#438 |
| A5 | [#435](https://github.com/marius-patrik/BoardGamesWithQuests/issues/435) | Live Tkinter UX audit and concrete polish specification | Completed; 13 Linux frozen screenshots reviewed, six UX subissues |
| B1 | [#436](https://github.com/marius-patrik/BoardGamesWithQuests/issues/436) | Chess reference games and rulebook completion | After #431/#434; only one shared engine writer |
| B2 | [#437](https://github.com/marius-patrik/BoardGamesWithQuests/issues/437) | English Draughts reference games and rulebook completion | After #431/#434; serialize shared changes with B1 |
| B3 | [#438](https://github.com/marius-patrik/BoardGamesWithQuests/issues/438) | Clocks, quests, terminal/session lifecycle | After stable game rulebooks and audits |
| B4 | [#439](https://github.com/marius-patrik/BoardGamesWithQuests/issues/439) | Local settings, saved game, restart and security hardening | After #431/#432; coordinate any view changes with C2 |
| C1 | [#440](https://github.com/marius-patrik/BoardGamesWithQuests/issues/440) | Minimal evidence-backed production-code cleanup | After #433 and stabilized shared engine; no large blind rewrite |
| C2 | [#441](https://github.com/marius-patrik/BoardGamesWithQuests/issues/441) | **Polish the existing Tkinter GUI**, screenshot/interaction-verified | After #435; stable local-session contract; nonoverlap with C1 |
| C3 | [#442](https://github.com/marius-patrik/BoardGamesWithQuests/issues/442) | Replace weak tests with supported behavioral suites | After #432, coordinate with game/UI writers; no premature deletion |
| D1 | [#443](https://github.com/marius-patrik/BoardGamesWithQuests/issues/443) | Actual four-platform **extracted frozen executable** acceptance | After final GUI/QA/persistence; source-run startup alone not enough |
| D2 | [#444](https://github.com/marius-patrik/BoardGamesWithQuests/issues/444) | Independent exact-head code/UX/security/docs/CI/release audit | After integrated A–D1; blocked gaps become precise fix tasks |
| R | [#445](https://github.com/marius-patrik/BoardGamesWithQuests/issues/445) | Maintainer-approved integration, protected promotion, release publication and verification | Only after #444 PASS + explicit approval at each gate |

## Audit intake — 2026-10-23 (reports, not implemented work)

- Read-only **#432 test audit** received: 154 named Python tests/23 modules; retain useful real-session, GUI, security, governance and docs evidence, replace weak internal/self-oracle tests through [#450](https://github.com/marius-patrik/BoardGamesWithQuests/issues/450) under #442 without mass deleting first.
- Read-only **#433 code-quality audit** received: 26 findings, including verified shadowed `ConditionEvaluator._equal` that bypasses recursive work charging. Completed targeted [#446](https://github.com/marius-patrik/BoardGamesWithQuests/issues/446); remaining manager/hook budget paths are [#456](https://github.com/marius-patrik/BoardGamesWithQuests/issues/456); broader dead-code, duplication, snapshot and query optimizations remain measured/serialized under #440.
- Read-only **#434 gameplay audit** received: investigate WCDF capture-removal policy, repetition and progress claims via [#449](https://github.com/marius-patrik/BoardGamesWithQuests/issues/449); #436/#438 own complete Chess and generic draw/clock/quest semantics. Keep source-backed, full-rulebook acceptance and immutable configurations.
- Read-only **#435 full frozen Linux GUI audit received and independently inspected**: 41,761-byte Markdown, 13 screenshots, all 26 indexed findings in closed issue #435. Release-blocking board/actions clipping at 840×640; missing board keyboard focus; unsafe game-switch lifecycle, incomplete result and sidebar. Responsive layout [#447](https://github.com/marius-patrik/BoardGamesWithQuests/issues/447) now completed; [#448](https://github.com/marius-patrik/BoardGamesWithQuests/issues/448) intentionally deferred, continue sequential [#451](https://github.com/marius-patrik/BoardGamesWithQuests/issues/451) lifecycle/terminal/status → [#452](https://github.com/marius-patrik/BoardGamesWithQuests/issues/452) board piece/choice → [#453](https://github.com/marius-patrik/BoardGamesWithQuests/issues/453) quest/history/sidebar → [#454](https://github.com/marius-patrik/BoardGamesWithQuests/issues/454) dialogs/ttk/style/refresh. One view writer at a time. Linux screenshot evidence is **not** Windows/macOS acceptance.
- #431 terminal patch has already passed 1 original regression + 128 affected tests on each Python 3.10–3.13, plus 11 real Tkinter/Xvfb tests, in isolated [CI run 39936337058](https://github.com/marius-patrik/BoardGamesWithQuests/actions/runs/39936337058). It is integrated into #271 and passed exact integrated-head acceptance. No verification-only workflow was imported.

All four read-only audits #432–#435 are **closed as completed investigations**, not as implementation proof. The full #435 archive was received and inspected on 2026-10-25. No audits changed production source or completed v1 acceptance. Agents must not infer that issue creation itself dispatched any work.

## Current blocking correction

Agent Dispatch 01 committed `fix/430-terminal-outcome-correctness` at `0377a4ee9ebf5a14e1991a88203841e82f89abc0` against #271 baseline `daf90e8e1c1568a3f9718c2bd908c52b51622234`. Candidate changes English-draughts no-legal-moves outcome to match ordinary move events, binds timeout actor to expired active participant, and adds terminal regressions. The original test did not run on the first agent's final candidate initially, but isolated CI subsequently passed, and the correction is **now integrated and exact-head tested**. Do not substitute source inspection or format for runtime evidence.

## Test migration and final evidence

- [#432] inventories **every** existing `.github/tests/` case as retain/adapt/replace/delete and maps meaningful behavior to independent rulebook/perft/full-game, public DesktopSession, live Tkinter/Xvfb, restart/hostile input and **native frozen GUI** acceptance.
- [#442] systematically replaces non-proving private implementation tests as equivalent stronger boundary coverage lands, rather than deleting all tests or stacking redundant suites. Keep narrowly justified pure-math/validator diagnostics supplementary.
- Required display/provider/native tests are **FAIL/BLOCKED**, not secretly skipped. Only actual executed tests on the exact target SHA and host can count as passing. Run targeted tests while implementing; run Python 3.10–3.13 and the full real-GUI/native gates at final release.
- Four target platforms are Windows x64, macOS ARM64, macOS x64 and Linux x64. Verify actual extracted frozen apps, game interaction, preferences, restart/shutdown, resources, hashes, PrideVer metadata and publishability. Do not mistake `--check` or a five-second process survival for a playable application.

## Orchestration policy

- Issue-owned scoped agents: one objective, exact base SHA, owned paths, pass criteria and structured handoff. Separate read-only audits from writers, isolate write branches/worktrees and never overwrite a concurrently changing #271 head. Serialized ownership for game engine and JSON.
- The existing DarkFactory workflow is **not** confirmed to accept task-specific ad hoc dispatch; [DarkFactory #2694](https://github.com/marius-patrik/DarkFactory/issues/2694) requests that feature. Filing issues is not dispatching agents or running tests.
- Orchestrator independently validates each candidate, reconciles integration and updates this PLAN/TODO as status changes. No external reviewer can self-approve, merge PR #271, change protected `main`, enable publication or publish a release.
- Current-state docs, diagram sources/outputs, test paths and active rules must remain true to *committed code in the same PR*; prospective v2 content stays in issue #348.

**Completion:** publicly published v1.0.0, four verified downloadable and playable packages, exact correct source/tag/hash and required independent maintainer approvals. A merged #271 alone does not finish the project.
