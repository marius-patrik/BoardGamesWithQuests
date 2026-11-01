# BoardGamesWithQuests v1.0.0 — definitive remaining execution plan

**Authority:** .agents/GOAL.md and issue #430. **Canonical integration:** draft PR #271 -> protected develop. **Release:** a separately approved develop -> main PR followed by PrideVer. **Status:** NO-GO.

**This document supersedes the previous chronological dispatch notes and speculative next-step advice.** Evidence and earlier attempts remain in issues, CI logs and SCRATCHPAD.md. Do not add new feature requirements, start another general audit, or invent a second product integration PR. Change this plan only for an actual reproduced blocker, a newer explicit maintainer instruction, or an approved change in the frozen product goal. Changes must state why, the affected gate, and the evidence.

## Verified baseline — 2026-11-01

- Canonical product SHA before this plan: f685c6b276fa015749550c62c65fd97a1a6f2d13. **9/9 applicable GitHub Actions workflows SUCCESS on this SHA.** This proves the governed source, gameplay, Tk/Xvfb and native **PACKAGE** checks, not a full extracted-native acceptance certificate.
- One JSON-configured engine, Tkinter Canvas, two-sided player/quest GUI, clocks, history, settings, local persistence, full source-tree migration and four-platform package creation have been implemented on PR #271.
- Both bundled game definitions still declare playable: false; do not change this until their respective certification gates are met.
- Exactly **five unresolved maintainer PR #271 review threads**, two already substantially addressed (obsolete games initializer and GameScreen composition), three demanding NEW final resource/entrypoint layout (data/chess.json, data/checkers.json, src/main.py).
- Native #443 **not passing**. N1B isolated branch qa/443-n1b-macos-recovery at 3d119f4767db06c9d0d814522044436f49dd42d7; exact run #41304444805 is COMPLETE FAILURE: Windows and Linux BLOCKED at intended incomplete-journey gate; macOS ARM64 FAIL board not visually observable; macOS x64 FAIL chess persist-move-1 unchanged at square (6,4). The previous macOS file-picker race was real, but its correction did not certify N1B.
- #437/#449 WCDF engine corrections are mostly integrated; independent final reference certification remains. #436/#473/#477 FIDE dead-position and timeout correctness remains an explicit P0 blocker. #440, #442/#450, #444 and #445 are not closed.
- Existing Python release publication is **disabled** in repo.dfconfig. No tag, protected promotion or release publication is authorized.

## Non-negotiable v1 scope (no new features)

