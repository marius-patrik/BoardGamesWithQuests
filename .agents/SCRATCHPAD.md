# Orchestrator scratchpad — verified observations / open questions

**Snapshot date:** 2026-10-27. Scratchpad notes are operational evidence, not alternative requirements. Canonical release issue [#430](https://github.com/marius-patrik/BoardGamesWithQuests/issues/430).

## Current topology

- Repo default: `develop`; release branch: `main`; single bot-authored desktop draft PR [#271](https://github.com/marius-patrik/BoardGamesWithQuests/pull/271) (`feature/product-integration → develop`). Second open draft [#422](https://github.com/marius-patrik/BoardGamesWithQuests/pull/422) (`feat/independent-server-web-native-bootstrap → feature/product-integration`) is **V2-only and intentionally deferred**. V2 desired design is #348 (39 app tables, 27 app operations; some proposed defaults await maintainer ratification).
- At prior verified *code* SHA `1f6816da13e9d3f73f450c1e2bf8635fe12db860`, eight PR-triggered Actions runs passed (Desktop gameplay/Xvfb/native packaging/quality/docs/release metadata). GitHub's *separate* commit-status API reported `Vercel – boardgameswithquests-api` and `Vercel – boardgameswithquests-web` as **failure**, pointing to provider build-rate-limit/upgrade URLs. Required-protection status **not independently established**. No four-OS extracted frozen GUI user journey has been certified.
- PR #271 review disposition includes maintainer `CHANGES_REQUESTED`; 44 review threads exist and zero are unresolved. Mergeable metadata alone is not approval. No public v1.0.0 release.
- Branch inventory initially contained 18 refs; 14 obsolete task/verification branches were checked and **deleted** with exact-SHA safety and open-PR/protection guards ([successful cleanup run #40468515823](https://github.com/marius-patrik/BoardGamesWithQuests/actions/runs/40468515823)). Temporary cleanup branch self-deleted. **Active refs retained:** `main`, `develop`, `feature/product-integration`, `feat/independent-server-web-native-bootstrap`, `game/438-draw-lifecycle`, `security/439-persistence-hardening` (the last may be pruned after acceptance).

## Code/UX facts needing final proof

- `GameManager` in `src/model/game/manager.py` owns revisioned transitions, clocks, declarations, quests and replay. `DesktopSession` is the sole local authority; GUI consumes detached state. Chess and Draughts JSON both currently say `playable:false`.
- Source `src/view/player_game_view.py` discovers named configured claim rules but `claim_draw` still submits `intended_move:None`; WCDF prospective threefold cannot complete through GUI. No authoritative mutual offer/accept/reject action yet. Assigned upcoming owner #438.
- Chess reference #436: corrected a bad en-passant FEN oracle; 26 candidate tests + 99 existing regressions executed green on Python 3.10–3.13. 33-ply Opera Game fixture integrated. Still missing authoritative FIDE 50/75 boundary, rare dead/timeout mating possibilities and intended-move claims.
- WCDF #437/#449: 263 Python cases per version and a 91-ply sourced game, short kings/capture chain/deferred removal and declarative threefold/40-move claims integrated; generic GUI claim discovery corrected. Re-run complete pointer paths and mutual draw after #438.
- #435 source/frozen-Linux UX audit documented 26 findings/13 screenshots. Responsive 840×640 and terminal safeguards are fixed via #447/#451. #452–#454 still own capture chooser/piece contrast, scrollable quest/history/player presentation, native ttk/modal/idle polishing.
- #439 Dispatch B candidate `8c84d395` has three scoped files integrated at `52043693`: validated bounded duplicate/nonfinite JSON, ancestor symlink/junction and file identity checks, read-only destination refusal, replay-verified saves, and real subprocess Chess/Draughts/settings recovery tests. Earlier candidate's 290 cases per Python version executed; full later/exact integrated-head matrix and Windows/macOS native filesystems still need certification. #439 remains open; final native restart acceptance is #443.
- Tests live under `.github/tests/`; #450 must trace RETAIN/ADAPT/REPLACE/DELETE without replacing external gameplay oracles with implementation-generated expected results.
- Native acceptance #443 must test the *extracted frozen* application on Windows x64, macOS ARM64, macOS x64 and Linux x64. CI packaging/`--check` is necessary but not sufficient.

## Ownership hazards / evidence policy

- #438 and #452/#453 can collide in `player_game_view.py`; sequence writers. #439 may proceed only on persistence modules and its own tests while #438 edits engine/session/view.
- Do not import temporary verify-only workflows/branches into product PR. Automated architecture-diagram regeneration must run on **combined** integration head, never copied from stale task branches.
- A new docs/code commit invalidates a literal 'all exact-head checks passed' claim until checks complete on that new SHA. Don't merge, approve, promote or publish without explicit maintainer native review.
- Maintenance to clarify the master and subordinate issue bodies was applied 2026-10-26: #430 now separates passing Actions checks from failed Vercel statuses; #440 supersedes old '#456 OPEN' claim; #441 supersedes stale '#451 open' and inaccessible-UX-artifact text.
