# Plan — BoardGamesWithQuests v1.0.0

**Implementation authority:** [v1.0.0 issue #430](https://github.com/marius-patrik/BoardGamesWithQuests/issues/430). **Integration:** existing bot-authored [PR #271](https://github.com/marius-patrik/BoardGamesWithQuests/pull/271) → protected `develop`. **Release:** independent maintainer approval of `develop → main`, then PrideVer. **Future v2:** [issue #348](https://github.com/marius-patrik/BoardGamesWithQuests/issues/348) / deferred PR #422.

**Delivery condition:** Four real, independently verified, downloadable and playable desktop distributions; a merged PR alone is insufficient. Release publication stays disabled until approval and all release gates pass.

## Baseline — preserve actual recovered work

- The complete historical revisioned JSON `GameManager` from #405 has been substantially recovered into `src/model/game/manager.py` with conditions, hooks, queries, captures, events, replay, clocks, quests and outcomes. `DesktopSession` and current Tkinter controllers/views use it. **Do not rebuild an engine or GUI.**
- The original Tkinter board renderer and game-selection experience are retained; historical player/quest panels were adapted. Historical behavior must be audited for intentional differences versus regressions.
- Both bundled JSON definitions are present but still declare `playable: false`. Preserve that until independent complete-game and GUI release acceptance.
- Mandatory source-run Tkinter/Xvfb and native build jobs exist, but green native `--check`/startup is not proof of frozen GUI functionality.
- At the inspected v1 branch HEAD `41e4db90f301f3269c4543af05478193004ab6ae`, the four native jobs and real Tkinter acceptance passed; Python gameplay/quality failed on a draughts **timeout vs no_legal_moves terminal precedence** regression. Refresh exact-head evidence before any work.
- All historical #271 inline threads were reported resolved; final independent gameplay, architecture, usability and release review remains necessary.

## Task sequence and gates

### A — Stabilize gameplay correctness (first)

1. Reproduce and fix the terminal-precedence regression in the existing generic JSON engine/rulebook; verify explicit expiry, no legal moves, resignation, draw claims, retries, snapshots and atomic rollback. Never weaken the failing expectation to get green CI.
2. Independently verify standard Chess and WCDF English Draughts complete opening-to-terminal games, reference positions/perft, legal actions, special moves, draws and captures/crowning; no testing only partial recorded games called “complete.”
3. Verify clocks/increments and autonomous timeout, quests/one-time rewards, error paths, variable board shape, execution-budget failures, corrupt input, replay and secure local preferences.
4. Mark each definition `playable: true` only after real supported game and UI gates pass.

**Exit:** One production engine, two independently verified rulesets and fully green affected game behavior; no known correctness regressions.

### B — Deep code-quality and historical-parity review, then focused cleanup

1. Read every production module under `src/` and the two JSON definitions. Compare the original playable Tkinter tree `43a3d01fab45a305d02ef26a4f86f0e7cd9a0d96` and recovered JSON tree `6002ac787664efceb0161d2bcbd3891927b69b34` against the actual PR #271 head.
2. Inventory meaningful dead code, duplicate algorithms, unused aliases/compatibility, conflicting representations, misnamed responsibilities, unnecessary conversions, non-obvious complexity, unsafe filesystem paths and lost UI/game capabilities. Identify which historical features intentionally retired and which regressed. Check quest variety and default Fischer clocks explicitly.
3. Correct only validated problems; preserve working domain and GUI architecture, remove retired paths without legacy shims. A large manager or JSON rulebook is not itself a defect—split only on a real cohesive boundary that improves comprehension and verification.
4. Review performance where observed (legal generation, query recursion, snapshot copying, GUI refresh); keep deterministic bounded execution and a single authoritative state owner.
5. Keep source-governed decisions/docs and generated diagrams accurate in the **same** implementation changes. No proposed v2 contracts in tracked files.

**Exit:** Cohesive, maintainable source, zero unjustified parallel implementations, no unused historical production paths, no demonstrated behavior regressions.

### C — Polish the existing Tkinter UX (not a rewrite)

1. Capture actual before-state screenshots and run existing UI to identify concrete visual and interaction defects.
2. Improve ttk visual system, text hierarchy, spacing, board/piece/target rendering, window resize/DPI behavior, player/quest/history panels, clock/turn/outcome feedback, discoverability, input dialogs, keyboard and accessible focus, game reset/switch and clean shutdown.
3. Keep `DesktopSession` as sole state authority. Preserve the board renderer and existing event paths unless specific defects justify changes.
4. Visually inspect the implemented UI after each substantial change, including native differences; confirm no clipping, stale widgets, broken actions or callbacks.

**Exit:** Professional, responsive, intuitive and verified desktop UI on supported platforms.

### D — **Replace** weak tests with a release-contract strategy

1. **Inventory each current test:** map it to an observable player/consumer or deployment contract and independently sourced expected result, or classify `retain/adapt/replace/delete`. Most internal-only tests should be retired **after** the behavior they purport to cover has a genuine boundary test.
2. Build a compact acceptance matrix: (a) real DesktopSession actor-visible legal/illegal/game results and replay, (b) independent rulebook/complete-game/perft references, (c) actual Tkinter mouse/keyboard/dialog/clock/reset UI paths, (d) hostile storage/resource/atomic recovery and failure boundaries, (e) four native **extracted frozen executable** end-to-end scenarios, (f) release/provenance policy.
3. Do not test the implementation as its own oracle: private class/field checks, method-call/mocked-action counts, toy objects bypassing production rules, syntax/import-only tests and deliberate “unavailable” results are not product acceptance. Deterministic fake time *only at a supported host boundary* is acceptable to reproduce clocks; never replace engine/view with mocks.
4. Keep only indispensable supplemental mathematical/validator tests, explicitly labeled diagnostic and never substituted for boundary acceptance. Prefer comprehensive nonduplicated user journeys. Validate both success and hostile/negative paths.
5. Mandatory real GUI tests and packaged-app acceptance fail closed if unavailable; no essential skip interpreted as green. Iterate targeted checks, then run all release gates on the **exact** reviewed SHA. All tests/fixtures/harness code reside in `.github/tests/`.

**Exit:** Small, coherent, behavior-first suites proving the actual playable application; old ineffective tests removed with no loss of meaningful coverage.

### E — Four-platform production package validation

1. Preserve working existing PyInstaller/native CI and PrideVer safeguards; extend real frozen tests beyond `--check`/process survival. Extract each archive on its actual Windows x64, macOS ARM64/x64 or Linux x64 runner; launch and interact with gameplay, use both definitions, settings, restart, shutdown, and confirm bundled JSON.
2. Verify signed/intended provenance and version metadata, archive layout, matching SHA256 sidecars and publication fail-closed on missing/corrupt assets. If signing/installability requires external credentials, explicitly disclose blocked status; never fake evidence.
3. Refresh final exact-head Python 3.10–3.13, required Xvfb, native four-platform checks and independently inspect test evidence plus UI visuals.

**Exit:** Four confirmed usable downloadable platform packages.

### F — Review, merge and publish v1.0.0

1. Complete cross-component review of code quality, game correctness, UX, security, package acceptance and current-state docs. No review thread resolved only due to deleted old lines.
2. Obtain maintainer approval of the **final** #271 SHA and merge into `develop` only on explicit authorization.
3. Separately review and approve same-repo `develop → main` release promotion; enable gated publication only at the authorized release boundary. Keep PrideVer sole version authority.
4. Publish and independently verify a public v1.0.0 GitHub release with four installable/playable platform assets, matching hashes/tag/source commit and accurate download instructions.

**Exit:** Released and usable v1.0.0, not merely a passing draft PR.

## Orchestrated execution / work ownership

- One canonical v1 issue #430 and one active desktop PR #271. Read-only architecture/test inventory and read-only UX audit can overlap with the engine bugfix.
- Scope each agent by task, exact pinned starting SHA, file ownership, acceptance, allowed writes and a structured evidence handoff; concurrency only for disjoint writes or isolated worktrees. Keep engine+JSON under one writer; independent QA/UX/packaging work cannot silently overlap a moving branch.
- DF task-specific dispatch is requested in [DarkFactory #2694](https://github.com/marius-patrik/DarkFactory/issues/2694), **not yet implemented by opening the issue**. Use currently supported orchestration only; do not claim scoped agents were launched.
- Never assign the entire migration/release to one unbounded agent. The orchestrator integrates verified handoffs, rechecks source/CI and keeps this plan and TODO current. No autonomous merge or publication.
- After v1 public release, #422 owns the v2 work described in issue #348; do not introduce it in #271.

**Scope:** Existing exports may continue operating, but no new export format or historical export-parity project is authorized for v1.