Deliver the *existing* Python/Tkinter app with orthodox Chess, 8x8 WCDF English Draughts, quests, clocks, history, local saves/settings, existing pointer UI and four usable downloadable native archives (Windows x64, macOS ARM64, macOS x64, Linux x64). Rulebook correctness and actual native use are mandatory, not optional preview substitutions. No web/server, Tauri, database migration, export expansion, new board keyboard mode (#448 deferred), aesthetic redesign, alternative game engine or v2 PR #422 integration.

## Execution contract — applies to EVERY work package

1. **Exactly one writer per overlapping source area.** Task work in one issue-bound isolated branch based on the *latest accepted PR #271 source*, with an explicit changed-file allowlist. Read-only evidence gathering may run in parallel. Never start the next writer on obsolete module paths. No parallel GUI, JSON/model, or native packaging writers.
2. Before coding, write the failing observable contract and independently sourced expected result in the owning issue. Do not add new unspecified gates. Implement the smallest coherent correction; retain all already proven behavior.
3. Before integration, independently inspect the exact candidate diff, affected imports/resources and executable result with **candidate SHA, commands, per-OS/Python results, relevant artifacts and FAIL/BLOCKED/NOT RUN**. Reject unproven behavior, disabled assertions, fake green, untested source, and stale generated diagrams.
4. Merge only accepted source into existing DRAFT PR #271 with a verified head lease; regenerate diagrams from **combined** source and check its exact new HEAD. Candidate CI never substitutes for combined-head CI. On failure, reproduce and repair the *same issue* rather than spawning another sweeping dispatch.
5. No production mutation outside its task owner; no automatic issue closure from a green workflow. Resolve PR inline threads only after the maintainer verifies the code and agrees. Close individual issues when their documented exit gate passes.
6. A new issue/dispatch is permitted only for a **specific reproducible defect that blocks an existing gate**. It must name the failing test, exact source SHA, owner, affected files and exit condition. No extra general audits or branch-per-investigation churn.
7. STOP on known wrong game results, failed required OS, unproven FIDE conclusion, security regression, incomplete user data recovery or missing maintainer authorization. Do not downgrade the release contract implicitly. Preserve evidence and report precisely what blocks it.

## W1 — Finish the five outstanding maintainer review threads (#462)

**Order:** FIRST. **Owner:** single structure/package writer. **Input:** latest PR #271. **Output:** one coherent change on an isolated branch, then independently integrated and reviewed.

- Implement the latest explicit maintainer layout: move the *canonical unchanged JSON* from games/chess/config.json and games/checkers/config.json to **data/chess.json** and **data/checkers.json**, eliminate obsolete subfolders/package. Update model.games, model.resources, validation/loading, all tests, setuptools/pyproject metadata, PyInstaller resource manifest, frozen integrity checks, installed distribution checks, generated diagrams and documentation. Keep game selectors chess/checkers and reject untrusted user-path substitutes.
- Rename **src/boardgameswithquests.py -> src/main.py** as requested. Keep the installed app/CLI identity **boardgameswithquests**, point its gui-script and PyInstaller entrypoint at main:main, verify python -m main --check and installed boardgameswithquests --check. Do **not** add a second legacy entrypoint without a specific real compatibility requirement.
- Verify existing src/view/screen.py composes exactly ONE GameScreen and ONE existing Canvas without duplicate application/game authority. Verify the old src/games/__init__.py no longer exists; address these two already-implemented threads with evidence rather than gratuitous rewriting.
- **Exit gate:** zero stale imports/paths; source, clean editable, wheel and sdist installs outside checkout all load both definitions and execute/replay real Chess and Draughts moves; existing saved sessions reopen without changing the serialized game identities; full Python 3.10–3.13 governed matrix, real Tk screenshots/interaction, and all four native **build + frozen --check** jobs pass on the candidate and exact combined HEAD. Resolve all FIVE PR inline threads after maintainer confirmation. Close #462 only then.
- Freeze the completed source layout. **Do not edit native #443 automation simultaneously**; its isolated N1B code will be selectively adapted to this final layout in W2.

## W2 — Finish real extracted-native acceptance (#443)

**Dependency:** W1 integrated. **Owner:** one native QA/packaging writer, exclusively under .github/tests/frozen_native_acceptance.py, native workflows and necessary packaging script adjustments. **Recovery input:** qa/443-n1b-macos-recovery SHA 3d119f4767db06c9d0d814522044436f49dd42d7, not a new harness. Its useful files must be ported to a new branch from the final W1 product HEAD. Prior M/N1 branches are provenance only.

1. Diagnose both latest real macOS failures using run #41304444805 screenshot and native-result artifacts: ARM64 board-observation failure; x64 chess move visually unchanged at (6,4). Distinguish window focus, native modal, pointer mapping, asynchronous dialog and true production bug. Fix test code only where proven; if the app is wrong, open a tightly scoped production fix and rerun.
2. Define and run **the same eight mandatory native journeys on EACH OS** using the actual extracted application and pointer/native dialogs:
   - J1 Archive/source/version/architecture/SHA256 sidecar, frozen --check, both bundled definitions, missing/altered resource rejection.
   - J2 Native game chooser and Chess legal moves + capture, with visible board/turn/history changes.
   - J3 Draughts legal move + compulsory capture, with visible board/turn/history changes.
   - J4 Settings Save/Cancel and restart persistence, including board sizing/coordinates.
   - J5 New Game and resignation cancellation followed by continued gameplay; accepted resignation/terminal feedback and clean exit.
   - J6 **Both games:** Save from GUI -> terminate OS process -> restart -> Open through GUI -> independently compare board, side, revision, history, clock/quest state -> make next legal move.
   - J7 Native advanced Chess promotion and Draughts full multihop/crowning; eligible/ineligible draw offer/claim flows through UI. Use independently validated saved-position fixtures **loaded via the UI** when reaching these states from the opening is impractical; never bypass the GUI for the action under test.
   - J8 Cancelled/invalid Open/Save, preserved active game and original file on failure, offline gameplay without network dependency, no orphan process/modal after exit.
3. Keep machine-readable result PASS/FAIL/BLOCKED/NOT EXECUTED per journey and per OS. A platform is PASS only if J1–J8 all PASS on the **same exact source SHA**; screenshots, native result JSON, build manifest, process logs and archive hashes are retained. Native package build or GUI smoke alone does not count.
4. Signing/trust: record Windows Authenticode and macOS Developer ID/notarization/quarantine truthfully, and obtain an **explicit release-policy decision** if their absence prevents publishing. Do not call an ad-hoc macOS signature notarization or accept a silent bypass.
5. **Exit gate:** 4/4 extracted targets pass mandatory J1–J8, on final integrated source; accepted QA workflow/tests integrated into draft PR #271 and re-run against its exact HEAD. Close #443 only then.

## W3 — Certify English Draughts, no new engine (#437 and #449)

**Dependency:** W1 data path finalized. Can run reference inspection concurrently with W2, but exclusive ownership for any shared model/JSON changes.

- Check unchanged 8x8 WCDF legal-set/oracle, short kings, compulsory alternate capture chains, deferred captured-piece occupancy, no re-capture, crowning ends capture sequence, last-piece/no-move outcome, draw by agreement, threefold and 40-move no-progress claim, illegitimate claims, timeout, rollback, idempotency and replay.
- Replay the existing published **91-ply Tinsley–Long** reference without filtering the shipped rulebook; supplement with independent legal-route and draw-boundary sources; include one complete terminal game and real DesktopSession + Tk consumer checks.
- **Exit gate:** independently sourced expected/actual matrix and all relevant tests passed on complete unmodified production rules; only correct demonstrated defects. Enable checkers playable: true after all its gameplay/UI requirements pass and rerun full matrix. Close #437 and #449 with evidence. Do NOT turn a passing partial position into a claim of entire rulebook certification.

## W4 — Resolve Chess FIDE soundness and timeout adjudication (#477, #473, #436)

**Dependency:** W1 finalized; serialize all shared model/game writes with W3. This is the **longest uncertain critical-path technical problem**. Do not make an unsupported algorithm promise.

- **W4A: approve contract #477 before coding.** Obtain/review Dispatch K's complete 405-line design artifact (the handoff summary is insufficient). Record an explicit maintainer-approved decision for durable pending timeout on restart, transaction/acknowledgment and disk-error ordering, clock suspension, participant/arbiter authority, replay/idempotency, legacy snapshot migration, UI pending display, permitted actions, resource budget and supported game-state input. Do not add unconditional autosave to every move without deciding its intended durability semantics.
- **W4B: sound proof obligation #473.** Use one authoritative rules/transition system. Distinguish **FIDE 5.2.2** (neither player has any legal path to mate) from **FIDE 6.9** (non-flagged player has no legal path to mate). Formal result types are proved-impossible / witnessed-possible / unknown. A mate witness must replay legally; impossibility must come from an independently checkable complete proof or sound abstraction, **not** arbitrary search exhaustion, material/blockade heuristic, CHA corpus labels alone, or a FEN-specific exception. Preserve the Buchanan dead fortress and proven mate-possible near-twin tests; record that orthodox-opening retro-reachability of the published fortress has not yet been established. Check checkmate vs 75-move precedence.
- **W4C: implement approved lifecycle and evaluator**, in minimal engine-neutral modules, with durable pending state if unknown; no default win/draw on unknown, no invented arbiter authority, no duplicate game engine. Add tests for flag side, deadline, pending restart, missing/full disk, duplicate action/revision, rollback, forged evidence, saved-session v1 compatibility, cross-game isolation and actual UI recovery.
- **W4D: independent conformance** on Chess complete bundled JSON: standard movement, king safety, castling/en passant/promotion, legal move sets, repetition/50/75-move, claims and agreement, mate/stalemate, dead positions, timeouts, at least one independently referenced complete terminal game, session replay, native GUI relevant actions and Python 3.10–3.13.
- **Exit gate:** zero known incorrect result in the defined v1 Chess domain, the published dead/live adversarial cases handled soundly, *all supported* reachable positions obey FIDE outcome semantics, pending states are explicit/recoverable whenever proof is inconclusive, and all session/gui/persistence tests pass. Only then enable chess playable: true and close #477, #473, #436 as their separate proofs warrant.
- **Unresolvable branch:** if no feasible sound correctness method can meet the frozen full-rulebook requirement, record the formal blocker and leave v1.0.0 **NO-GO**. Do not silently narrow FIDE, drop the regression or ship a false certified result. Any changed product requirement needs the maintainer's explicit separate approval.

## W5 — Close code quality and test architecture (#440, #442, #450)

**Dependency:** W3/W4 substantive gameplay changes completed; W2 native acceptance harness stabilized. **Owner:** one QA writer and, separately/sequentially, one source cleanup writer.

- #440: inspect pre-existing audit P0/P1 findings against **actual final code** and document a finite per-file RETAIN/FIX/DELETE disposition. Remove real obsolete/duplicated implementation, fragile imports and misleading comments; no new conceptual abstractions, broad rearchitecture or style-only churn.
- #442/#450: inventory all existing pytest node IDs/CI selectors; map each to an independent public session, rules or actual GUI/native acceptance oracle; RETAIN/REPLACE/DELETE with traceability. Remove redundant tests only AFTER their replacements reproduce meaningful failures and prove the same contract. Retain essential security/math diagnostics. No self-generated expected legal outcomes, hidden fixture rule pruning, false skips or unsafe timeout waivers.
- **Exit gate:** no unresolved audit P0/P1, no lost verified behavior, Python 3.10–3.13 governed suites, 71+ previously covered real Tk behavior (counts may change only with explicit mapped replacement), installed-dist and four-platform extracted tests re-run on integrated final HEAD. Close #440, #442 and #450 only on evidence.

## W6 — Finish UI review and reconcile PR #271 (#454, #462)

**Dependency:** W1–W5 complete. **Owner:** integrator plus independent maintainer reviewer.

- Inspect final 840x640, 1024x768, 1100x760 and 1440x900 real Tk screenshot sets for Chess/Draughts; settings 32/56/88px, board/pieces, both own-quest panels, history long-scroll, terminal feedback, modal focus and resize. Accept existing design if functional/readable; fix only observable regressions or severe clipping. No further redesign.
- Verify PR #271's five review threads actually match current source and are maintainer-approved/resolved. Source structure, docs and AST/UML generated outputs must describe actual code. No unmerged competing product PR or stale source aliases.
- **Exit gate:** #454/#462 CLOSED with documented visual review and review-thread resolutions. PR #271 remains DRAFT until W7 independent audit and explicit approval.

## W7 — One independent release audit (#444)

**Dependency:** W1–W6 integrated and their checks pass on one final **frozen source SHA** (not merely predecessor/candidate). **Mode:** read-only audit, no source rewrite.

- Construct a source-SHA keyed evidence matrix for both game rulebooks, authoritative clocks/quests/history, session data migration, security, real Tk, installed editable/wheel/sdist, and native J1–J8 on each of four platforms; verify actual uploaded screenshots/JSON/artifact hashes. No FAIL/BLOCKED/NOT RUN for any mandatory gate.
- Verify repository-generated docs, PR's precise diff, branch protections, version config and signed/unsigned disclosure policy. Independent review of security/regression, no skipped mandatory checks.
- **Exit gate:** explicit **GO** report for the exact SHA and no P0/P1 release issues; otherwise return a *single precise correction* to its issue owner and repeat only affected plus required integration gates. Close #444 only after GO.

## W8 — Controlled approved promotion and public release (#445)

**Dependency:** W7 GO, full CI, native artifact matrix, resolved PR review, and the maintainer's explicit authorization of the final reviewed PR #271 SHA.

1. Maintainer approves and merges **only** PR #271 into protected develop using the authorized GitHub path. Check resulting develop SHA and run all mandatory validations again.
2. Create/review one **same-repository develop -> main** release PR, obtain a **second explicit maintainer approval**; never bypass protection, proxy review or merge unattended.
3. Only after authorization and verified release policy enablement set repo.dfconfig python publication to true through the reviewed process, reconcile PrideVer as sole v1.0.0 version authority, and promote to main.
4. Confirm tag v1.0.0 points to the authorized main SHA and public release contains **four** architecture-correct archives, SHA256 sidecars, release notes and a clearly truthful signing/notarization statement. Independently download assets and execute representative extracted install/play checks.
5. **Exit gate:** user-accessible, verified v1.0.0 release with four functional artifacts, exact provenance, approvals and issues #430/#445 closed. No v2 work bundled.

## Dependency graph and work scheduling

W1 -> [W2, W3, W4 contract/proof research]. Only one writer on common model/JSON; W2 owns native test/packaging, W3 owns WCDF definition/reference, W4 owns Chess and generic terminal code **after W3 writer hands off**. W2/W3 may gather independent evidence in parallel. [W2 + W3 + W4] -> W5 -> W6 -> W7 -> W8.

**NEXT ACTION:** W1 final source layout. Preserve N1B's current recovered native test work but STOP editing it until W1 source integration; then adapt it once and complete W2 against final paths.

## Reporting discipline

For each W package, attach a single short status record to its **existing issue**: owner/branch, baseline and final SHA, changed-file allowlist, externally grounded acceptance cases, exact commands and four-platform/Python results, artifacts, integrated SHA, review disposition, remaining blocker and NEXT OWNER. Maintain **PLAN** as the only overall schedule and **TODO** as the short live queue; historical evidence lives in issue comments/SCRATCHPAD, not newly appended master plans. A green prior run never proves a newer SHA. No new 'all done' report without all explicit gates.