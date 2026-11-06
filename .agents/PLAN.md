# BoardGamesWithQuests — v1.0.0 Completion and Release

**Canonical v1 issue:** [#430](https://github.com/marius-patrik/BoardGamesWithQuests/issues/430)  
**Implementation PR:** [#495](https://github.com/marius-patrik/BoardGamesWithQuests/pull/495) (`v1 → develop`)  
**Release promotion PR:** [#501](https://github.com/marius-patrik/BoardGamesWithQuests/pull/501) (`develop → main`)  
**Future v2:** [#496](https://github.com/marius-patrik/BoardGamesWithQuests/pull/496) (`v2 → develop`), issue #348  
**Release:** `v1.0.0`

**Target product:** A complete local Python/Tkinter Chess and English Draughts desktop application with Python-defined rules, authoritative gameplay, clocks, quests, game history and persistent per-game logs. The existing Canvas board remains the drawing surface; the surrounding Tkinter widgets use modern monochrome ttk styling. The maintainer conducts gameplay, GUI and native-platform testing after publication.

**Review interpretation:** The latest overall review on PR #495 requests a **code-defined v1 game model** and alignment with the posted reference UML, including overlapping responsibilities and names. Game rules and built-in game definitions therefore live in Python modules; persistent game records may use JSON as a *data format*. The PR's inline requests are assigned below to concrete code destinations. Treat this interpretation as the working review resolution for maintainer discussion before implementation.

## Phase 1 — Complete the application and integrate PR #495

### 1. Python-defined Chess and English Draughts

1. Implement bundled game definitions in `src/model/chess.py` and `src/model/checkers.py`, using Python model objects/functions for initial positions, pieces, legal movement, captures, promotion/crowning, terminal rules, clocks and quests. Preserve the behavior represented by the current `data/chess.json` and `data/checkers.json` implementations, including Chess FIDE special moves and WCDF compulsory/multihop captures.
2. Use `src/model/definition.py` for the common typed game-definition contract and the shared rule/quest declarations. Route the game selector through the two Python definitions; update `src/main.py`, controller calls, installed entrypoint and frozen application boot.
3. Complete the transition from runtime JSON rule/config evaluation to these Python definitions, then remove the superseded game-definition JSON files, loaders, bundled-configuration packaging, and config-specific tests. Retain observable Chess, Draughts, quests, history and terminal behavior through replacement gameplay regressions.
4. Align the domain objects and relationships with the **reference class diagram in PR #495's maintainer comment**. For overlapping concerns, implement the roles of `GameManager`, `HerniPlocha`/board, `Figurka`/piece, `Tah`/move, `RevizorTahu`/validator, `Hrac`/player, `Timer`, `Quest`, `QuestManager`, and `GameLogger`. Keep a single authoritative game-state owner and a single legal-move validator. Use the diagram's domain names where matching existing functionality, and preserve explicit Python import names through the coordinated migration.
5. Retain and pass the four independent Chess reachability regressions already integrated at `.github/tests/test_chess_fide_reachability_boundaries.py`: Buchanan dead fortress, live near-twin legal mate, side-specific timeout result and checkmate precedence at the 75-move boundary. Implement FIDE 5.2.2/6.9/5.1.2 with a sound distinction between provably possible, provably impossible and unresolved mating reachability. Persist unresolved flag falls with suspended clocks, replayable provenance and an explicit operator-resolution flow. Add focused restart, retry, rollback, legacy-save and unaffected-Draughts regressions.

### 2. Consolidate the model modules (PR #495 review comments)

| Review target | Phase 1 code action |
| --- | --- |
| `src/model/session.py` | Rename to `src/model/game.py`; retain the public game/session lifecycle, idempotent actions and authoritative state. Update imports and tests. |
| `src/model/schema.py`, `src/model/outcomes.py` | Move remaining model/action validation and outcome checks into `src/model/validator.py`; remove superseded modules. |
| `src/model/hooks.py`, `src/model/conditions.py` | Move shared typed rule/condition behavior into `src/model/definition.py` and the Python game definitions; remove superseded interpretation layers. |
| `src/model/capture_policy.py`, `src/model/capture_geometry.py` | Move capture legality and capture-route generation into `src/model/validator.py`; retain WCDF-specific route semantics. |
| `src/model/board_queries.py` | Place board-state reads on `src/model/board.py` and move-legality queries on `src/model/validator.py`; retire the stand-alone query facade. |
| `src/model/snapshot_queries.py` | Move authoritative snapshot reads and history/clock queries into the game/manager state interface; retire the stand-alone snapshot-query adapter after converting all callers. |
| `src/model/resources.py`, `src/model/games.py` | Replace bundled JSON discovery with direct Python game registration and installed-package imports; remove obsolete resource discovery. |
| `src/model/notation.py` | Remove PGN/PDN and notation-export implementation and its user commands. |
| `src/model/preferences.py` | Move any necessary default visual constants to the ttk application; remove player-editable settings persistence. |
| `src/model/persistence.py` | Consolidate into `src/model/logger.py`; maintain one atomic, revisioned JSON activity/save file per game beneath the **writable application data root** at `data/logs/<game-id>.json`, with secure path handling, retry recovery and deterministic replay. |
| `src/controller/controller.py` | Rename to `src/controller/game_controller.py`; update the window controller, views, entrypoint and tests. |

**Persistence placement:** `data/logs/` is relative to the application's writable per-user data directory, so installed wheels and frozen applications can save without modifying bundled code/assets. File identity is one stable file per game; action/history updates are atomic and replayable.

### 3. Consolidate and restyle the GUI (PR #495 review comments)

1. Rename `src/view/board.py` to `src/view/game.py`; keep its Canvas board drawing, pointer actions, promotion/capture selection and piece rendering.
2. Move screen composition, commands, toolbar, game selection, session status, clock displays and dialog ownership from `src/view/screen.py` into `src/view/app.py` and `src/view/game.py`, with a clear separation between Tk application/window ownership and game-specific board presentation.
3. Move dialog composition from `src/view/modal.py` and focus/grab/close behavior from `src/view/dialog_lifecycle.py` into the appropriate app/game owners; preserve cancellation, focus restoration and error handling.
4. Merge quest widgets from `src/view/quests.py` into `src/view/panel.py`; each player's quests and status remain visually associated with that player's panel.
5. Remove the player settings window `src/view/settings.py` and its commands; define the fixed desktop presentation in `src/view/app.py`.
6. Apply a modern **black/white/neutral-gray ttk theme** in `src/view/app.py`: readable contrast, coherent rounded-where-supported widget styling, clear disabled/focused states, balanced spacing, and the existing left-player/board/right-player composition. Keep game-piece colors distinguishable when required for gameplay.
7. Replace player-facing file Export, Notation and editable-rule/configuration commands with the automatic per-game activity/save log. Provide session resume and clear saved-game status through the actual game UI.
8. Update imports, resources and keyboard/mouse actions for the completed view/controller layout and check both Chess and Draughts launch, play, save/resume, draw/resign and shutdown from the installed application.

### 4. Finalize source correctness, packaging and PR review

1. Run focused tests for the new Python definitions, Chess FIDE reachability, complete WCDF capture/crowning, session/clock/quest/terminal transitions, per-game log durability and GUI startup/actions. Migrate existing tests to stable player-facing Python/Tk boundaries and preserve the four independent FIDE regressions.
2. Move repository-owned tests and helper scripts to root-level `tests/` and `scripts/` in accordance with the original maintainer review on PR #271. Update all workflows, pytest discovery, release tooling and documentation generator paths. Preserve the four Chess FIDE regressions and existing gameplay checks. Update `pyproject.toml`, wheel/sdist contents, native packaging, runtime manifests, generated docs and diagrams for Python game modules. Maintain archive-safe version selection.
3. Ensure four buildable desktop distributions remain supported: Windows x64, macOS ARM64, macOS x64 and Linux x64. Keep package smoke checks, source/version provenance and SHA256 checksums in the GitHub Actions release path; keep extracted GUI journey tests available to the maintainer as a manual workflow.
4. Correct the live `Deploy Documentation` workflow failure represented by pipeline incident #503 and route follow-up deployment-failure reporting into the consolidated v1 issue #430; verify source and docs workflow execution on `v1`.
5. Respond to **all 22 current PR #495 inline review threads** with exact code/diff evidence. Address the latest overall review's Python-only v1 architecture and UML reference. Request the maintainer's review resolution and required protected-branch approval on the final PR SHA.
6. Deliver a clean `v1` source SHA with passing required source/build CI, traceable code changes and release-ready packaging.

## Phase 2 — Publish v1.0.0 and complete repository cleanup

1. Finalize and obtain required approval for **PR #495 (`v1 → develop`)**; merge through protected GitHub controls and verify the resulting `develop` SHA, required CI and actual default-branch Actions documentation deployment.
2. Update the **existing draft PR #501 (`develop → main`)** to the promoted candidate, obtain the required maintainer approval and merge through protected GitHub controls.
3. Enable the existing `repo.dfconfig` Python release publication setting on the reviewed release source; use the existing PrideVer `.github/workflows/release.yml` from the live `main` SHA to publish **`v1.0.0`**.
4. Verify all four public architecture-correct native archives and their SHA256 sidecars, the source/tag relationship and accurate Windows/macOS unsigned/notarization disclosures. Provide the maintainer with installation and first-run guidance for postrelease testing.
5. Preserve `main`'s released history in `v2` via a history-preserving merge; retain draft PR #496 and its unique functionality. Delete temporary `v1` after its commits remain reachable from the protected release history. Preserve release tags and archived commits.
6. Close consolidated issue #430 after successful publication and cleanup. **Final repository branches:** `main`, `develop`, `v2`. **Final open issue:** #348.

**Delivery ledger:** final source and release SHAs, PR approval/merge links, focused regression results, documented live review dispositions, docs deployment result, four release artifact URLs and hashes, v2 ancestry verification and final issue/branch inventory.
