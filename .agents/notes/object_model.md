# Architecture Decisions

**Product:** [PRD](PRD.md) · **Runtime contract:** [JSON rules](json_contract.md) ·
**Source reference:** [UML](reference_diagram.md) · **Delivery:** [PLAN](PLAN.md).

| Boundary | Decision |
| --- | --- |
| Engine | One headless Python package with game-neutral geometry, JSON hook evaluation, rules, outcomes, quests and authoritative domain commits. No game-name branching. |
| Configuration | Each game and user variant is bounded, validated, versioned JSON; active matches pin immutable snapshots. |
| Games | Independent `chess`, `english_draughts` and `international_checkers` packages declare movements and rulebooks as JSON data only. |
| Participants | Exactly two verified Supabase Auth identities per game; accounts may be guest or registered. |
| State | GameManager pins immutable JSON configuration and owns detached versioned board, canonical turn, rights, clocks, per-participant quests, accepted events, terminal result and revision. |
| Persistence | Supabase PostgreSQL holds authoritative durable JSON state with atomic revision checks; no process-memory authority. |
| Database security | The `bgwq` namespace is private, migrations are versioned, database access is server-only; browser privileges and JWTs are narrowly scoped. |
| Transport | FastAPI runs on Vercel Python Functions; Realtime events prompt authenticated refetch of authoritative snapshots. |
| Frontend | One React/TypeScript/Rsbuild/Bun interface with schema-driven settings and source-defined glyphs. |
| Desktop | Tauri 2 WebView loads the identical verified HTTPS frontend, with no duplicated UI or bundled Python. |
| Geometry | MoveValidator owns geometric candidates and attack queries; GameManager owns configured legality, transition publication and outcomes. |
| Movement | Immutable intents contain ordered landings and an optional promotion kind. Generic geometry derives complete capture routes; final authorization and configured effects belong to GameManager. JSON offers and configured far-rank policies define special-move and promotion behavior; shipped rulebooks must supply complete legality. |
| Rules | Five typed declarative hooks; all effects pass the central authorized state transition. No executable authored extensions. |
| Quests | Independent per-user, per-game progress, durable achievements and experience derived from completed rewards. |
| Outcomes | Configured terminal proposals resolved by deterministic declared precedence; ambiguous top-priority conflicts fail closed. |
| Export | One trusted game-owned serializer per format; PGN/SAN/FEN computed from authoritative game events and state. |
| Documentation | MkDocs/Material/mkdocstrings generate pages, homepage and navigation exclusively from tracked Python source/docstrings; strict builds retain live UML and required reference assets, link specifications to the checked-out Git revision, and commit no documentation source directory or static pages. |

## Domain transition ownership

`GameManager.submit` is the sole domain action boundary. The host supplies a
verified stable participant identity, expected revision, idempotent action
identifier, immutable move intent and trusted timestamp. The manager validates
geometry and configured authorization, applies effects to isolated candidate
state and publishes only the complete accepted transition. Direct intent
execution is denied. A rejected action or effect failure changes no observable
session state.

One accepted move, including all capture hops, produces one revision and one
event containing captured squares and the resolved outcome. Legal enumeration
and submission share isolated transition preparation, including post-move
effects and quest evaluation. Exact retries return the accepted event; conflicting identifiers and stale
revisions are rejected. Post-move evaluation reads accepted history and the next
canonical turn while participant selectors bind to the evaluating actor.
Outcome selectors bind to the next participant; post-move and quest selectors
bind to the mover. The canonical turn remains the next participant in both
evaluation contexts. Game-owned side effects cannot silently overwrite captured pieces. The session
prepares offers, promotion and transition effects once on an isolated board,
then evaluates configured permission against the observed snapshot and explicit
projected geometry. Configured roles select safety predicates; no piece name
identifies royalty. Initial rights/targets and additional halfmove-reset
conditions belong to the immutable definition and deterministic replay. Terminal
proposal conflicts fail closed and winners must resolve to session participants.

Snapshots pin configuration and initial identities and reproduce state by
replaying accepted events with recorded timestamps. This domain replay and an
in-process lock do not replace the server's authenticated Supabase transaction.
The durable adapter must compare expected revisions atomically across processes
and retain immutable action events. Public multiplayer, provider authorization
and complete game conformance require independent integration evidence.

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
