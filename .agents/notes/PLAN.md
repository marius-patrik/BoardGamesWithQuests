# BoardGamesWithQuests — Consolidated Completion Plan

**Status:** Active implementation plan; architecture approved 2026-10-13, implementation **not** complete.  
**Owner issue:** [#129](https://github.com/marius-patrik/BoardGamesWithQuests/issues/129). **Final test gate:** [#239](https://github.com/marius-patrik/BoardGamesWithQuests/issues/239).  
**Integration branch:** `feature/product-integration`, draft PR into `main`. **Never merge without maintainer approval.**  
**Authority:** Product contract: [PRD](PRD.md). Architectural deviations: [object model](object_model.md). Source reference: [reference diagram](reference_diagram.md). Current progress only: [scratchpad](../SCRATCHPAD.md).

## 1. Goal and constraints

Finish a **playable, correct online two-player** chess/English/international draughts app, game-neutral Python engine, JSON-only game configuration, public free-tier web deployment and Tauri desktop wrapper. Classmates must be able to visit the public URL, enter as guests, create/join a game, play to a result, and reconnect without losing state. Registered accounts also work. No leaderboard, classroom lobby, tournaments, separate rooms, separate desktop GUI or other unrequested product features.

**Principle:** No knowingly incorrect interim production behavior, duplicate configuration architecture, UI pretending to be playable, or unsupported feature advertising. All game-significant defaults come from explicit configuration. Original supplied reference drawings are immutable; changes require documented, approved deviations. Tests measure behavior.

## 2. Repository and deployed architecture

```text
packages/
  engine/     Python board/pieces, declarative rules/quests/hooks, moves, lifecycle
  chess/      config.json, game-owned serializers; no engine chess special cases
  english_draughts/      config.json for WCDF English draughts
  international_checkers/ config.json for international draughts
  server/     Python FastAPI, Supabase integration, player authorization, game transactions
  web/        React + TypeScript + Rsbuild + Bun + Tailwind + shadcn/ui + Motion + Lucide Animated
  desktop/    Tauri wrapper loading the same deployed web URL; no second frontend
```

**Vercel:** Two projects from the same repo: static Rsbuild frontend and Python Functions/FastAPI API. **Supabase:** Auth (including anonymous guests), Postgres authoritative persistence, Realtime notifications. This does not introduce a continuously running Python server or browser-resident Python. Tauri loads the hosted web app and needs a network connection. Pin/lock dependencies and generated API types. Verify Vercel Python runtime/package constraints rather than assuming deployability. No paid plans or paid resources without authorization.

**Boundary:** Engine knows neither HTTP, frontend nor database. Server imports engine and verifies identity, game membership and access. Browser owns presentation state only. Supabase Realtime distributes committed updates; never trust broadcast messages as move authorizations.

## 3. Declarative configuration — highest architecture gate

Every shipped game uses validated **`config.json`** specifying board dimensions/placements, piece glyphs and movement/attack capabilities, clock parameters, rules, quests, hooks, conditions/effects, outcomes and supported exporters. Users may duplicate/edit their own configurations; versions are stored as validated JSON in Supabase and running games pin an immutable snapshot. The shipped chess/checkers defaults are immutable. There is **one** game discovery, config parser/validator and loader. Remove competing `runtime_configuration.py`, `legacy_games.py`, `legacy_app.py`, `packages/default.json`, and parallel config/discovery logic.

**No user-authored executable code:** no Python or JS editor for rules/quests, dynamic imports of user-supplied modules, unsafe eval/exec, or writable executable config directories. Declarative JSON composes **trusted generic Python primitives**; extensible rules/quests are data, not user code. Generic behavior includes board queries, selections, vectors/attacks, captures, ownership, turns, logical AND/OR/NOT, comparisons/counts, rule state, conditional effects, progress/rewards and outcome proposals.

Keep the five conceptual hooks: `permits_move`, `available_moves`, `outcome`, `on_move_made`, `status`. Rules propose and the engine coordinates. Design a bounded and typed JSON AST/schema (no arbitrary string expressions); validate nesting, supported ops, target references and complexity. Test representative complex chess/English/international draughts rules *before* freezing schema, especially castling, en passant, pawn promotion, attack/check, repetition, mandatory multi-capture and outcome precedence. If an operation is missing, generalize primitives rather than hardcode a game identifier. No promise of arbitrary computation from finite JSON primitives.

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
- **Draughts:** Separate WCDF English (8×8, short kings) and international (10×10, flying kings, backward captures, maximum-capture obligation) JSON definitions. Multi-hop captures, crowning and results are generic hook behavior.
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

- `repo.dfconfig` is the single DarkFactory configuration. Python packaging metadata in `pyproject.toml` and any documentation-tool configuration remain independent tool inputs unless DarkFactory explicitly supports their generation. Retain functioning repository agent, approval and release automation.
- Pin DarkFactory to the latest **verified** released immutable commit and update through the supported installer. Use supported installer/update process and correctly retain global/local issue board behavior.
- Use GPL-3.0 consistently in `LICENSE`, Python metadata and `repo.dfconfig`. Preserve version-from-tag (`setuptools-scm`), not static `0.1.0`. Update dependencies for FastAPI, Supabase and frontend/Tauri.
- No duplicate workflows, stale workflow display names or wrong required checks. Preserve the existing GitHub Projects board #14 (BoardGamesWithQuests; 211 items audited) and Global project #17; do not create a duplicate board. The current PR is confirmed on both boards. Historical local statuses were reconciled from verified GitHub closure/merge evidence with a read-back check in run 38397182126. Document required CI coverage and approval gates.

## 9. Integration and source authority

The single active implementation branch and draft PR implement the current PRD.
Reference branches and closed issue discussions are provenance, not implementation
instructions. Review useful algorithms against the current engine contract rather
than importing executable game-specific rules or retired UI code. Package
configurations are JSON-only; exported formats are trusted serializers.

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
| G0 — COMPLETE | Keep one integration PR, preserve source ancestry, and reconcile tracking | Recovery refs absorbed and retired, one draft PR, Global #17 membership verified; local project #14 all 216 current items independently read and 81 statuses reconciled and verified by Actions run 38397182126. |
| G1 — COMPLETE | Freeze typed JSON rules/quests/references, prove generic chess and both draughts primitives, verify Vercel and Supabase transaction feasibility | Python G1 scenario/negative probes, public FastAPI + web smoke test, live private Supabase CAS/RLS/immutable config fixture. Backend-to-DB integration and complete game legality remain G2–G4. |
| G2 | Rebuild engine rules/quests/config/move commit/clock/history | Headless legal move and state/restart probes; zero game-name logic |
| G3 | Implement chess, English draughts and international draughts with game-specific formats against G2 | FIDE, WCDF and international scenarios run through the same engine |
| G4 | FastAPI/Supabase and React UI in parallel against frozen typed contracts | End-to-end two-user real browser session; auth, clocks, quests, configuration persistence |
| G5 | Tauri wrapper, CI release/deployment, docs/diagram and issue alignment | Hosted web+desktop work, provenance checked |
| G6 | Fresh behavioral suite #239, security and independent audit | Required Python/browser/API/DB/deploy tests pass, no unresolved critical defects |
| G7 | Classroom rehearsal and owner approval | Public Vercel URL, concurrent games, guests, restart recovery; explicit owner approval before merge |

Use modular commits/workstreams on the **single shared integration branch**. Agent orchestration may work in isolated worktrees but must sequence integration at contract boundaries and avoid colliding writes. Final permanent tests are rebuilt from zero at G6; targeted temporary probes throughout are mandatory, not mistaken for a complete suite.

## 12. Remaining critical implementation risks

- The JSON rules/effects vocabulary must express the complete chess and both draughts rulebooks.
- Every legal move, quest and outcome must be applied through one authoritative,
  reconstructible session transaction, with no user-registry shortcuts.
- No release until public API deployment, two-user play, concurrency, guest
  shared-IP quota and the full independent behavior suite are verified.
- Authentication, persistence and provider configurations are not yet live.

## 13. Definition of done

One complete and game-neutral JSON-driven Python engine; all three game definitions correct; no executable user configs; strict legal move/auth boundary; sound per-user quests/history; correct format writers; secure registered+guest identity and atomic Supabase persistence; fully functional responsive React GUI and hosted Tauri wrapper; public class-ready Vercel deployments on the approved free tiers; aligned licenses/CI/DarkFactory/docs/diagrams/issues; entire permanent behavior-driven suite #239 passing; independently reviewed evidence; explicit maintainer approval of the single consolidated PR. No claim of completion before those checks.
