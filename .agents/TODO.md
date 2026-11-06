# BoardGamesWithQuests — Finish and Ship v1.0.0

**Manual gameplay/GUI/native testing is maintainer-owned after publication.** No independent acceptance agent or J1–J8 gate. The sole remaining dispatch is the **implementation and release** prompt in [PLAN.md](PLAN.md). Active v1 PR #495 (`v1 → develop`), v2 future PR #496 (`v2 → develop`).

- [x] Git history cleanup and integration: exactly `main`, `develop`, `v1`, `v2`. Four independent Chess tests and original history are merged into `v1`; do not reimport, recreate, xfail or delete.
- [x] Four-platform package workflow retains smoke/build/checksum gates; extracted-app J1–J8 is now opt-in via manual `Desktop Native Manual QA` workflow, not required for release.
- [ ] Fix known Chess Buchanan dead/live/timeout source bug and preserve all four mandatory regressions (#473); safely suspend any undecidable timeout instead of fabricating FIDE outcomes (#477). Run focused affected tests.
- [ ] Implement PR #495's two `data/config/` review requests; update installed/frozen resources, package-data, manifests, tests and generated docs (#462).
- [ ] Finish release configuration: accurate `playable` flags, true four-platform packaging, correct SHA256, PrideVer enablement on approved source, truthful unsigned/unnotarized guidance (#445).
- [ ] After protected native maintainer approvals: merge #495 → `develop`; confirm actual default-branch Docs Actions deployment (current issue #502); review and merge `develop → main` release PR; publish PrideVer v1.0.0 with four archives and checksums.
- [ ] Preserve unique v2 commits/PR #496, retire temporary `v1` after release, close completed or canceled v1/ops issues. Final only `main`, `develop`, `v2` and open issue #348.

**Not in agent scope:** independent code/GUI/native acceptance, five unfinished J1–J8 test scenarios, macOS native-dialog QA automation, final cross-platform manual game testing. **The maintainer will test the released app.** Never claim unrun tests passed or circumvent red source regressions/required GitHub approvals.
