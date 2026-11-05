# BoardGamesWithQuests v1.0.0 — Master Execution Plan

**Status: DRAFT — maintainer has not approved agent dispatch.** Authorized repository hygiene executed on 2026-11-05 is recorded below.
**Repository:** marius-patrik/BoardGamesWithQuests. **Master issue:** #430. **Sole v1 integration:** draft PR #271, feature/product-integration → protected develop. **v2:** issue #348, branch feat/independent-server-web-native-bootstrap, draft PR #422.
**Product goal:** Finish the existing Python/Tkinter Chess and WCDF English Draughts game. Preserve the JSON-configured engine, Canvas board, session, clocks, quests, saving, and working tests. No engine rebuild, UI rewrite, new architecture, unrequested v2 feature, or general new audit.

**Execution policy:** ChatGPT orchestrates and supplies these **three copyable manual agent prompts**; user launches agents. No DarkFactory issue-event agent execution, duplicate dispatch issues or unattended background work. Agents may run focused reproductions/regressions during implementation. **Only Prompt 2 is comprehensive application acceptance.** Never change protected develop/main, authorize a release, or delete a live branch by implication; every merge/release remains owner-controlled. Each agent must record source SHA, exact changed paths, tests and PASS/FAIL/BLOCKED evidence.

## 0 — Reconcile surviving work and settle only concrete technical decisions

### Completed by orchestrator (2026-11-05)

- **Integrated current develop ancestry into PR #271:** merge commit 3c802428889f58e3b4a96c950a4b57bbbcb969e6, parents f94dccf10cf247bce7f0304d8c75b1246a9aa91f and dee3f39f4171d470eae67d785908395b89b956e9. The develop tree (64f5da77bb9390ac83cc7f117a1a7a82b61c4cb3) was byte-identical to the pre-divergence merge base, so this **preserved all 20 develop-only commits without changing game/source files**. No develop or main ref was changed.
- **Deleted two safe ancestor QA refs** after exact-head leases, proof that they are ancestors of the retained qa/443-n1b-macos-recovery SHA 3d119f4767db06c9d0d814522044436f49dd42d7, and an open-PR dependency check:
  - qa/443-final-native-recovery at 33e15ecb8ca4d24def9deeaadacbcfd367c14fcb;
  - qa/443-lifecycle-persistence at ee671de5b317700beda6fd6b8e43e8be8b4de40f.
  Evidence: one-time GitHub Actions run #42029588171, successful; temporary cleanup workflow removed in the following plan commit.
- **Remaining noncanonical branches:** game/473-sound-unwinnability; qa/443-frozen-native-acceptance; qa/443-n1b-macos-recovery; qa/443-final-data-acceptance. Retain until their unique tests/behavior are reconciled. Keep feature/product-integration until released; preserve the v2 branch.
- Prior verified PR source **324 Python tests PASS each** on Python 3.10–3.13, **71 real Tk tests PASS**, installed editable/wheel/sdist PASS and four package-build jobs PASS. Those are not final extracted-native acceptance.
- Known defects: Buchanan dead-fortress FIDE 5.2.2/6.9 vs live near-twin; macOS overwrite confirmation automation; unimplemented native advanced/offline/process journeys; outdated canonical notes 0001-product.md/0002-structure.md; default-branch Deploy Documentation post-publication PR deployment status API returns HTTP 422, although Pages deploy itself succeeds; five unresolved maintainer review threads; new duplicate DarkFactory fleet issue #493.
- Both game JSONs still have playable:false, publication disabled. Release trust/signing policy remains an owner decision.

### Manual Agent Prompt 0 — Targeted reconciliation and correction contract (NO IMPLEMENTATION)

You are the independent repository-forensics, Python/Tkinter and FIDE correctness specialist.
Repo: marius-patrik/BoardGamesWithQuests. Issue #430, with #473/#477 Chess and #443 native. Read current draft PR #271 **after the 2026-11-05 develop ancestry merge**; refresh all SHAs.

