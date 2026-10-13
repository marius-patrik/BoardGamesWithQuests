# Integration Status

**2026-10-13 — source-backed status, not a second roadmap.** The sole current plan is [notes/PLAN.md](notes/PLAN.md); product requirements are [PRD](notes/PRD.md), deviations in [object_model](notes/object_model.md), operational rules in [AGENTS](AGENTS.md).

## Consolidation and artifact status

- **Plan:** [#129](https://github.com/marius-patrik/BoardGamesWithQuests/issues/129).
- **Sole active draft PR:** [#271](https://github.com/marius-patrik/BoardGamesWithQuests/pull/271), branch `feature/product-integration`, base `main`.
- Original **25** draft implementation PRs #218–#209 closed *unmerged* as superseded; previously rejected #170 remains closed. Their code history is preserved by a merge commit with current #218 and the previous full-stack #209 as parents. All 26 obsolete PR branch refs (including rejected #170) were safely deleted through a one-time GitHub Actions workflow after verifying each head SHA was reachable from the consolidated commit. The cleanup workflow itself was then removed; the source history remains in commit ancestry. Unrelated historic refs were not part of this authorized cleanup.
- Old open product/Plan issues were marked superseded rather than falsely completed; completed flattening #142 was marked completed. Only #129 and final behavior-gate [#239](https://github.com/marius-patrik/BoardGamesWithQuests/issues/239) stay open.
- The **existing 211-item project board #14** was renamed from ChessWithQuests to BoardGamesWithQuests; the newly created empty duplicate #22 was removed, keeping the original data. DarkFactory project automation now succeeds for #129 and #271. Global project #17 remains; #129 and #239 were added, but adding PR #271 to Global hit GitHub GraphQL rate limits and remains unverified. Historical issue/PR project status fields still need auditing because item events failed before the board was renamed. The one-time sync workflow was removed rather than leaving a broken automation.
- The canonical `darkfactory` management branch now contains only `repo.dfconfig` (latest verified DarkFactory v0.289.0), and the integration branch has a matching active configuration. `.github/darkfactory.json` is absent from the consolidated working tree.
- **Remaining historical refs:** `rebuild/chain-tip` and `rebuild/true-base` are unrelated divergent recovery histories, not part of the closed PR stack. They were not deleted because they contain unique commits that were not absorbed by the consolidation. Do not misrepresent them as active implementation branches.
- Structural CI, strict documentation generation, issue binding and package metadata checks have passed on the consolidated branch (e.g. commit `82020e6` and subsequent verification); **no behavior test suite exists yet**. Changes after each verified SHA still require fresh checks.
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

Original full-stack code has broken startup/import and incompatible config methods, game-specific validator coupling, unauthorized move paths, per-player quest state leakage, invalid IDs/timers and exporter contract violations; it restored obsolete `theme/` and static package version. These are not fixed merely by retaining the old history. The owner-authored draft #267 was closed and replaced by reviewable DarkFactory App-authored draft #271; the one-time reissue workflow was removed after verified success. Original source and PR discussion remain accessible via closed historical PRs.
