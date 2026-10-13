# Architecture Decisions

**Product:** [PRD](PRD.md) · **Runtime contract:** [JSON rules](json_contract.md) ·
**Source reference:** [UML](reference_diagram.md) · **Delivery:** [PLAN](PLAN.md).

| Boundary | Decision |
| --- | --- |
| Engine | One headless Python package with game-neutral geometry, JSON hook evaluation, rules, outcomes, quests and authoritative domain commits. No game-name branching. |
| Configuration | Each game and user variant is bounded, validated, versioned JSON; active matches pin immutable snapshots. |
| Games | Independent `chess`, `english_draughts` and `international_checkers` packages declare movements and rulebooks as JSON data only. |
| Participants | Exactly two verified Supabase Auth identities per game; accounts may be guest or registered. |
| State | Game session owns board, active turn, rule state, per-player quests, clocks, events, terminal result and revision. |
| Persistence | Supabase PostgreSQL holds authoritative durable JSON state with atomic revision checks; no process-memory authority. |
| Database security | The `bgwq` namespace is private, migrations are versioned, database access is server-only; browser privileges and JWTs are narrowly scoped. |
| Transport | FastAPI runs on Vercel Python Functions; Realtime events prompt authenticated refetch of authoritative snapshots. |
| Frontend | One React/TypeScript/Rsbuild/Bun interface with schema-driven settings and source-defined glyphs. |
| Desktop | Tauri 2 WebView loads the identical verified HTTPS frontend, with no duplicated UI or bundled Python. |
| Movement | Per-piece vectors and bounded configurable capture policies implement multi-hop and flying captures, deferred removal and promotion hooks. |
| Rules | Five typed declarative hooks; all effects pass the central authorized state transition. No executable authored extensions. |
| Quests | Independent per-user, per-game progress, durable achievements and experience derived from completed rewards. |
| Outcomes | Configured terminal proposals resolved by deterministic declared precedence; ambiguous top-priority conflicts fail closed. |
| Export | One trusted game-owned serializer per format; PGN/SAN/FEN computed from authoritative game events and state. |
| Documentation | Source-derived implementation diagrams, strict docs, one PRD/plan and one permanent behavioral acceptance suite. |

## Source reference constraints

The supplied [class](diagrams/reference-page1.svg) and
[MVC](diagrams/reference-mvc.svg) diagrams define domain concepts,
not additional runtime implementations. Their Czech class captions
map to canonical English domain names; names alone must not create duplicate
model classes. Reference typos and incomplete inheritance marks do not define
extra types. UI responsibilities live in React, and an optional source alias
must reference the same Python type rather than create a second system.

Every architectural change updates this table, relevant requirement rows,
the JSON contract, tests, deploy scripts and source-derived diagrams together.