**Read-only tasks (do not modify code, issue state or branches):**
1. Compare qa/443-frozen-native-acceptance, qa/443-n1b-macos-recovery, and qa/443-final-data-acceptance by all changed files and actual function bodies, not counts. Identify each distinct must-keep native harness test/fixture/workflow/package fix, obsolete material and exact conflict. Final-data has the latest ~2,002-line frozen harness but its macOS overwrite Replace AX lookup failed. State precisely what to copy into a current feature/product-integration-based implementation.
2. Inspect game/473-sound-unwinnability; transfer specification for its four valid sourced FIDE tests, adapt historical model.game imports to current model.* layout; do **not** merge its known-red tests without a sound correction.
3. Reproduce/confirm Buchanan dead FEN vs published live near-twin, select a **sound** Chess mating-possibility / impossibility method using the current legal engine. Require legal mate witness for POSSIBLE, sound impossibility proof for IMPOSSIBLE, explicit UNKNOWN otherwise. Determine exact bounded runtime and whether #477 durable pending adjudication is necessary. **If no sound acceptable policy exists, return precise BLOCKED decision** rather than guessing or launching indefinite solver research.
4. Recheck actual source against the prior audit: WCDF 91-ply/reference behavior, generic clocks/quests/persistence, Tk GUI existing source, and 324 Python + 71 Tk passing CI. Add a source change to the register **only for a new concrete, independently reproducible defect**. No broad audit or speculative refactor.
5. Inspect the actual five PR #271 unresolved threads, the two stale canonical notes paths, docs #476 HTTP 422 in Mark only successfully published preview heads as deployed, duplicate fleet review #493 and its generation trigger. Give the **exact source change** or maintainer decision for each.
6. Confirm protected-branch integration history is up to date and that the remaining noncanonical branches have no unsaved essential history; do not delete them now.

**Deliver one FINITE implementation register:** ID, issue, current wrong result, independently expected result, minimum file paths, exact correction, dependency, focused regression, ready/blocked. Explicitly classify no-change items. Include the complete file-level native branch salvage map, selected Chess design or precise owner decision, GUI/docs/CI corrections, and remaining branch deletion conditions. **Do not commit, deploy, open PR, or run final acceptance.**

**Exit:** Prompt 1 can perform bounded fixes without another general investigation. If a mandatory Chess product decision remains, request explicit maintainer approval before that part of Prompt 1.

## 1 — Make all definitive corrections and integrate incrementally

### Manual Agent Prompt 1 — Production and native finishing (IMPLEMENTATION, focused tests ONLY)

You are the principal Python/Tkinter, JSON rules engine, GitHub Actions/native QA and integration engineer.
Repo: marius-patrik/BoardGamesWithQuests. Own issues #430, #473/#477, #443, #462/#476 and any confirmed defect register owner. Read the approved Prompt 0 correction register and exact latest PR #271 head. **Do not make unapproved design decisions**; do not rebuild or redesign the working game.

**Execute the register in dependency order:**
1. Recover the accepted, unique native QA files and fixtures from qa/443-final-data-acceptance and qa/443-n1b-macos-recovery onto a current PR #271-based topic branch. Selectively preserve valid qa/443-frozen-native-acceptance behavior not in later branches. Do not blindly merge stale branches.
2. Bring the four sourced Chess regressions from game/473-sound-unwinnability into current module paths **together with** the approved sound FIDE outcome fix, or report a precise Chess product/proof blocker. Use existing legal-move authority and JSON rules; never hardcode Buchanan, treat exhausted search as proof, or silently turn UNKNOWN into win/draw. If approved, implement minimal durable timeout/replay changes and cover persistence, clock freeze, retries and existing save compatibility.
3. Correct only independently demonstrated WCDF/session/quest/persistence/GUI defects (if register lists any). Existing acceptance has not demonstrated that these systems need rebuilding.
4. Repair the proven macOS overwrite Replace/Cancel automation, then implement the missing advanced native Chess promotion, Draughts multiple captures/crowning, draw offers/claims, invalid/cancelled file handling, offline and process-tree checks. Retain existing passing gameplay/settings/save→exit→reopen journeys. Do not fake a native PASS or modify game source to fix an automation bug.
5. Update canonical .agents/notes/0001-product.md and 0002-structure.md to src/main.py and data/{chess,checkers}.json; regenerate docs. Repair the default-branch Docs deployment post-Pages preview-metadata GitHub API HTTP 422 and add focused diagnostics. Preserve Pages-through-Actions.
6. Reconcile the five exact maintainer review threads with present source; correct only still-unsatisfied requirements; do not silently resolve maintainer-owned reviews.
7. Stop generation of obsolete DarkFactory fleet review issues like #493 by the smallest policy/configuration correction approved by the owner, without disabling unrelated quality/release CI.
8. Set playable:true in BOTH bundled game definitions only **after** their required accepted rules and UI evidence is sufficient and **before** freezing the final integrated candidate. Keep publication disabled until owner approves release.
9. For EACH accepted patch, run direct focused regression tests, inspect changed files, preserve the latest integration HEAD (fast-forward/lease; no force push), integrate into sole draft PR #271 and record source SHA. **Do NOT run comprehensive final 4-OS/Python/UI acceptance**; that belongs only to Prompt 2.
10. After each accepted integration, compare its source branch to the integrated head, preserve uniquely needed work, then delete genuinely redundant temporary branches. Do not delete v2, main, develop or PR #271 head branch. Return exact remaining branches and issue states.

