# Plan — BoardGamesWithQuests

**Target:** standalone Python/Tkinter `v1.0.0` · **Integration:** `develop` · **Release:** `main`  
**PR stack:** `#414 → #271 → #422` · **Current phase:** 0

## Execution order

| Phase | Owner | Remaining outcome | Status |
| --- | --- | --- | --- |
| **0 — Foundation** | **#414** | Verify repository/provider settings, release and docs infrastructure; finish review and merge | In progress |
| **1 — Desktop** | **#271** | Complete application, mandatory GUI acceptance, native package verification and review | Pending |
| **2 — Release** | Promotion PR | Integrate, approve `develop → main` and publish verified `v1.0.0` | Pending |
| **3 — Migration** | **#422** | Complete and verify FastAPI, Supabase, React, Tauri and multiplayer | Deferred until v1.0.0 |

## Completion criteria

- [ ] #414 is independently reviewed, its required live settings are verified, and it is approved and merged.
- [ ] #271 provides complete playable chess/draughts through Tkinter, passing real-GUI acceptance, resolved reviews and verified standalone distributions for all four platform targets; it is approved and merged.
- [ ] A reviewed same-repository `develop → main` promotion automatically publishes `v1.0.0` through PrideVer for the correct commit with four verified distributions and SHA256 checksums.
- [ ] #422 remains excluded until desktop v1.0.0 is released and verified.

## Phase 0 — Repository foundation (#414)

- [ ] Independently review the final #414 diff, generated requirements/architecture documents, workflow security and release gates; correct findings and re-run required checks.
- [ ] Verify actual `develop` branch rules, required check contexts, approvals and restrictions on force pushes/deletion.
- [ ] With approved administrator access, bootstrap trusted `main-source` and release workflows on `main` and enforce PR-only same-repository `develop` promotion, strict quality checks, independent approval, resolved conversations, admin protection and restrictions on force pushes/deletion.
- [ ] Verify GitHub Pages Actions publication and PR preview lifecycle; resolve unrelated Vercel web/API required-check interference without disabling relevant safeguards.
- [ ] Inspect GitHub's live provider settings and final checks; obtain maintainer approval, merge #414 and verify the result.

**Blocker:** Native GitHub protection administration currently returns HTTP 403 through the connected integration. Checked-in policy is not proof of provider enforcement. The existing packaging infrastructure cannot be accepted as functional desktop distributions until Phase 1 exercises the complete GUI.

## Phase 1 — Python/Tkinter application (#271)

- [ ] Bring #271 into alignment with the updated #414 base, resolve its current non-mergeable state, and inspect the consolidated desktop diff for duplicate state owners, imports, game definitions, resources and application boundaries.
- [ ] Complete and verify chess, English draughts, clocks, quests, settings, notation/exports, persistence, error handling, new games and all real Tkinter interactions.
- [ ] Replace ineffective tests; run mandatory real/virtual-display GUI acceptance without silent skips and verify the supported Python-version matrix.
- [ ] Run Phase 0 native packaging against the complete application on Windows x64, macOS ARM64/x64 and Linux x64. Verify packaged startup, gameplay, bundled resources, persistence and checksums; ensure failures block publication.
- [ ] Address remaining #271 review comments and applicable archived #405 feedback; update current-state requirements, architecture, notes, tests and generated docs in #271; independently review and obtain approval.

## Phase 2 — v1.0.0 release

- [ ] Merge the approved #271 into `develop` and verify the integrated application, mandatory tests and platform artifacts.
- [ ] Confirm native `main` protections and trusted source/release workflows are operational, then approve a reviewed same-repository `develop → main` PR.
- [ ] Allow guarded PrideVer resolution of `v1.0.0` and automatic publication only after all required platform jobs and checksums pass.
- [ ] Verify public release status, immutable tag, intended source SHA, four packaged downloads and checksums.

## Phase 3 — Architectural migration (#422; after v1.0.0)

- [ ] Reconcile #422 with the released application and its owning specification issues; fix actual Rust/Tauri Linux GLib CI dependencies.
- [ ] Complete FastAPI, Supabase authentication/persistence, React gameplay, Tauri, multiplayer, provider/deployment verification and applicable reviews; obtain explicit merge approval.

**Document ownership:** [GOAL](GOAL.md) defines outcomes; this file is the sole phase plan; [TODO](TODO.md) contains the active queue; [SCRATCHPAD](SCRATCHPAD.md) holds temporary evidence. Approved requests and accepted decisions document only implemented reality. Proposed future contracts remain in issues.
