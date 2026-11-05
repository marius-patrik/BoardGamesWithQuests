# BoardGamesWithQuests v1.0.0 — current queue (DRAFT)

**Canonical:** [PLAN.md](PLAN.md) and #430; **one integration:** draft PR #271 → develop; **v2:** #348 + draft #422. Manual agent prompts ONLY; user has not authorized dispatch.

## Completed by orchestrator, 2026-11-05
- [x] Verified develop has 20 history-only commits from merge-base bc2531e4842a323153e399b6b784a974694d81f2; identical tree 64f5da77bb9390ac83cc7f117a1a7a82b61c4cb3.
- [x] Integrated all develop commits through two-parent merge commit 3c802428889f58e3b4a96c950a4b57bbbcb969e6 with **no content change**.
- [x] Safely deleted qa/443-final-native-recovery (33e15ecb8ca4d24def9deeaadacbcfd367c14fcb) and qa/443-lifecycle-persistence (ee671de5b317700beda6fd6b8e43e8be8b4de40f): preserved ancestor commits in qa/443-n1b-macos-recovery (3d119f4767db06c9d0d814522044436f49dd42d7), no open PR ref dependence. Successful GitHub Actions run #42029588171.
- [x] Removed temporary one-shot deletion workflow after successful execution (plan-update commit).

## Pending, ONLY after plan approval and manually launched prompts
- [ ] **Prompt 0**: exact unique-scope comparison across 3 surviving native QA branches, preserve 4 Chess proof test cases, choose sound FIDE algorithm or precise blocker, finite existing docs/PR/CI and fleet issue contract, no broad audits.
- [ ] **Prompt 1**: implement approved C01/C02 Chess, N01 macOS overwrite, N02 J7/J8/advanced native tests, D01 canonical docs paths, D02 docs 422 status handling, G02 five review threads, G03 duplicate fleet automation, G04 playable flags; integrate accepted source and safely remove now-redundant branches.
- [ ] **Prompt 2**: ONE final independent all-Python/FIDE/WCDF/GUI/4-native-platform J1–J8 acceptance at exact SHA; NO-GO returns targeted fix to Prompt 1.
- [ ] **Explicit maintainer approvals only:** PR #271 → develop; reviewed develop → main; PrideVer v1.0.0 publication, signing/trust policy, verify 4 public binaries.
- [ ] **Post-release:** v2 history preserved/reconciled, close stale v2 PR #422, delete obsolete v1 integration branch, close all complete v1/operational issues. Final only main, develop, feat/independent-server-web-native-bootstrap and one OPEN issue #348.

## Fixed reality checkpoint
- 324 Python tests passed on each of 3.10–3.13; 71 real Tk passed; editable/wheel/sdist passed; four **native package builds** passed. This is not 4-OS extracted-native certification.
- Existing qa/443-final-data-acceptance remains 5 commits ahead of integration baseline with real frozen test work, but Mac overwrite AX control failed and advanced/offline/process journeys are NOT RUN. Keep branch for Prompt 1.
- Existing chess proof branch game/473-sound-unwinnability contains 4 useful sourced tests but remains RED without a mathematically sound fix; adapt stale model.game imports.
- Both data/chess.json and data/checkers.json have playable:false; release disabled.
- Five unapproved maintainer review threads, outdated .agents/notes/0001-product.md and 0002-structure.md, Docs deployment-preview-status HTTP 422 and duplicate DarkFactory fleet issue #493 remain.
- Do not delete qa/443-frozen-native-acceptance or qa/443-n1b-macos-recovery until unique code/tests are checked against final-data; do not touch v2.
