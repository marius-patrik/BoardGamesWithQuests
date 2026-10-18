# TODO — Current work

Task queue for the existing [Plan](PLAN.md). Mark complete only with verified evidence.

## Phase 0 — #414

- [x] Restore template-style GOAL, PLAN, TODO and SCRATCHPAD ownership; delete the redundant roadmap.
- [x] Describe the current product architecture in approved requests and accepted decisions; regenerate docs.
- [x] Add four-platform desktop build/release infrastructure while keeping Python publication disabled.
- [ ] Independently review #414's final source and release security, then verify CI.
- [ ] Inspect `develop` native protection, required check names and approval policy.
- [ ] Obtain authorized `main` trusted-workflow bootstrap and native branch protection; verify provider enforcement.
- [ ] Verify live GitHub Pages Actions publication and PR previews.
- [ ] Reconcile irrelevant Vercel statuses with Python release checks.
- [ ] Address any new review findings; request approval before merge.

## Phase 1 — #271

- [ ] Audit final desktop model/controller/Tkinter behavior, eliminate duplicates and fix game/configuration/clock/quest/export defects.
- [ ] Enforce real GUI acceptance without silent skips; run full Python quality matrix.
- [ ] Build and smoke-test native executable assets on all Phase 0 runners.
- [ ] Resolve applicable #271 reviews, inspect archived #405 feedback, regenerate documentation, obtain approval.

## Phase 2 — Release

- [ ] Merge approved #271, verify integrated acceptance and protected `develop → main` promotion.
- [ ] Verify automatic `v1.0.0` publication and all binary/checksum assets.

## Phase 3 — Deferred

- [ ] Resume #422 only after v1.0.0 and complete the migration independently.
