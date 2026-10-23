# Plan — BoardGamesWithQuests v1.0.0

**Product:** local Python/Tkinter Chess and English Draughts.  
**Integration PR:** #271 into `develop`. **Release:** reviewed `develop → main` promotion, then PrideVer v1.0.0.  
**Release publication:** disabled until behavioral and native package acceptance.

## Remaining work in execution order

### 1. Complete reference-game acceptance

1. Expand the recovered FIDE reference acceptance with independent complete-game records and perft positions, cross-check terminal adjudication, legal escapes and clock expiration against source rulebooks, and resolve any observed deviations through the canonical JSON engine.
2. Extend the current English-draughts short-king, compulsory multi-jump, branching route, crowning-stop and last-piece outcome tests with full opening-to-terminal games, independently sourced move-count/perft positions and adversarial variant interactions.
3. Exercise outstanding independent non-square positions, aggregate-budget exhaustion and effect-failure rollback through supported action APIs. Existing adversarial tests cover special offers, idempotency and invalid declarations; only add scenarios demonstrating new observable gaps.
4. Only after the relevant end-to-end scenarios pass, change each bundled definition from `playable: false` to `true`. Do not mark either game ready based on opening-only tests.

**Exit:** both shipped game definitions can complete and replay independent complete games and all their declared rules work through the public engine.

### 2. Complete player-facing desktop behavior

1. Exercise legal highlights, alternative capture-route and promotion selection, rejected actions, game switching and game-ended behavior through real Tkinter canvas interactions on Xvfb.
2. Verify authoritative clock progression/increment, expiration with no user click, timeout adjudication, cancellation of callbacks during window destruction and game switch, and nonmutation on rejection.
3. Verify first-move/first-capture quest progress and once-only rewards for both participants; test interaction with terminal outcomes and replay.
4. Extend the implemented PGN and PDN notation exporters with independent reference-game cases (castling, en passant, promotion, disambiguation, capture chains, terminal results), and verify full-game output through the actual Tkinter export button.
5. Extend saved-game and preferences import/export acceptance with oversized-file, symlink/path escape, interrupted-write and restart recovery cases through complete application sessions.
6. Extend mandatory UI acceptance to all supported Python versions where practical; ensure dedicated Xvfb gate remains mandatory and never silently skips.

**Exit:** both complete games, clocks, quests, errors, exports, reset/restart and shutdown work through the actual Tkinter UI, not only isolated engine tests.

### 3. Validate native frozen application

1. Verify the real Windows x64, macOS ARM64, macOS x64 and Linux x64 `desktop-build.yml` jobs for the final exact commit. Keep all produced artifacts from the PR run for inspection.
2. Extend frozen GUI smoke beyond process survival to real selection, move, game switch, export/preferences, restart and shutdown on each operating system. Do not treat source-run Xvfb widget tests as frozen application acceptance.
3. Inspect archive platform naming, contents, version/metadata, copied assets and SHA256 sidecars. Reject unsigned/incomplete/mismatched publication inputs according to existing release policy.

**Exit:** four fully functional self-contained native archives meet gameplay, metadata and checksum acceptance.

### 4. Reconcile quality and reviews

1. Rerun the entire required Python 3.10–3.13 matrix after final gameplay and packaging changes; investigate exact-head failures and skips against real production contracts.
2. Reconcile the remaining outdated #271 review threads against the current desktop-only diff, preserving #422 ownership of unfinished server/web tasks; do not treat a superseded source file as delivered hosted functionality.
3. Inspect source-derived AST/UML diagrams and regenerate projections from canonical notes, requests, decisions and active rules. Ensure all records describe implementation in the PR rather than desired future features.
4. Perform independent implementation/security/gameplay review, obtain the maintainer's native approval of the final commit and merge #271 only when complete.

**Exit:** zero unresolved actionable desktop review concerns, fully green final-head CI and explicit maintainer approval.

### 5. Publish v1.0.0

1. Verify the approved #271 merge on protected `develop`.
2. Independently review the same-repository `develop → main` promotion, preserving current branch protection.
3. Confirm PrideVer's release and exact main SHA, enable the gated desktop release only after all four frozen binaries have met acceptance, and publish v1.0.0 with matching assets and hashes.
4. Verify the public release artifacts and disable/fail publication immediately on incomplete platform acceptance.

**Exit:** v1.0.0 is a released, usable, verified four-platform Tkinter application.

### Deferred (not part of v1.0.0)

#422 owns FastAPI, Supabase, React, Tauri, hosted identity, multiplayer and persistence. Do not implement those here or start their release work before desktop v1.0.0.
