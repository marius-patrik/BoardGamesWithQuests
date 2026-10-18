# Plan — BoardGamesWithQuests

**Integration:** `develop` · **Release:** `main` · **Target:** standalone Python/Tkinter `v1.0.0`  
**GitHub-native stack:** `#414 → #271 → #422`; #405 was consolidated into #271 and closed.  
**Current phase:** 0 — repository setup, governance, packaging and release infrastructure.

## Execution order

| Phase | Owner | Deliverable | Status |
| --- | --- | --- | --- |
| **0** | **#414** | Governance, repository/provider settings, documentation, platform-packaging infrastructure, automatic guarded release workflow | Source implemented; provider setup and final review pending |
| **1** | **#271** | Complete Python/Tkinter application, behavioral and real-GUI acceptance, platform artifact verification | Consolidated; acceptance pending |
| **2** | Release promotion | Approve/merge #271, protect/promote `develop → main`, automatically publish verified v1.0.0 | Pending phases 0–1 |
| **3** | **#422** | Finish FastAPI, auth/database, React, Tauri and multiplayer migration | Deferred until v1.0.0 |

## Completion criteria

- [ ] #414 has reviewed accurate product/architecture records, operational native branch and Pages settings, and a secure fail-closed desktop release pipeline; it is approved and merged.
- [ ] #271 has complete playable chess/draughts and Tkinter behavior, mandatory real-GUI tests, resolved applicable reviews and verified packages for every supported platform; it is approved and merged.
- [ ] The authorized same-repository `develop → main` promotion automatically publishes `v1.0.0` through PrideVer with the intended commit, four native packages and verified checksums.
- [ ] #422 stays excluded from the desktop release and resumes only afterward.

## Phase 0 — #414: repository foundation

- [x] Recover template documentation ownership and GitHub-native PR stacking; retain bot-authored #271.
- [x] Complete source-governed documentation, DarkFactory checks, source-derived diagrams, product requirements and architecture for the **actual #414 engine**.
- [x] Implement cross-platform PyInstaller/GUI-smoke/archiving/checksum infrastructure and a release workflow dependent on every required platform; keep `repo.dfconfig` Python publication disabled pending the complete application.
- [ ] Independently inspect #414's complete diff and all current generated documentation; address findings and rerun checks.
- [ ] Verify **`develop` native settings** (required check names, review policy, restrictions on force push/deletion).
- [ ] Through an approved administrator-authorized route, bootstrap trusted `main-source` and release workflows on `main`; configure **`main` native protections**: only same-repository `develop` PR promotion, strict checks, independent review, resolved discussions, admin enforcement and restrictions on force pushes/deletion.
- [ ] Verify GitHub Pages Actions publication and PR preview lifecycle, and separate migration-only Vercel API/web status checks from required Python/release checks.
- [ ] Re-read actual provider state and CI after setup; obtain maintainer approval and merge #414.

**External blocker:** This GitHub integration cannot administer branch protection (HTTP 403). Checked-in policy is not evidence of enforcement. Platform GUI packaging will be executed against #271's completed sources, not claimed as proven on #414.

## Phase 1 — #271: desktop application and acceptance

**Canonical implementation on #271:** `src/chesswithquests/`, `src/controller/`, `src/model/`, `src/view/`, `src/games/{chess,checkers}/`. The historical Tkinter GUI has already been recovered.

- [ ] Review model, controller, GUI, config, imports, persistence and resource ownership; eliminate duplicate or competing implementations.
- [ ] Complete chess, draughts, clock, quest, settings, notation/export, error-recovery and new-game behavior through the actual Tkinter interface.
- [ ] Replace ineffective tests, run mandatory GUI acceptance under a real/virtual display rather than skipping, and verify Python tests on 3.10–3.13.
- [ ] Execute Phase 0 Windows x64, macOS ARM64/x64 and Linux x64 packaging **against completed application source**; verify standalone launch, resources, gameplay and checksums.
- [ ] Reconcile all active #271 and relevant archived #405 reviews, and update same-PR requirements, architecture, generated docs and diagrams. Independently review the final diff and request approval.

**Existing evidence:** An inspected Python 3.12 run reported **424 passed, 46 skipped**; skipped graphical tests are not GUI acceptance.

## Phase 2 — v1.0.0 promotion and publication

- [ ] Merge approved #271 into `develop`; verify integrated behavior, governance and packaged application.
- [ ] Confirm Phase 0 native protections, trusted release workflows and required checks are active on `main`.
- [ ] Approve/merge a reviewed same-repository `develop → main` PR for the exact validated commit.
- [ ] Automatically resolve `v1.0.0` via PrideVer, run the complete platform matrix and publish only all-asset-verified releases.
- [ ] Independently verify the public release tag, source SHA, four binary distributions and SHA256 checksums.

## Phase 3 — #422: post-release migration

- [ ] Rebase/refresh #422 onto the released baseline; correct Rust/Tauri Linux GLib CI dependencies.
- [ ] Reconcile implementation contracts in issues, then complete and verify FastAPI, Supabase auth/persistence, React/Tauri clients, multiplayer and deployment.
- [ ] Independently review and obtain approval before merging.

## Document ownership

This file is the **sole execution plan**. [TODO](TODO.md) lists immediate actions; [SCRATCHPAD](SCRATCHPAD.md) records temporary evidence; [GOAL](GOAL.md) defines success. Approved requests and accepted architecture describe only what exists *on this branch*; proposed future contracts stay in issues. No new roadmap file or duplicate plan authority.
