# BoardGamesWithQuests v1.0.0 — canonical completion and dispatch plan

**Current checkpoint:** 2026-11-04. **Decision:** NO-GO, no production merge or publication authorization.
**Authority:** [GOAL.md](GOAL.md), [master issue #430](https://github.com/marius-patrik/BoardGamesWithQuests/issues/430). This file is the **only operative phase plan**; [TODO.md](TODO.md) is the active work queue. Superseded investigation histories live in Git history, issue comments and SCRATCHPAD, not as competing future instructions here.

## 1. Frozen product and non-negotiable contract

Deliver the existing Python/Tkinter app as **v1.0.0** with orthodox FIDE Chess, 8×8 WCDF English Draughts, the recovered declarative JSON engine, local two-player sessions, clocks, quests, history, bounded atomic save/open/replay, validated settings, actual mouse-driven Tkinter play and **four usable extracted native downloads** (Windows x64, macOS ARM64, macOS x64, Linux x64). No unreviewed change of FIDE/WCDF rules, incomplete game flag, or native gate is permitted to count as finished.

Preserve **one** authoritative manager/session/rules interpretation path, original Tkinter Canvas and two-sided player/quest UI. The canonical game assets are `data/chess.json` and `data/checkers.json`; the only source entrypoint is `src/main.py` and installed command is `boardgameswithquests`. All tests remain in `.github/tests/` and scripts in `.github/scripts/` until the maintainer expressly resolves contrary review feedback and validates every consumer. Future design contracts belong in owning issues, not generated architecture documents.

Explicitly excluded: multiplayer, FastAPI, Supabase, React/Bun client, Tauri, v2 PR #422, new export features, broad redesign, another game engine and keyboard-controlled board navigation (#448, deliberately deferred). Do not claim full keyboard-only accessibility. **Draft PR #271 is the sole canonical v1 product integration PR.**

## 2. Verified baseline and release blockers

| Reference | Exact evidence / current classification |
| --- | --- |
| Product integration | `feature/product-integration` PR #271 at `41f15fd86d301026a34cd5e2ad172cfc2e44a258`, **DRAFT**, unmerged, five unresolved maintainer review threads. Protected `develop` and `main` untouched. |
| Source layout | W1 flat data/main migration integrated at `a117efaba454433b1caa19607fd45498178f9933`, 9/9 relevant workflows succeeded on **that SHA**. W1 source changes complete; review acceptance remains open (#462). |
| Integrated source CI | At `41f15fd8`, nine ordinary integration workflows succeeded, but native **package** run #41625688688 did **not** fully pass: Windows x64, macOS x64 and Linux x64 passed packaging; macOS ARM64 was cancelled. Do not substitute this for extracted-native acceptance. |
| Native QA | Isolated `qa/443-final-data-acceptance` at `1e49fa588732a8ec307cc8332272b27398ed7b2a`. Exact run [#41625407817](https://github.com/marius-patrik/BoardGamesWithQuests/actions/runs/41625407817) is COMPLETE/FAIL at workflow level: Windows and Linux **BLOCKED** only on missing advanced journeys after nine implemented journeys passed; macOS ARM64/x64 **BLOCKED** in `invalid_user_files_and_failed_save` after eight earlier journeys passed. Both macOS runners report `native overwrite Replace button unavailable: native overwrite Replace control not exposed (-2700)`. The OS overwrite alert remains visible; this is a measured QA automation/accessibility failure, **not proven Tk rendering failure**. |
| Native unfinished | Promotion, full WCDF multihop/crown, draw controls, offline/process cleanup and final trust acceptance not yet implemented in the extracted-app harness. J1–J8 have **NOT** all passed on any one SHA. |
| WCDF | Broad WCDF implementation and 91-ply reference acceptance integrated. Prospective threefold intended-move selection now exists in `src/view/screen.py`; old issue comments saying otherwise are obsolete. Independent final rulebook/GUI/native certification pending (#437, #449). |
| Chess | Real FIDE counterexample: Buchanan published dead fortress receives a timeout **win** rather than draw; reference live near-twin permits mate. Known proof/unknown-outcome blocker persists (#436, #473, #477). FIDE complete compliance cannot be claimed; proof algorithm and durable pending adjudication are not implemented. |
| Rulebook flags | Both canonical JSON definitions still say `playable: false`. Do not change without separate completed independent acceptance. |
| Release | PrideVer Python publishing is disabled in `repo.dfconfig`; no authorized v1.0.0 protected promotion, Windows signing or Apple Developer ID notarization. |
| Governance | #476 documentation-deploy failure is a separate open issue requiring evidence-based triage; current README projection still names the former `src/boardgameswithquests.py` entrypoint and should be corrected at its `.agents/notes/` source. |

**Priority:** Chess soundness is the largest unbounded technical risk, so begin **read-only feasibility and contract verification immediately**, in parallel with native QA implementation. Do not make it wait behind packaging. Progress is evidence-gated, not date-gated.

## 3. Agent dispatches and exclusive ownership

The orchestrator owns the canonical PLAN/TODO, issue contracts, source-owner lock, cross-branch reconciliation, independent diff review and protected promotion requests. Agents own bounded work **only** through issue-based dispatch with the authority below. **At most one writer per overlapping path.** Running a GitHub Actions workflow does not imply the agent actually completed a task; check the central dispatch/agent result.

| Lane / dispatch | Parent issues | Allowed work now | Forbidden overlap |
| --- | --- | --- | --- |
| **N — Native execution** | #443 | **One exclusive writer** on existing `qa/443-final-data-acceptance`: `.github/tests/frozen_native_acceptance.py`, `.github/workflows/desktop-native-acceptance.yml`, `.github/workflows/desktop-build.yml`, `.github/scripts/package_desktop.py` **only when needed**. Inspect real PNG/JSON failure evidence and finish J1–J8. | Cannot touch `src/`, `data/`, public release, protected branches or bypass native assertions. Production defects go back to orchestrator for a separate bounded owner. |
| **D — WCDF conformance** | #437, #449, #438 | Independent **read-only** reference/rules/actual GUI review. Produce exact legal set, full-game, terminal and claim matrix; identify only real failures. | No model/JSON/GUI/packaging edits until its source ownership is granted. No claiming `playable:true`. |
| **C — Chess mathematics & adjudication feasibility** | #473, #477, #436 | Independent **read-only** proof algorithm + full proposed pending-timeout contract review; independently distinguish sound proofs, replayable mate witnesses, deterministic unknown, resource budget and durable event ordering. | No speculative model writes or copy of an unverified external solver; no immediate outcome for UNKNOWN. Source implementation requires approved #477 decision and one exclusive owner. |
| **Q — QA/quality reconciliation preparation** | #440, #442, #450 | Independent **read-only** final source/test inventory, pytest node-ID and external-oracle mapping, finite RETAIN/FIX/REPLACE/DELETE disposition and precise blocker list. | No mass deletion and no source changes until gameplay/native work stabilizes. |
| **R — Release/UX readiness** | #441, #454, #462, #444, #445, #476 | Read-only five-thread reviewer dossier, final UI screenshot plan, external signing/credential/trust decision sheet and docs workflow root-cause triage. | Never self-approve/resolve maintainer review, rewrite release policy, merge, sign without credentials or publish. |

**Scheduling:** Wave 1 immediately activates N (writer), D (read-only), C (read-only); Q and R may prepare read-only evidence without blocking Wave 1 but must not spawn overlapping source writers. Wave 2 grants one writer at a time on shared model/JSON/GUI once D/C findings and #477 architecture decision are accepted. Wave 3 performs selective integration and whole-product acceptance. Wave 4 performs independent release audit and separately approved promotion.

**Agent output contract:** owning issue; branch and starting/final full SHA; exact changed-file allowlist; commands and external reference oracles; per-Python/per-OS PASS, FAIL, BLOCKED and NOT RUN; screenshots/JSON/CI/artifact links; verified and unverified behavior; earliest outstanding blocker; explicit ACCEPT/REJECT/NO-GO recommendation. No agent is authorized to merge PR #271, modify `develop`/`main`, delete repositories or publish releases.

## 4. Acceptance work packages and dependencies

### N — Complete extracted native verification (#443) — implementation now

Keep the current harness and its already verified journeys; repair only reproducible native synchronization or UI defects. Current macOS failing site is the OS-owned Replace/Cancel confirmation in failed-readonly-save. An Accessibility `entire contents` lookup for a button named `Replace` failed on both architectures; examine PNG + actual AX hierarchy/focus/window identities and use a robust observed control, not an arbitrary delay or suppressed assertion. The read-only target must remain byte-identical, app state must survive and further play must proceed.

**J1–J8 must be PASS individually on all four extracted binaries, same exact candidate/integration SHA:**
1. Verified archive architecture, source/build SHA and version, checksums, `--check`, both trusted bundled JSON files and missing/corrupt resource rejection.
2. Native game chooser, Chess real pointer moves/captures, visible board/turn/history.
3. English Draughts compulsory capture and actual pointer move-route selection with visible board/turn/history.
4. Native Settings Save/Cancel, board-size/coordinates and preferences across independent process restart.
5. Dirty-game New/Open/switch, resignation cancel and accepted terminal result, preserved interaction and clean exit.
6. **Both games:** GUI Save→quit→independent extracted relaunch→GUI Open→compare board, player, revision, history, clock/quests→next legal move. Validate actual snapshots, not screenshot alone.
7. Chess promotion, Draughts multihop capture and crown/terminal; positive and negative eligible draw offers, responses and claims through real GUI. Independently checked saved-position fixtures may be imported **through** GUI to reach advanced states.
8. Invalid/cancelled Open and Save, unchanged original bytes and active game on rejection, offline play, no orphan modal/process and provenance/trust inspection.

The harness must retain machine-readable per-OS per-journey outcomes, before/after PNG evidence and fail-closed final exit. Do not auto-convert UNKNOWN/BLOCKED into pass. A native **package build** is never proof of J1–J8.

### D — WCDF rulebook closure (#437, #449, #438)

Independently check the shipped complete JSON and public `DesktopSession`: men/kings, short king steps, forced/alternative route captures, deferred occupancy and prohibition of recapture, crowning ends turn, no pieces/no moves, timers, 40-move rule, threefold and intended-move claim, mutual draw, resign, complete 91-ply referenced game, a terminal full game, replay/idempotency, and actual Tk pointer/claims UI. No rule pruning, self-oracle, convenient skip or heuristic. A failing external oracle authorizes a bounded separate correction on the existing integration dependency. Only set Draughts `playable:true` after final native and game acceptance.

### C — FIDE Chess correctness (#477 → #473 → #436)

**First:** review/approve #477 durable adjudication decision **before implementation**: atomic accepted-action/disk-commit relationship, clock suspension, explicit `active → pending_timeout → terminal`, authorization and arbiter policy, user-visible offline pending behavior, v1 snapshot/event migration, crash/restart, idempotent retry, bounded deterministic proof time/memory, missing/full disk and replay verification without rerunning solver. The existing full design is not automatically approved.

**Second:** prove FIDE 5.2.2 global deadness versus 6.9 side-specific flag-fall unwinnability using one trusted move generator. Possible = legally replayable mating witness; impossible = independently checkable sound proof/abstraction; unknown = *not* win/draw. Buchanan fortress must be dead while published live near-twin must preserve possibility. A depth timeout, material heuristic, FEN exception or third-party corpus label is **not** sufficient. Test ordinary play, all special moves, 50/75 move and repetition priority, claims, terminal/resign/timeout, clocks, rollback, replay, JSON inputs and four-platform deterministic behavior. Note published fortress orthodox-opening retro-reachability has not been established.

**Third:** only after separate approval and a proven proof method, one model/JSON writer implements the smallest coherent lifecycle and evaluation changes; an independent validator runs the full affected Python 3.10–3.13 and Tk/native matrix. Do not claim every orthodox position conclusively decidable in a bounded budget; UNKNOWN must remain safe and recoverable. If the frozen v1 full-rulebook goal cannot be proven feasible, preserve NO-GO and request an explicit *new* product-scope decision instead of silently narrowing FIDE.

### Q — Final code and test quality (#440, #442, #450)

Against the *final* integrated code, review known audit P0/P1 findings and enumerate every production file/test node ID/CI selector. Map independently sourced public-session/game/real-Tk/native acceptance to meaningful regression failures. Retain sound security/math unit oracles; replace obsolete/private-shape/self-oracle tests only **after** comparable executable proof exists. Remove duplicated/dead implementation conservatively, regenerate diagrams and source-derived README from canonical notes. Preserve old exported user session compatibility. No large rearchitecture or broad formatting-only churn.

### R — UX, maintainer review and repository hygiene (#441, #454, #462, #476)

Verify real Tk screenshots at 840×640, 1024×768, 1100×760, 1440×900 and 32/56/88px board settings: actual game chooser, two players' independent quest cards, history scroll, different move types, terminal state, dialog focus/cancel, redraw discipline, pointer mapping, error feedback. Require demonstrable failures for cosmetic rewrites.

Obtain maintainer disposition for **five existing PR #271 unresolved inline threads** (`src/games/__init__.py`, `src/view/screen.py`, `data/checkers.json`, `data/chess.json`, `src/main.py`). Address the additional 2026-10-31 review note requesting tests/scripts at root without silently overriding governed `.github/tests/` layout: write a precise conflict/consumer analysis, request a maintainer decision and implement once. Fix stale generated README at its `.agents/notes/` source; recheck #476 documentation deployment instead of ignoring a live default-branch failure. Close historical #438/#439/#441/#454/#462 only after real final acceptance.

### Final integrated audit and release (#444 → #445 → #430)

After N + D + C + Q + R accepted, selectively merge **only independently approved source** into one existing **draft PR #271** under expected-HEAD lease. Regenerate actual-source diagrams/docs; run CI on new **combined exact SHA**: Python 3.10–3.13, clean editable/wheel/sdist outside source checkout, no missing/stale game resources, deterministic replay/atomic rollback, authentic GUI and all four extracted J1–J8 plus release metadata and governance. All mandatory failures/blocks must be zero. Compare shipped artifacts and SHA256 sidecars to exact source provenance.

**Independent #444** must issue a written exact-SHA GO decision; maintainer then explicitly approves PR #271 → protected `develop`. Reverify promoted SHA. A **separate reviewed same-repo `develop → main` PR** and second explicit maintainer approval are mandatory. PrideVer Python publishing remains disabled until authorized; Windows signing and Apple Developer ID/notarization/trust handling require truthful evidence and an explicit external-credential/release-policy decision. On authorized release, independently download all four v1.0.0 artifacts, verify hashes, expected architecture, startup and representative real gameplay before closing #445/#430.

## 5. Integration and evidence discipline

- No competing v1 product PR; task-local temporary CI-only draft PRs may be used if necessary, linked to exact issue and closed **without merge**. Do not create meaningless branches or restart completed source migration.
- A **test being implemented**, `--check` passing, 321 source tests, or four package jobs passing is not native certification. Passes are always SHA-specific.
- External references must be independent of the production rule interpreter. Never rewrite a failing oracle to match the bug; preserve dead/live edge tests.
- Agent dispatch is **explicitly authorized** for bounded, non-overlapping work by the 2026-11-04 owner request. This supersedes earlier blanket "no further dispatches" statements; it does **not** supersede the no-auto-merge, no-rearchitecture and evidence requirements.
- Central CI/issue agent dispatch must show an actual workflow/branch/result to count as launched or completed. Issue comments and labels without an active worker are **prepared assignments**, not proof an agent is executing.
- Do not modify protected branches or releases as part of orchestration. Maintain one dispatch ledger in TODO: READY → DISPATCHED (trigger evidenced) → EXECUTING (actual worker evidenced) → BLOCKED / ACCEPTED → INTEGRATED, with SHA and checks.
- Reporting to the owner must distinguish `[Certain]` observed evidence from `[Likely]` analysis and `[Guessing]` hypotheses. Never offer speculative release dates.

**Current next action:** commit this plan and TODO; then issue bounded dispatches for N, D and C with exact file ownership and acceptance. Verify GitHub workflow actually created worker execution rather than treating a posted assignment as delivery. Continue native evidence review and specific fixes while independent rulebook/solver work runs.
