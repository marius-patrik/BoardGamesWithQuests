# Plan — Python/Tkinter v1.0.0

**Canonical release epic:** [#430](https://github.com/marius-patrik/BoardGamesWithQuests/issues/430). **Exact, scoped task contracts:** [#431–#445](https://github.com/marius-patrik/BoardGamesWithQuests/issues/430). **Bot-authored integration PR:** [#271](https://github.com/marius-patrik/BoardGamesWithQuests/pull/271) → `develop`. **Release:** independently approved `develop → main` → PrideVer v1.0.0. **Future multiplayer v2:** [issue #348](https://github.com/marius-patrik/BoardGamesWithQuests/issues/348) / deferred PR #422.

The implementation baseline is the **existing playable Tkinter GUI** and the substantially recovered historical JSON game engine, now integrated as `src/model/game/manager.py` + `DesktopSession`. Complete and refine this code **in place**, never reconstruct it. The final product must be clean/readable (no dead, duplicate or historical compatibility paths), rulebook-correct, visually polished and actually downloadable/playable as frozen Windows/macOS/Linux apps. Expanded exports and server/database/web/Tauri are outside the v1 scope.

**Contract precedence:** issue #430 is the integrated product/release definition of done. Its child issues own exact methods, file scopes, dependencies and behavioral acceptance. This PLAN records phase sequencing/current work, not a second implementation spec. The actual committed code/accepted decisions remain the authority for shipped behavior; issue #348 holds desired v2 contracts only.

## Scope, critical dependencies and current queue

| Gate | Scoped issue | Work | Dependency / permitted overlap |
|---|---|---|---|
| A1 | [#431](https://github.com/marius-patrik/BoardGamesWithQuests/issues/431) | **Test and integrate isolated terminal patch** | Critical path; candidate `0377a4e` still **unverified** on pytest |
| A2 | [#432](https://github.com/marius-patrik/BoardGamesWithQuests/issues/432) | Test/CI inventory and authoritative acceptance design | Read-only; parallel with A1/A3/A4/A5 |
| A3 | [#433](https://github.com/marius-patrik/BoardGamesWithQuests/issues/433) | Whole-source code quality, dead/duplicate architecture audit | Read-only; parallel with A1/A2/A4/A5 |
| A4 | [#434](https://github.com/marius-patrik/BoardGamesWithQuests/issues/434) | FIDE/WCDF gameplay correctness + historical feature parity audit | Read-only; parallel with A1/A2/A3/A5 |
| A5 | [#435](https://github.com/marius-patrik/BoardGamesWithQuests/issues/435) | Live Tkinter UX audit and concrete polish specification | Read-only; real display evidence required or marked blocked |
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

## Current blocking correction

Agent Dispatch 01 committed `fix/430-terminal-outcome-correctness` at `0377a4ee9ebf5a14e1991a88203841e82f89abc0` against #271 baseline `daf90e8e1c1568a3f9718c2bd908c52b51622234`. Candidate changes English-draughts no-legal-moves outcome to match ordinary move events, binds timeout actor to expired active participant, and adds terminal regressions. **No pytest ran on the candidate.** The only reported successful check was formatting. Do not merge candidate into #271 or mark #431 complete until the real failing test, new regressions and supported Python matrix execute and pass. If CI execution is unavailable, preserve branch and report BLOCKED. Do not substitute source inspection or format for runtime evidence.

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
