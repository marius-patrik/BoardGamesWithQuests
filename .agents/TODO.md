# TODO — Current work

Only outstanding work is tracked here. Phase-level scope and acceptance are in [PLAN](PLAN.md); remove tasks when verified complete.

## Phase 0 — #414

- [ ] Independently review the entire #414 diff, current requirements/architecture, release workflow security and final CI; correct any findings.
- [ ] Verify native `develop` branch protection, required checks and approval settings.
- [ ] Obtain authorized `main` trusted-workflow bootstrap and native protection; verify the actual provider configuration.
- [ ] Verify GitHub Pages Actions publication and live PR previews.
- [ ] Reconcile migration-only Vercel status checks with Python-required checks.
- [ ] Obtain maintainer approval; merge #414 only after authorization and verify the merge.

## Phase 1 — #271

- [ ] Align #271 with the final #414 base and repair its current non-mergeable state.
- [ ] Complete and review engine/controller/Tkinter gameplay, configuration, clocks, quests, persistence and exports.
- [ ] Require real/virtual-display GUI acceptance and correct ineffective tests; verify the Python quality matrix.
- [ ] Build, install and smoke-test native Windows/macOS/Linux distributions using the Phase 0 infrastructure.
- [ ] Address applicable #271/#405 feedback, regenerate current-state documents, independently review, and obtain approval.

## Phase 2 — Release

- [ ] Merge approved #271; verify integration and native platform assets.
- [ ] Review and approve protected `develop → main` promotion.
- [ ] Verify automatic `v1.0.0` release, exact tag/SHA, all binary downloads and checksums.

## Phase 3 — Deferred until after v1.0.0

- [ ] Complete and verify #422's server, database, web, native and multiplayer migration.