**Deliver:** one completed fixed-ID register; exact diff and integrated PR SHA; focused tests; native harness journey inventory; documented remaining external decisions; safely deleted branch SHAs. No protected merge/release. If a mandatory blocker remains, return NO-GO with the one precise decision needed, not another indefinite audit.

**Exit:** one issue-reviewed final PR #271 candidate ready for Prompt 2, no unintegrated required v1 commits, no unimplemented mandatory J1–J8 harness scenario.

## 2 — Single final acceptance → approved v1.0.0 release → finish cleanup

### Manual Agent Prompt 2 — Independent release auditor and release operator (GATED)

You are the independent Chess/WCDF Python/Tkinter and native cross-platform release verification engineer. Repo marius-patrik/BoardGamesWithQuests. Issues #444, #445, #430. Refresh the **exact final frozen** PR #271 SHA, compare to Prompt 1 accepted register and inspect source. **Read-only until explicit maintainer GO** for EACH protected merge/release/destructive operation.

**ONE comprehensive final acceptance on ONE source SHA:**
1. Verify full Chess FIDE special moves, repetition/50/75-move rules, checkmate priority, sound dead/live/flag-fall behavior, claim/offer/resignation, independent complete games; verify full WCDF movement, mandatory/multihop/deferred captures/crowning, 91-ply reference game, terminal outcomes and draw claims.
2. Run governed full Python tests on **3.10, 3.11, 3.12, 3.13**; exact collected/pass/skip/fail counts. Verify public DesktopSession clocks, quests, history, replay, idempotency, bad inputs, atomic saved games and actual save→new process→reopen→continue.
3. Run **real** Tk GUI acceptance at supported viewports/board sizes, actual pointer moves and modal controls; screenshots/interaction evidence. Verify editable, wheel, sdist and installed CLI in clean environments.
4. Build/extract/source-match native archives for **Windows x64, macOS ARM64, macOS x64, Linux x64** and execute J1–J8 on every target: integrity/assets, Chess, Draughts, settings/restart, cancellation/terminal, BOTH games GUI save→full exit→relaunch→open→continue, promotion/multihop/crown/draw, hostile files/offline/process shutdown. Produce exact-SHA per-OS machine-readable PASS/FAIL/BLOCKED, screenshots, logs and SHA256. **Package smoke cannot substitute for actual extracted-app tests**.
5. Verify all five PR review threads addressed, source/generated docs and deployment readiness, issue register, game playable flags, release/provenance policy, signature/notarization requirements, and zero mandatory unverified gates. Output **GO only if all mandatory checks PASS**, else NO-GO with exact failed requirement and focused correction back to Prompt 1. Rerun this **same** full acceptance on the corrected exact SHA, never a new general audit.

**Only AFTER independent GO and separate maintainer approvals:**
6. Approve/merge PR #271 to protected develop; verify resulting develop SHA, required CI and actual default-branch Deploy Documentation success. Create a separate reviewed develop→main PR; obtain approval, enable authorized PrideVer publication; verify v1.0.0 tag, public release, all 4 independent downloads/checksums, actual launch/play and truthful Windows signing/Apple notarization policy.
7. Preserve all v1 history/tags; reconcile unique v2 branch commits and PR #422's dependency on feature/product-integration, preserving v2 history without force-pushing unapproved. Safely delete PR #271 integration branch and any remaining obsolete v1 refs, closing completed v1/ops issues only after verified acceptance. **Final branch set exactly: main, develop, feat/independent-server-web-native-bootstrap. Final OPEN issue set exactly: #348.** Keep closed issues/PR history.

**Deliver:** one exact-SHA comprehensive GO/NO-GO report, fully evidenced approved release if authorized, final before/after branch/issue inventory. Stop at each missing approval, missing signing policy, unproven Chess result, or unverified native platform; do not claim release or cleanup success prematurely.

---

**Approval:** This is a **working draft**, not permission to dispatch Prompt 0/1/2 or release. The maintainer's 2026-11-05 instruction specifically authorized develop history reconciliation, two verified QA ancestor deletions and this plan update. Completed repository actions are recorded above; future destructive work remains separately gated.