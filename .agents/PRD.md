# BoardGamesWithQuests

BoardGamesWithQuests is a configuration-driven multiplayer board-game platform. One React application runs on Vercel and in Tauri WebViews; a separate Vercel-hosted Python/FastAPI application executes a generic deterministic engine. Supabase PostgreSQL owns all authoritative state and declarative configurations; Supabase Storage holds raster presentation assets. Configuration JSON is portable interchange and is not authoritative database state.

# 1. INVARIANTS

## 1.1 User-visible product

The application provides guest and registered accounts; creation and joining of games by opaque URL; published built-in definitions; an owned visual editor; configuration import/export; private real-time revision hints; game history; optional objectives/quests; ratings for eligible built-ins; and responsive, accessible browser/native UX. Users interact through a single frontend and API.

Playable built-ins are **chess**, **English draughts**, **international draughts**, and **MoneyProperty**, an original, unbranded Monopoly-style property-trading game. No protected third-party names, boards, cards, or other artwork may be bundled. Chess is the selection default. Game history export is not provided; configuration JSON export is provided.

No matchmaking, bots, spectator mode, social feed, leaderboard, or tournaments are specified.

## 1.2 Domain and ownership

- **Entity type**: `game | space | item | objective`. Types are domain metadata, not distinct interpreters. All seeded and dynamically created instances share one entity model.
- **Action**: a configured command or an automatically triggered hook action, attached to one entity type. It may enumerate typed locals, evaluate a pure Boolean condition, and execute an ordered list of effects. There are no separate movement, rule, or quest pipelines.
- **Objective**: a normal entity whose fields and actions encode progress, terminal game outcomes or optional quests. Permanent account XP/ratings are privileged settlement operations independent of author-defined effects.
- **Space**: an entity graph with directed or undirected links, optional grid coordinates, cyclic tracks, zones or ordered containment. Nothing in the engine requires a rectangular board.
- **Phase**: a named action-eligibility state; turns may contain multiple phases, simultaneous eligibility, and decisions. No hardcoded 2-player alternation.
- **Condition**: a typed, pure expression returning Boolean. Expressions can read observed/proposed state but cannot mutate it or perform I/O.
- **Effect**: a typed mutation proposal that acts only on a transition workspace. The engine never writes directly to PostgreSQL.
- **Hook**: an engine lifecycle event with deterministic ordering, context and bounded dispatch.
- **Presentation**: a read-only typed SVG scene projection assembled from entity topology, visuals and authoritative state. Never used to decide gameplay legality.

## 1.3 Action evaluation algorithm

For a submitted command, FastAPI authenticates the principal, checks Origin and CSRF, locks the game, resolves idempotency, and checks the expected revision. The repository loads the immutable pinned version and authoritative relational state into typed immutable projections. The engine generates candidates using entity actions, validates the selected command, creates an isolated proposed state, executes ordered effects and automatic hooks, evaluates objectives and completion, and returns a fully typed transition. The API validates the transition and commits all state changes, immutable event/mutation rows, revision increment and authorized progression in one PostgreSQL transaction. A failed check rolls everything back. Realtime publishes the committed revision as a hint; the client reloads the API projection.

The actor cannot submit trusted time, randomness, game state, the results of conditions, or effect arguments the definition does not permit. Exact same idempotency key+request digest returns the accepted result. Different payload reusing a key is a conflict. Accepted events are append-only; replay uses stored complete before/after mutations and recorded trusted inputs.

At activation, configuration seeds are instantiated in parent-before-child order. A seed with
an `owner` seat is instantiated **only when that seat is occupied**; this permits a
single 2–8-player MoneyProperty definition without instantiating tokens or wallets for
absent players. Global seeds must not depend on omitted optional-seat seeds. Every
instance's stable identity and initial order are recorded by the activation event.

Hook actions execute for live instances of their owning entity type in deterministic
creation/seed order. Within a hook, priority and action identity determine order.
Entity-scoped hooks evaluate against instances in deterministic order. Hooks for
an individual event subject (such as a drawn card) MUST explicitly match the
subject instance; a shared entity type or operation name is not sufficient.
Configured automatic movement MUST verify that the instance belongs to the
active participant, preventing actions on other participants' pieces or tokens.
Chess promotion is an effect within the same accepted pawn-movement command
before the turn advances; no separate post-turn promotion command is permitted.

A successful effect may expose a typed result to later effects in the same proposed
transition (for example, a trusted die result); it is never available to candidate
or legality evaluation before the random effect executes. Phase-changing effects
schedule subsequent `phase.enter` hooks through a bounded queue, never recursive
uncontrolled dispatch. Wildcard-phase actions apply to every configured phase.

