# Scratchpad — #271 current recovery findings

- **Synchronization:** #414 is merged as `develop` head `bc2531e4842a323153e399b6b784a974694d81f2`. #271 still contains its older governance ancestry; this PR is receiving an explicit merge of `develop` to preserve history and the desktop `src/` tree.
- **Source mismatch:** #271's `src/model/game/configuration.py` imports and executes editable Python modules. `src/view/code_editor.py` and `src/model/game/source_validation.py` remain connected to settings. Archived #405 has a different schema-driven `GameManager` and JSON rules; a file-level restore alone cannot bridge their APIs.
- **Missing implementation:** #405 held revisioned JSON transitions, bounded rule evaluation and event replay. Archived server auth/persistence/migrations and some tests are missing from #422; track server-only recovery there, not in desktop v1.
- **Tests:** A previous Python 3.12 run reported 424 passed, 46 skipped. Mandatory GUI acceptance and native packaged releases remain unverified.
- **Current development scope:** Correct the desktop engine then the UI; do not copy archived server/database runtime into #271 or enable Python publication prematurely.

- **Recovery baseline:** Archived #405 includes three game-engine trees (`src/model/`, `packages/engine/model/`, `packages/server/engine/model/`). The substantial revisioned JSON manager and declarative schema are under `packages/engine/model/`; the `packages/server/engine/` copy is not assumed equivalent. Select one authoritative implementation rather than restoring all trees.
- **First recovered modules:** `schema.py`, `conditions.py`, `hooks.py` now reside under `src/model/game/` and have JSON-boundary tests. These helpers do **not** yet replace the source-executing game configuration or perform game transitions.
