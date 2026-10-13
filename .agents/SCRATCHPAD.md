# Integration Status

**2026-10-13 — source-backed status, not a second roadmap.** The sole current plan is [notes/PLAN.md](notes/PLAN.md); product requirements are [PRD](notes/PRD.md), deviations in [object_model](notes/object_model.md), operational rules in [AGENTS](AGENTS.md).

## Consolidation (in progress)

- **Plan:** [#129](https://github.com/marius-patrik/BoardGamesWithQuests/issues/129).
- **Sole active draft PR:** [#267](https://github.com/marius-patrik/BoardGamesWithQuests/pull/267), branch `feature/product-integration`, base `main`.
- Original **25** draft implementation PRs #218–#209 closed *unmerged* as superseded; previously rejected #170 remains closed. Their code history is preserved by a merge commit with current #218 and the previous full-stack #209 as parents. Old remote branch refs cannot yet be deleted using the connected GitHub API and require an authorized cleanup step after verification.
- Old open product/Plan issues were marked superseded rather than falsely completed; completed flattening #142 was marked completed. Only #129 and final behavior-gate [#239](https://github.com/marius-patrik/BoardGamesWithQuests/issues/239) stay open.
- The consolidated tree starts with the corrected #218 game-neutral foundation plus **unverified** historical chess/checkers piece/export candidates. It deliberately **does not** revive broken Tkinter, executable user rule/quest code, competing historical runtime loaders, rejected agent removal, or obsolete docs/CI versions. Preserving ancestry **does not equal integrating all behavior**.

## Actual product state

**Not playable, not deployed, not verified, and not approved for merge.** The Python engine remains incomplete for declarative JSON hooks, orthodox chess, WCDF checkers, per-user quests, online transactions, authentication, GUI, and end-to-end gameplay. Any green compile/format/docs check is only the stated check. The user approved a complete architecture change to JSON-only rules/quests, React, FastAPI on Vercel Functions, Supabase and a hosted Tauri web wrapper; these are **targets**, not delivered functionality.

## Immediate gates

1. Confirm consolidated branch contains merged history and correct retained source files; audit historical PR comments/requirements for recoverable algorithms, without importing rejected runtime code.
2. Finalize typed bounded JSON behavior AST/schema and demonstrate chess/checkers expressiveness; validate Vercel Python/Supabase connection and atomic test transaction.
3. Build final generic engine, games, web/API and persistence through the [single plan](notes/PLAN.md).
4. Rebuild permanent behavior tests only after final API/UI integration in [#239](https://github.com/marius-patrik/BoardGamesWithQuests/issues/239); temporary smoke/probes during development are required.
5. Align all docs/diagrams, provider settings, GitHub issues, labels and PR; perform independent review and real classroom public deployment tests.
6. Explicit maintainer approval before merge. **No approval has occurred.**

## Known blocking risks

Original full-stack code has broken startup/import and incompatible config methods, game-specific validator coupling, unauthorized move paths, per-player quest state leakage, invalid IDs/timers and exporter contract violations; it restored obsolete `theme/` and static package version. These are not fixed merely by retaining the old history. The new draft PR was opened through the connected GitHub account rather than bot-authored `open-pr` workflow; reconcile that procedural exception before approval. Original source and PR discussion remain accessible via closed historical PRs.
