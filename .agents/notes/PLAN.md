# BoardGamesWithQuests — Consolidated Completion Plan

**Status:** Active implementation plan; architecture approved 2026-10-13, implementation **not** complete.  
**Owner issue:** [#129](https://github.com/marius-patrik/BoardGamesWithQuests/issues/129). **Final test gate:** [#239](https://github.com/marius-patrik/BoardGamesWithQuests/issues/239).  
**Integration branch:** `feature/product-integration`, draft PR into `main`. **Never merge without maintainer approval.**  
**Authority:** Product contract: [PRD](PRD.md). Architectural deviations: [object model](object_model.md). Source reference: [reference diagram](reference_diagram.md). Current progress only: [scratchpad](../SCRATCHPAD.md).

## 1. Goal and constraints

Finish a **playable, correct online two-player** chess/checkers app, game-neutral Python engine, JSON-only game configuration, public free-tier web deployment and Tauri desktop wrapper. Classmates must be able to visit the public URL, enter as guests, create/join a game, play to a result, and reconnect without losing state. Registered accounts also work. No leaderboard, classroom lobby, tournaments, separate rooms, separate desktop GUI or other unrequested product features.

**Principle:** No knowingly incorrect interim production behavior, duplicate configuration architecture, UI pretending to be playable, or unsupported feature advertising. All game-significant defaults come from explicit configuration. Original supplied reference drawings are immutable; changes require documented, approved deviations. Tests measure behavior.

## 2. Repository and deployed architecture

```text
packages/
  engine/     Python board/pieces, declarative rules/quests/hooks, moves, lifecycle
  chess/      config.json, game-owned serializers; no engine chess special cases
  checkers/   config.json, game-owned serializers; no engine checkers special cases
  server/     Python FastAPI, Supabase integration, player authorization, game transactions
  web/        React + TypeScript + Rsbuild + Bun + Tailwind + shadcn/ui + Motion + Lucide Animated
  desktop/    Tauri wrapper loading the same deployed web URL; no second frontend
```

**Vercel:** Two projects from the same repo: static Rsbuild frontend and Python Functions/FastAPI API. **Supabase:** Auth (including anonymous guests), Postgres authoritative persistence, Realtime notifications. This does not introduce a continuously running Python server or browser-resident Python. Tauri loads the hosted web app and needs a network connection. Pin/lock dependencies and generated API types. Verify Vercel Python runtime/package constraints rather than assuming deployability. No paid plans or paid resources without authorization.

**Boundary:** Engine knows neither HTTP, frontend nor database. Server imports engine and verifies identity, game membership and access. Browser owns presentation state only. Supabase Realtime distributes committed updates; never trust broadcast messages as move authorizations.

## 3. Declarative configuration — highest architecture gate

Every shipped game uses validated **`config.json`** specifying board dimensions/placements, piece glyphs and movement/attack capabilities, clock parameters, rules, quests, hooks, conditions/effects, outcomes and supported exporters. Users may duplicate/edit their own configurations; versions are stored as validated JSON in Supabase and running games pin an immutable snapshot. The shipped chess/checkers defaults are immutable. There is **one** game discovery, config parser/validator and loader. Remove competing `runtime_configuration.py`, `legacy_games.py`, `legacy_app.py`, `packages/default.json`, and parallel config/discovery logic.

**No user-authored executable code:** no Python or JS editor for rules/quests, dynamic imports of user-supplied modules, unsafe eval/exec, or writable executable config directories. Declarative JSON composes **trusted generic Python primitives**; extensible rules/quests are data, not user code. Generic behavior includes board queries, selections, vectors/attacks, captures, ownership, turns, logical AND/OR/NOT, comparisons/counts, rule state, conditional effects, progress/rewards and outcome proposals.

Keep the five conceptual hooks: `permits_move`, `available_moves`, `outcome`, `on_move_made`, `status`. Rules propose and the engine coordinates. Design a bounded and typed JSON AST/schema (no arbitrary string expressions); validate nesting, supported ops, target references and complexity. Test representative complex chess/checkers rules *before* freezing schema, especially castling, en passant, pawn promotion, attack/check, repetition, mandatory multi-capture and outcome precedence. If an operation is missing, generalize primitives rather than hardcode a game identifier. No promise of arbitrary computation from finite JSON primitives.

## 4. Shared engine and game conformance

- **Board/pieces:** generic geometry, occupancy, piece capabilities and transaction-safe state change; no implicit 8×8, chess setup, royal label, FEN glyph or ten-minute timer. Game-specific piece declarations/logic are in JSON and game-owned assets; avoid concrete chess classes in engine.
- **Move commit:** one authoritative `GameManager`/domain boundary handles candidate generation, configured legality, turn and owner constraints, mutation, rule effects, quest progress, clock state, terminal result and ordered game history. A user registry must never independently call `Move.execute`. Rejected/invalid input cannot mutate state or return false success.
- **Results:** one result type with winner, cause, kind and deterministic precedence. No universal checkmate label; correct draw and timer conditions.
- **Session:** exactly one selected config snapshot and board, two player positions and per-player rule/quest state; session can serialize and reconstruct across serverless invocations.
- **Time:** configured initial/increment and trusted timestamps, reject invalid or negative time, enforce flag falls without a continuously running process.
- **Users:** prevent duplicate identities and invalid player associations. Supabase Auth owns registration/login; engine references stable identities without authenticating them.
- **Quests:** JSON hook definitions, per-player per-game progress, persistent user completions, XP derived from rewards. One player's completion cannot complete another player's instance.
- **History:** one authoritative event/move record. Logs never truncate by accident; no chess-only generic headers.
- **Chess:** orthodox movement, castling, en passant, promotion, check/mate/stalemate, draws/claims as applicable, timer, resignation and custom configurations. Chess rule conformance checked against `chess_rules.md`.
- **Checkers:** WCDF English draughts (single-step kings, mandatory captures/chains, crowning, correct outcomes), independently of chess. Adding this game changes no generic engine source.
- **Exports:** FR-43 one format-specific trusted writer per game format; engine has no format switch. Correct PGN/SAN, six-field FEN **export only**, letter notation, transcript/metadata, applicable checkers and stenographic variants. No FEN import/round-trip requirement; compare output to known positions.

## 5. Backend, authentication, persistence, realtime

- FastAPI/OpenAPI defines typed request/response models, used to generate TypeScript contracts. Explicit methods for create, join, state, legal moves, submit move, resign, profile/history, settings and user configuration.
- Supabase Auth supports registered and **anonymous guest** sign-in with nicknames; enforce membership using verified JWT identity and row-level security. Avoid secret/service-role credentials in public clients. Validate guest rate limits for shared school IP.
- Persist games, two player assignments, config snapshot, revision, clocks, rule state, quest progress, moves, results, user achievements and ratings as applicable.
- Make a submitted move an **atomic operation**. Lock/check expected revision inside the transaction, verify identity and legality, persist updated state plus history once, handle repeat/parallel requests safely; conflicts return an explicit sync/retry response.
- Only authorized participants receive private game updates. Use Supabase Realtime to signal committed changes; clients independently refetch authoritative state after reconnect, missed/out-of-order updates or restarts.
- Transactions/serverless connection strategy must be verified with Supabase/Vercel deployment constraints. No assumed global in-memory sessions.

## 6. Web and Tauri presentation

The only GUI implementation lives in `packages/web`: React, TypeScript, Rsbuild, Bun, shadcn/ui, Tailwind, Motion, Lucide/lucide-animated. Provide game selection/start/join, board + coordinates, selectable pieces, legal highlights, clocks, two player panels, captures/lost pieces, turn indicator, history, per-player quest progress, true outcome/footer, resignation, registered/guest auth, and configuration UI.

The settings surface exposes Board/Pieces/Rules/Quests/Clocks as **schema-driven forms**, with validation, save/cancel/reset, duplicate/edit/delete user variants and real effect on subsequent games. No source-code editor. Respect supplied GUI reference and issue-specific accepted UI requirements (filled differentiated symbols, per-player quests, short-window layout). Preserve user choices where relevant without mixing local UI state with authoritative game state.

`packages/desktop` is a minimal Tauri 2 wrapper pointing at **the deployed web app** (not a local Python process). Restrict native capabilities, and verify authentication/navigation in the WebView. No second implementation.

## 7. Deployment and classroom proof

- Free-tier Supabase + two Vercel projects, no third-party game host.
- Validate the API Python runtime, dependency bundling/imports, Rsbuild SPA routing, environment secrets, CORS/origins, API routing, cold starts, auth callbacks, RLS and Realtime quotas.
- CI builds tagged/preview revisions and gates production on verified results; frontend/API deployed from a matching reviewed commit and schema-compatible migration.
- End-to-end: two guests open different browsers, create/join a game, alternate legal moves, finish correctly, persist result; repeat with registered users, two simultaneous independent matches, restart/reconnect, double-submission/concurrency, clock cutoff and unauthorized action.
- Rehearse classroom-size traffic and anonymous sign-up rate limits on the intended network. Public URL must be reachable. Free-tier quotas do not guarantee capacity.

## 8. DarkFactory, repository and licensing

- **Only `repo.dfconfig` is configuration**; migrate valid settings out of `.github/darkfactory.json` and remove it after its consumers (workflow callers, docs scripts, CI) are reconciled. Retain DarkFactory agent and approval automation—issues #124, #126, #167 and PR #170 are rejected/closed. Do not blindly delete functioning project-specific setup.
- Pin DarkFactory to the latest **verified** released immutable commit (identified at approval: v0.289.0; recheck on update). Use supported installer/update process and correctly retain global/local issue board behavior.
- Use GPL-3.0 consistently in `LICENSE`, Python metadata and `repo.dfconfig`. Preserve version-from-tag (`setuptools-scm`), not static `0.1.0`. Update dependencies for FastAPI, Supabase and frontend/Tauri.
- No duplicate workflows, stale workflow display names or wrong required checks. Preserve the existing GitHub Projects board #14 (renamed BoardGamesWithQuests; 211 original items) and Global #17; do not create a second empty board. Ensure the current PR and tracking issues belong to both boards, subject to actual API rate limits. Document required CI coverage and approval gates.

## 9. Stack consolidation and source disposition

Original stack **25 open PRs** from #218 through #209 at planning time, with the withdrawn #170 omitted from active work. New branch is based on corrected #218 (which itself descends from current main) and **merges the historical final #209 as a second parent**, preserving the entire previous stacked ancestry and its review provenance. To avoid resurrecting known-broken architecture the initial reconciled working tree keeps the corrected #218 files and only selected chess/checkers piece/export candidates from later PRs. **Those candidate files are not certified compatible.** The historical gameplay, rule, quest, GUI and runtime work remains recoverable through commit ancestry for targeted reimplementation/verification, but none is claimed as integrated or playable.

Review the entire legacy source chain against current JSON, engine and UI decisions; do not paste it blindly. For each source feature: retain, adapt, reimplement, or reject with evidence. Old Tkinter, local Python code-authoring, FEN importer, stale docs, static packaging, duplicate startup and agent-deletion changes are rejected as active architecture. A merged ancestry is **not** proof that all historical code was integrated.

Retire all 25 historical draft PRs once this consolidated draft PR is opened; post supersession links and preserve them as closed historical records. **Completed 2026-10-13:** all 26 obsolete PR-branch refs (including rejected #170) were removed by one-time GitHub Actions cleanup only after exact-SHA and commit-ancestry checks succeeded. Original commits remain reachable via the consolidated merge history; the temporary cleanup workflow was removed.

**Issues:** #129 is the authoritative consolidated Plan issue; #239 stays open as final tests. Existing old plan/request issues are superseded (not completed) and link #129/new PR. Their historical comments remain in GitHub. Do not leave obsolete Tkinter/Python/FEN-import/agent-removal requests in the live backlog.

## 10. Artifact alignment

- `README.md`: accurate evergreen overview, setup intent and documentation navigation; no claims of current playability.
- `.agents/AGENTS.md`: operational review, security, formatting and automation rules; correct `repo.dfconfig` references and current code/runtime verification. No temporary status.
- `.agents/notes/PRD.md`: all current product requirements; preserve FR identifiers where possible, mark withdrawn FEN import explicitly; describe JSON-only rules, web/server/Tauri architecture.
- `.agents/notes/object_model.md`: every intentional change from original Czech UML with rationale; no competing requirements/status.
- `.agents/notes/reference_diagram.md`: literal source diagram, no edits to historical fact.
- Implementation diagrams: regenerate from actual code, avoid misleading tracked stale SVG snapshots. Complete the approved red/green comparative SVG; visually review.
- `.agents/SCRATCHPAD.md`: succinct actual milestone/verification status and pointer here; not a second plan.
- GitHub: one active draft PR bound to #129; links, descriptions, labels and issue statuses consistent. Closed historical discussions remain reference-only, not active instructions.
- Docs workflows/Page builds: source routes and links match. No "verified playable" assertion until behavioral evidence.

## 11. Execution dependency graph and gates

| Gate | Work | Proof to proceed |
|---|---|---|
| G0 — CORE COMPLETE | Consolidate PR ancestry/tree/issues and establish authoritative plan | App-authored draft #271; 25 historical PRs closed unmerged; all 26 associated old PR refs removed with SHA/ancestry verification. Project board #14 preserved and renamed. Current Plan issue #129 and test gate #239. **Global board #17 still needs PR #271 after temporary GitHub GraphQL rate exhaustion.** |
| G1 | Validate JSON schema, five hooks, expression/condition vocabulary; Vercel + Supabase deploy feasibility | Both games expressible; a real Python API function imports engine and safely commits a fixture |
| G2 | Rebuild engine rules/quests/config/move commit/clock/history | Headless legal move and state/restart probes; zero game-name logic |
| G3 | Implement chess/checkers and format writers against G2, parallelized | Orthodox and WCDF scenarios run through same engine |
| G4 | FastAPI/Supabase and React UI in parallel against frozen typed contracts | End-to-end two-user real browser session; auth, clocks, quests, configuration persistence |
| G5 | Tauri wrapper, CI release/deployment, docs/diagram and issue alignment | Hosted web+desktop work, provenance checked |
| G6 | Fresh behavioral suite #239, security and independent audit | Required Python/browser/API/DB/deploy tests pass, no unresolved critical defects |
| G7 | Classroom rehearsal and owner approval | Public Vercel URL, concurrent games, guests, restart recovery; explicit owner approval before merge |

Use modular commits/workstreams on the **single shared integration branch**. Agent orchestration may work in isolated worktrees but must sequence integration at contract boundaries and avoid colliding writes. Final permanent tests are rebuilt from zero at G6; targeted temporary probes throughout are mandatory, not mistaken for a complete suite.

## 12. Known blocking findings to close

Independent source reviews (2026-10-12) found: inactive installed game entry point and a GUI `engine` NameError; wrong `default_configuration_name(root)` call and missing `DEFAULT_GAME`; generic export interface contrary to FR-43; duplicate runtime loaders; game-specific validator checks; direct unvalidated move execution; per-player quest completion leakage; duplicate user ID overwrite; timer invalid-ID/negative-time acceptance; code/doc/license pin conflicts; stale generated diagrams, no conclusive behavior tests. Additionally the old branch restored static `0.1.0`, old `theme/`, removed approved workflows and resurrected Python authoring. The new architecture must remedy all root causes, not merely bypass tests. Refer to [#129](https://github.com/marius-patrik/BoardGamesWithQuests/issues/129) and linked closed original PR discussions for provenance.

## 13. Definition of done

One complete and game-neutral JSON-driven Python engine; both games correct; no executable user configs; strict legal move/auth boundary; sound per-user quests/history; correct format writers; secure registered+guest identity and atomic Supabase persistence; fully functional responsive React GUI and hosted Tauri wrapper; public class-ready Vercel deployments on the approved free tiers; aligned licenses/CI/DarkFactory/docs/diagrams/issues; entire permanent behavior-driven suite #239 passing; independently reviewed evidence; explicit maintainer approval of the single consolidated PR. No claim of completion before those checks.
