# Plan — BoardGamesWithQuests v1.0.0

**Product:** local Python/Tkinter Chess and English Draughts.  
**Integration PR:** #271 into `develop`. **Release:** reviewed `develop → main` promotion, then PrideVer v1.0.0.  
**Release publication:** disabled until behavioral and native package acceptance.

## Remaining work in execution order

### 1. Complete reference-game acceptance

1. Port the independent chess rule scenarios from archived #405 `tests/test_chess_rules.py` onto the supported public `DesktopSession` or revisioned `GameManager` interface. Verify castling (including traversed check), en passant (including discovered check), promotion and captures, checkmate/stalemate, legal escapes, threefold/fivefold repetition, move-count claims, dead material, timeout, resign and snapshot replay.
2. Port English-draughts reference positions from #405 and earlier gameplay tests onto the same authoritative JSON interface. Verify short kings, forced capture precedence, multi-jumps and branching routes, correct crowning timing, blocked-side outcomes and complete real games.
3. Test non-square configurable board geometry, bounded rule work, malformed/hostile hooks and forced atomic rollback using supported action interfaces. Remove incorrect declarative clauses; implement missing generic operations rather than variant checks in engine code.
4. Only after the relevant end-to-end scenarios pass, change each bundled definition from `playable: false` to `true`. Do not mark either game ready based on opening-only tests.

**Exit:** both shipped game definitions can complete and replay independent complete games and all their declared rules work through the public engine.

### 2. Complete player-facing desktop behavior

1. Exercise legal highlights, alternative capture-route and promotion selection, rejected actions, game switching and game-ended behavior through real Tkinter canvas interactions on Xvfb.
2. Verify authoritative clock progression/increment, expiration with no user click, timeout adjudication, cancellation of callbacks during window destruction and game switch, and nonmutation on rejection.
3. Verify first-move/first-capture quest progress and once-only rewards for both participants; test interaction with terminal outcomes and replay.
4. Implement actual player-facing notation export for chess and English draughts (in addition to the existing replayable JSON snapshot export), and verify full-game exported contents via the GUI.
5. Exercise corrupted/oversized preferences, symlink and path escape rejection, atomic writing, restart persistence and recovery across complete application sessions.
6. Extend mandatory UI acceptance to all supported Python versions where practical; ensure dedicated Xvfb gate remains mandatory and never silently skips.

**Exit:** both complete games, clocks, quests, errors, exports, reset/restart and shutdown work through the actual Tkinter UI, not only isolated engine tests.

### 3. Validate native frozen application

1. Verify the real Windows x64, macOS ARM64, macOS x64 and Linux x64 `desktop-build.yml` jobs for the final exact commit. Keep all produced artifacts from the PR run for inspection.
2. Require every frozen executable to run the permanent `--check` installation diagnostic: load both bundled JSON definitions, accept an action, confirm idempotency and replay. Fail archive creation on any diagnostic failure.
3. Extend frozen GUI smoke beyond process survival to real selection, move, game switch, export/preferences, restart and shutdown on each operating system. Do not treat source-run Xvfb widget tests as frozen application acceptance.
4. Inspect archive platform naming, contents, version/metadata, copied assets and SHA256 sidecars. Reject unsigned/incomplete/mismatched publication inputs according to existing release policy.

**Exit:** four fully functional self-contained native archives meet gameplay, metadata and checksum acceptance.

### 4. Reconcile quality and reviews

1. Run the entire required Python 3.10–3.13 matrix against current public-interface tests. Repair actual errors, obsolete declarations and config/version regressions without reintroducing Python game configuration.
2. Reconcile outstanding #271 review threads against the actual current diff; resolve the source editor complaint using tracked removal and verified GUI settings tests. Explain outdated server/web requirements as owned by #422 rather than pretending they exist in #271.
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
