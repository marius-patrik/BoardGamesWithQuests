# BoardGamesWithQuests — v1.0.0 Action Queue

**One current v1 issue:** #430. **Implementation:** PR #495 (`v1 → develop`). **Release promotion:** existing draft PR #501 (`develop → main`). **Future v2:** #348 / PR #496.

## Phase 1 — Complete application and PR #495

- [ ] Convert Chess and English Draughts' built-in game definitions and rules into Python modules; preserve complete game behavior and independent FIDE/WCDF regressions.
- [ ] Align GameManager, board, piece, move, validator, clock, quests and logger with the maintainer's reference class diagram; consolidate schema/conditions/hooks/outcomes/capture/query adapters into their named owning modules.
- [ ] Rename session → game, controller → game_controller and view board → game; place app/dialog/screen composition in app/game, quests in panel; deliver modern monochrome ttk desktop UI.
- [ ] Remove player-facing settings, notation and export; write one atomic JSON save/activity log per game to the writable app-data `data/logs/` directory; provide resume/replay.
- [ ] Correct the Buchanan dead/live/flag-fall Chess outcomes with sound proof handling and durable unresolved adjudication; retain the four already-integrated source-backed tests.
- [ ] Update source consumers, tests, wheels/sdists, four native package manifests/builds, generated docs/diagrams and deployment-failure handling (#503 → #430).
- [ ] Address all 22 inline threads and the latest code-only/UML overall review on PR #495; obtain maintainer review disposition and required PR checks.

## Phase 2 — Publish and finish

- [ ] Approve and merge PR #495 into protected `develop`; confirm default-branch documentation deployment.
- [ ] Update and approve existing draft PR #501 (`develop → main`); merge with protected checks.
- [ ] Enable PrideVer publication and publish v1.0.0 from `main` with four real platform packages, smoke/resource integrity and SHA256 sidecars.
- [ ] Provide truthful native trust/install guidance for maintainer-led postrelease testing.
- [ ] Preserve released v1 in `v2`, retain PR #496, delete integrated `v1`, close #430. Finish with branches `main`, `develop`, `v2` and one open issue #348.
