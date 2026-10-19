# Plan — BoardGamesWithQuests

**Target:** complete locally playable JSON-configured Python/Tkinter `v1.0.0`.  
**Integration:** `develop` · **Release:** `main` · **Current owner:** PR #271.  
**Stack:** `develop → #271 → #422` (governance PR #414 was merged).

## Execution order

| Stage | Deliverable | Status |
| --- | --- | --- |
| 1 | Account for #405's lost JSON-rule engine, tests and server-only work | In progress: v2 definitions, pure rule evaluator, snapshot queries and capture geometry recovered |
| 2 | Reconcile one authoritative versioned JSON game model in `src/model/` | Pending |
| 3 | Complete executable chess and English-draughts configurations | Pending |
| 4 | Adapt recovered Tkinter controllers, boards and views to the canonical engine | Pending |
| 5 | Remove player-facing rule/quest editing and replace executable configuration with validated JSON settings for permitted properties | Pending |
| 6 | Verify real gameplay, clocks, quests, save/export, hostile inputs and graphical interactions | Pending |
| 7 | Build, run and verify four native platform distributions | Pending |
| 8 | Resolve reviews, refresh source-governed docs and obtain approval to merge #271 | Pending |
| 9 | Approve `develop → main`, publish verified v1.0.0 through PrideVer | Pending |
| 10 | Complete post-release FastAPI/Supabase/React/Tauri migration on #422 | Deferred |

## Completion criteria

- [ ] Each substantial #405 implementation and test has a documented disposition: desktop recovery, post-release #422, verified replacement or intentional retirement.
- [ ] The desktop application contains one canonical generic JSON engine; no user-provided Python is executed.
- [ ] Supported chess and English-draughts definitions run to actual terminal outcomes through Tkinter, including clocks, quests, settings, persistence and export.
- [ ] Python 3.10–3.13 tests and mandatory real/virtual-display GUI acceptance pass without required graphical skips.
- [ ] Windows x64, macOS ARM64/x64 and Linux x64 packaged executables run successfully and have verified resources/checksums.
- [ ] Applicable #271 and archived #405 feedback is resolved; the final diff/CI/governance are reviewed and #271 approved/merged.
- [ ] An approved same-repository `develop → main` promotion publishes immutable v1.0.0 with all four verified downloads.
- [ ] No unfinished server/web/native migration implementation ships in v1.0.0.

## 1. Recover the authoritative implementation

1. Compare the historical GUI commit `43a3d01fab45a305d02ef26a4f86f0e7cd9a0d96`, closed #405 head `6002ac787664efceb0161d2bcbd3891927b69b34`, and live #271/#422 heads.
2. Recover and check remaining archived `manager`, generic board/capture geometry, rule queries, snapshot queries, outcomes and replay against the v2 immutable definitions already staged under `src/model/game/definition.py` and `src/games/{chess,checkers}/config.json`.
3. Account for discarded FastAPI auth, PostgreSQL transactions/migrations, concurrency and replay tests; assign server-only work to #422 without restoring that runtime into #271.
4. Reconcile the recovered immutable v2 definition parser, bounded schema/hook evaluator and isolated read-only snapshot queries with generic board/clock/quest execution; restore deterministic events/replay as **one** authoritative implementation in `src/model/` and remove the competing Python-configured manager.
5. Prove illegal actions do not change state, stale revisions fail, identical retries are idempotent and snapshots replay deterministically.

## 2. Finish game definitions and desktop integration

1. Convert shipped chess and English-draughts configurations to validated versioned JSON; do not expose the archived `playable: false` games as working until their rule acceptance passes.
2. Implement and test chess special actions, checks, draws and notation; correct English-draughts short-range kings and compulsory/multiple captures. Keep international draughts separate and non-playable unless proven.
3. Introduce a desktop session/controller adapter for local participant IDs, revisioned actions and monotonic clock timestamps, without HTTP or database dependencies.
4. Update `src/controller/` and `src/view/` to render canonical state and send action intents. Preserve startup, selection, game switching, quest panels, clock refresh and error recovery; cancel abandoned Tk callbacks.
5. Remove `src/view/code_editor.py` and `src/model/game/source_validation.py` after eliminating their production callers. The UI must **not permit editing rules or quests**, whether as Python or raw JSON. Game definitions may contain trusted, immutable declarative rules/quests; settings expose only permitted non-executable user preferences and configuration fields.
6. Keep immutable bundled definitions separate from atomic, validated user JSON in an OS-appropriate application-data directory.

## 3. Verify and package

1. Port relevant historical/#405 chess, rule-budget, adversarial, terminal-action and draughts scenarios to `.github/tests/`.
2. Replace ineffective tests and enforce required GUI acceptance under an actual or virtual Tkinter display; test complete chess/draughts games and JSON-settings round trips.
3. Run the complete Python 3.10–3.13 quality matrix; inspect every skipped case.
4. Adapt Phase 0's `.github/workflows/desktop-build.yml` and `package_desktop.py` to the final source, include immutable game resources and validate bundled launch/play/save/export on Windows x64, macOS ARM64/x64 and Linux x64.
5. Require the release workflow to reject incomplete assets or checksum failures; keep `repo.dfconfig` release disabled until every acceptance gate is proven.

## 4. Review, integrate and release

1. Resolve #271's current review threads (including the objection to Python code editing) and relevant historical #405 defects with test-backed fixes.
2. Update `.agents/notes/`, `requests/`, `decisions/` and source-derived diagrams **as functionality changes**, regenerate README/PRD/ARCHITECTURE/AGENTS and run CI.
3. Independently review final #271 behavior, ownership and diff, obtain maintainer approval and merge into `develop`.
4. Verify trusted release-branch protection and completed platform builds, obtain approval for same-repository `develop → main` promotion, then publish/verify `v1.0.0` through PrideVer.
5. After v1.0.0, finish the remaining migration in #422 without introducing a second authoritative game engine.

**Current caveat:** The recovered desktop GUI and extensive tests exist, but the active app still loads executable Python game/quest modules and does not contain #405's newer JSON rule engine. The earlier 424-passed/46-skipped source test run does not prove GUI or platform acceptance.
