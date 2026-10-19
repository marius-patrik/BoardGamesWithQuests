# Scratchpad — #271 current recovery findings

- **Synchronization:** #414 is merged as `develop` head `bc2531e4842a323153e399b6b784a974694d81f2`. #271 still contains its older governance ancestry; this PR is receiving an explicit merge of `develop` to preserve history and the desktop `src/` tree.
- **Source mismatch:** #271's `src/model/game/configuration.py` imports and executes editable Python modules. `src/view/code_editor.py` and `src/model/game/source_validation.py` remain connected to settings. Archived #405 has a different schema-driven `GameManager` and JSON rules; a file-level restore alone cannot bridge their APIs.
- **Missing implementation:** #405 held revisioned JSON transitions, bounded rule evaluation and event replay. Archived server auth/persistence/migrations and some tests are missing from #422; track server-only recovery there, not in desktop v1.
- **Tests:** A previous Python 3.12 run reported 424 passed, 46 skipped. Mandatory GUI acceptance and native packaged releases remain unverified.
- **Current development scope:** Correct the desktop engine then the UI; do not copy archived server/database runtime into #271 or enable Python publication prematurely.

- **Recovery baseline:** Archived #405 includes three game-engine trees (`src/model/`, `packages/engine/model/`, `packages/server/engine/model/`). The substantial revisioned JSON manager and declarative schema are under `packages/engine/model/`; the `packages/server/engine/` copy is not assumed equivalent. Select one authoritative implementation rather than restoring all trees.
- **First recovered modules:** `schema.py`, `conditions.py`, `hooks.py` now reside under `src/model/game/` and have JSON-boundary tests. These helpers do **not** yet replace the source-executing game configuration or perform game transitions.

- **Static schema source recovered:** `src/model/game/definition.py` validates bounded schema-v2 JSON and returns recursively immutable `GameDefinition` objects, using a pure `CapturePolicy` parser in `capture_policy.py`. Built-in archived `src/games/{chess,checkers}/config.json` resources are now tracked; they remain `playable: false`. Current legacy `Configuration` still controls gameplay, and the new validator is not yet wired to Tkinter.

- **Read-only snapshot query groundwork:** `src/model/game/snapshot_queries.py` now provides defensive-copy, finite-JSON snapshot queries. Tests exercise source isolation, rejected non-JSON data, missing facts and a trusted `RuleProgram` evaluating an isolated snapshot rule-state fact. Neither query adapter nor rule program is yet a live desktop transition engine.

- **Execution budgeting:** Pure `EvaluationBudget` instances now account for bounded rule-evaluation work and atomically reject exhausted nested counters. The registered `RuleProgram` accepts this budget; its effects are still only proposals, not production game transitions.

- **Capture geometry recovered:** `src/model/game/capture_geometry.py` enumerates capture routes against a non-mutating board with bounded searches, and is tested for a short capture and rejection without board mutation. It is not yet the production legal-move evaluator.