A game is `pending`, `active`, `finished`, or `expired`. The final accepted event settles one immutable outcome per participant and may authorize progression awards; nonterminal games have no outcome records. The configured minimum participant count activates pending games once seats/roles are valid. Pending invitations expire after 24 hours. Games always pin one published version; published versions are immutable. A terminal game does not accept gameplay actions other than exact retries.

## 1.4 Security and privacy

All client-visible game state and available actions must be projected for the authenticated viewer; hidden cards, inventories and other secret data must not leak to competitors. Runtime entity references must remain inside their game; configuration references inside their pinned version. All execution is bounded. Public Supabase roles cannot query private `bgwq` tables. Database Realtime topics are private and membership-restricted. Assets use bounded signed uploads, MIME+hash verification, and version-pinned Storage paths. No user-authored Python, JavaScript, SQL, or unrestricted SVG/HTML execution is accepted.

## 1.5 Numeric and temporal semantics

Authoritative values support Boolean, signed 64-bit integer, exact decimal, Unicode text, UTC instant, typed entity/participant reference, and absence. Lists, sets and paths are bounded typed execution values and relationally stored as ordered entities/links. Monetary values are integer minor units. No floating-point authoritativeness. Integer overflow and invalid casts cause a typed evaluation error. All execution ordering, collection iteration, state digests, random draws and server-time reads have deterministic semantics. Path enumeration cannot silently truncate candidate lists.

## 1.6 Rendering, interaction and accessibility

The web app uses **Wouter** for routing, SVG primitives for space/entity visuals, shadcn/ui for accessible controls, Motion for visual transitions, and an API-supplied typed action catalog for input forms. All boards, tokens, cards, pieces and tracks are dynamically generated. Generic controls support selection, drag/pointer, touch, keyboard, lists, paths, choices, auctions, trades, dice, cards, objectives and clocks. The client animates but does not determine legal moves or mutate authoritative state. Private Storage assets are resolved through authorized asset grants.

## 1.7 Required observable outcomes

- Chess must implement all orthodox moves and compound transitions, checks, mate, stalemate, castling, en passant, promotions, clocks, repetition, draw claims and automatic draws.
- English and international draughts must implement their distinct capture, promotion, king movement, victory and draw semantics.
- MoneyProperty must provide original 40-location board data, full purchasable economy, deterministic dice/deck replay, extra rolls, detention, taxes, rent, upgrades, mortgages, auctions, trades, bankruptcy, elimination and victory.
- All four games use the same engine and renderer without game-name branches; all have playable complete browser scenarios and full replay after process interruption.
- At least 30 simultaneous players across 15 games from one classroom IP must function with revision and authorization correctness.
- Only Tauri wraps the hosted frontend; it never duplicates or locally runs the engine.

## Normative architecture and contracts

The product requirements above are defined by the following **single-source contracts**, which must agree with one another:

- [ARCHITECTURE.md](notes/requirements/ARCHITECTURE.md) — source tree with inline responsibilities, package boundaries, frameworks, tooling, and deployment.
- [openapi.yaml](../packages/server/api/openapi.yaml) — complete OpenAPI 3.1 HTTP contract and payload schemas.
- [schema.prisma](../packages/server/supabase/schema.prisma) — relational PostgreSQL entities, fields, relations and indexes.
- [integrity.sql](../packages/server/supabase/integrity.sql) — PostgreSQL-only integrity and Supabase Auth/Realtime security (not expressible in Prisma Schema Language).
- [AST.mmd](notes/requirements/AST.mmd) — pure Mermaid source-declaration and dependency graph; rendered interactively by the documentation site, **without committing an SVG**.
- [data/](../data/) — portable configuration JSON Schema, four self-contained game configurations, operator semantics and provisioning DML.

**Authority:** the API YAML, Prisma schema, Mermaid graph, and portable JSON files are normative inputs, not illustrations. The PRD defines product behavior and invariants; it does not duplicate their contents. A diagram specifies source architecture and exported interfaces, but is not an executable substitute for function bodies. Complete behavior is verified against a running generic engine and database, not inferred from document shape.

The specification graph in [AST.mmd](notes/requirements/AST.mmd) describes intended interfaces and dependencies. Source-derived [implementation AST](notes/diagrams/implementation/ast.mmd) and [implementation UML](notes/diagrams/implementation/uml.mmd) describe only code actually committed. Both are shown through the one Git-backed documentation viewer. Neither kind of diagram is proof of executable game behavior or a complete code generator.
