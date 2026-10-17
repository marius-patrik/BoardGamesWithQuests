# BoardGamesWithQuests

BoardGamesWithQuests is a configuration-driven multiplayer board-game platform. One React application runs on Vercel and in Tauri WebViews; a separate Vercel-hosted Python/FastAPI application executes a generic deterministic engine. Supabase PostgreSQL owns all authoritative state and declarative configurations; Supabase Storage holds raster presentation assets. Configuration JSON is portable interchange and is not authoritative database state.

# 1. INVARIANTS

## 1.1 User-visible product

The application provides guest and registered accounts; creation and joining of games by opaque URL; published built-in definitions; an owned visual editor; configuration import/export; private real-time revision hints; game history; optional objectives/quests; ratings for eligible built-ins; and responsive, accessible browser/native UX. Users interact through a single frontend and API.

The initial playable games are **chess**, **English draughts**, and **international draughts**. **MoneyProperty** remains a fully specified, original and unbranded property-trading game definition and a required generic-engine compatibility target; complete playable economic behavior and its end-to-end acceptance are the **final game milestone**, after the generic engine, multiplayer system, editor, deployments and first three games are verified. No protected third-party names, boards, cards, or artwork may be bundled. Chess is the selection default. Game history export is not provided; configuration JSON export is provided.

No matchmaking, bots, spectator mode, social feed, leaderboard, or tournaments are specified.

## 1.2 Domain and ownership

- **Entity type**: `game | space | item | objective`. Types are domain metadata, not distinct interpreters. All seeded and dynamically created instances share one entity model.
- **Action**: a configured command or an automatically triggered hook action, attached to one entity type. It may enumerate typed locals, evaluate a pure Boolean condition, and execute an ordered list of effects. There are no separate movement, rule, or quest pipelines.
- **Objective**: a normal entity whose fields and actions encode progress, terminal game outcomes or optional quests. Permanent account XP/ratings are privileged settlement operations independent of author-defined effects.
- **Space**: an entity graph with directed or undirected links, optional grid coordinates, cyclic tracks, zones or ordered containment. Nothing in the engine requires a rectangular board.
- **Participants**: each immutable published definition declares a validated `min_participants`/`max_participants` range, with seats allocated only to joined users; no engine, API, schema, or renderer assumes exactly two. Chess and both draughts require precisely two; MoneyProperty supports two through eight, while the core model supports other bounded counts and multi-party decisions.
- **Phase**: a named action-eligibility state; turns may contain multiple phases, simultaneous eligibility, and decisions. No hardcoded two-player alternation.
- **Condition**: a typed, pure expression returning Boolean. Expressions can read observed/proposed state but cannot mutate it or perform I/O.
- **Effect**: a typed mutation proposal that acts only on a transition workspace. The engine never writes directly to PostgreSQL.
- **Hook**: an engine lifecycle event with deterministic ordering, context and bounded dispatch.
- **Presentation**: a read-only typed SVG scene projection assembled from entity topology, visuals and authoritative state. Never used to decide gameplay legality.

## 1.3 Action evaluation algorithm

For a submitted command, FastAPI authenticates the principal, checks Origin and CSRF, locks the game, resolves idempotency, and checks the expected revision. The repository loads the immutable pinned version and authoritative relational state into typed immutable projections. The engine generates candidates using entity actions, validates the selected command, creates an isolated proposed state, executes ordered effects and automatic hooks, evaluates objectives and completion, and returns a fully typed transition. The API validates the transition and commits all state changes, immutable event/mutation rows, revision increment and authorized progression in one PostgreSQL transaction. A failed check rolls everything back. Realtime publishes the committed revision as a hint; the client reloads the API projection.

The browser first calls the read-only `GET /session` to establish a CSRF-bound pre-authentication cookie even without an identity; it receives `authenticated: false` and a token. Guest/login/register are CSRF-checked against that cookie and issue new authenticated session credentials. The actor cannot submit trusted time, randomness, game state, the results of conditions, or effect arguments the definition does not permit. Exact same idempotency key+request digest returns the accepted result. Different payload reusing a key is a conflict. Accepted events are append-only; replay uses stored complete before/after mutations and recorded trusted inputs.

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

A game is `pending`, `active`, `finished`, or `expired`. Its chosen participant target is immutable after creation; an active game cannot add seats. The final accepted event settles one immutable outcome per participant and may authorize progression awards; nonterminal games have no outcome records. At creation, the creator chooses immutable `target_participants` within the pinned definition's `min_participants`/`max_participants` range. The game activates exactly when that many valid seats are occupied, rather than auto-starting a four-player invitation after its second join. The serialized join transaction atomically initializes once, and PostgreSQL independently rejects seat indexes or role allocations exceeding the pinned target. Pending invitations expire after 24 hours. Games always pin one published version; published versions are immutable. A terminal game does not accept gameplay actions other than exact retries.

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
- Chess and both draughts games first pass complete browser and provider-backed replay/recovery scenarios on the same generic engine and renderer. MoneyProperty is implemented and accepted as the final game, without adding game-name branches or a second interpreter.
- MoneyProperty's definition, generic operators, schema and API requirements remain normative from the outset. Deferring playable acceptance cannot defer variable participants, hidden-state, multi-phase decisions, or economic data-model support.
- At least 30 simultaneous players across 15 games from one classroom IP must function with revision and authorization correctness.
- Only Tauri wraps the hosted frontend; it never duplicates or locally runs the engine.

## Contract-finalization gate

Before implementing gameplay against this design, review the **API, schema and interface/dependency graph as one system**. Approval requires:

- **HTTP/API**: Every public operation declares its typed request/response, authentication and CSRF, per-participant authorization, revision/idempotency behavior, error cases, and viewer-scoped projection/redaction; each operation maps to a concrete service and transactional owner.
- **Database**: Every API projection and engine mutation maps to immutable version-pinned definitions, game-scoped state, append-only events, outcomes and rewards, with sound composite keys, indexes, constraints, RLS/grants, real upgrade paths and atomic settlement.
- **Source graph**: Every file and exported interface has one owner, typed inputs/outputs, dependencies, ordering, invariants, failure modes and side-effect boundaries. The specification graph cannot silently be confused with the actual generated implementation diagrams.
- **Cross-contract validation**: All JSON fixtures, operators, OpenAPI, Prisma and PostgreSQL integrity SQL agree on participant ranges, stable identifiers, reference scopes, secrecy, revisions and replay. Passing structural checks is not a substitute for running migrations and provider-facing acceptance.
- **Dependency**: Architecture is approved before treating platform bootstrap or integration as complete. The full MoneyProperty browser/product acceptance is last, while its architectural requirements apply throughout.

## Normative design and source ownership

The HTTP API, operation ownership and supplementary PostgreSQL design are maintained as **reference appendices in this PRD**, not as deployed OpenAPI or SQL source files. The executable database structure is authored in [Prisma schema](../packages/server/supabase/schema.prisma); constraints not expressible in Prisma require real migrations during implementation. Portable [sample game configurations](reference/data/configuration.schema.json) are input references, not authoritative game state.

The [engine UML](requirements/diagrams/engine_uml.mmd) defines the target state, transaction and interpreter boundaries; the [client UML](requirements/diagrams/client_uml.mmd) defines externally observable routing, identity, concurrency and recovery flows. These are deliberately **not** a speculative complete source AST. The [repository AST](architecture/diagrams/ast.mmd) and [actual implementation UML](architecture/diagrams/uml.mmd) are generated from source. Original assignment references and the retained [GUI mockup](reference/images/GUI_mockup.svg) belong exclusively under `.agents/reference/`.

## Source architecture

The following is a **target source inventory** with ownership and file responsibilities. It is not a claim that all source files exist. The diagrams describe contracts and behaviors; only executed tests against public/provider boundaries validate implementation. All source paths are rooted at the repository root.

## Stack and authority

| Concern | Normative choice |
| --- | --- |
| Frontend | `packages/client`: Bun, React, TypeScript, Wouter, Rsbuild, Tailwind, shadcn/ui and Motion; SVG scene renderer |
| Native | Tauri 2 WebView of the same HTTPS frontend (not a second UI or engine) |
| API | Python FastAPI and Pydantic on a separate Vercel project |
| Engine | Pure deterministic Python interpreter over entities, actions, conditions, effects and hooks |
| Database | Supabase PostgreSQL, Prisma Schema Language for schema/migration authoring, Python psycopg for runtime I/O |
| Security | Supabase Auth, private Realtime Broadcast, private Storage, backend-enforced authorization and CSRF |
| Documentation | TSDoc, Python docstrings, Rustdoc, OpenAPI and interactive Mermaid source diagrams |
| Verification | pytest, Playwright, native smoke tests, real database migrations and cross-contract validation |

Prisma is **schema authoring tooling**, not a production Node.js database runtime. PostgreSQL-specific constraints and trigger semantics are documented in the **supplementary SQL reference appendix** below, because Prisma PSL does not model CHECK constraints, partial indexes, Supabase Auth foreign keys, publication immutability, event parity, or private Broadcast authorization. This appendix is not an applied migration: implementation must author, deploy, and independently test actual PostgreSQL migrations before the database is production-ready.

## Target file tree

```text
.agents/  # Product and architectural requirements; implementation lives in packages, not here.
  architecture/  # Only actual implementation evidence; output diagrams are derived from tracked code.
    diagrams/  # Real cross-language repository AST and Python implementation UML.
      ast.mmd  # Generated cross-language file/declaration graph.
      uml.mmd  # Generated implementation classes and verified inheritance edges.
    images/  # Actual implementation screenshots only, never reference art.
      .gitkeep  # Keep optional image folder in Git when no verified screenshot exists.
      README.md  # Explain what source-generated diagrams actually prove and how to reproduce them.
  reference/  # Original assignment references, explicitly not normative implementation design.
    diagrams/  # Original reference models in editable Mermaid form.
      mvc.mmd  # Assignment MVC reference.
      uml.mmd  # Assignment UML reference.
    images/  # Original authored assignment artwork; do not synthesize a replacement silently.
      GUI_mockup.svg  # Preserved original Excalidraw drawing.
      README.md  # Keep the original reference diagrams and artwork distinct from product specifications.
  requirements/  # Normative target behavior and design, not generated code evidence.
    diagrams/  # Independently reviewable engine model and client interaction flow.
      engine_uml.mmd  # Target engine classes, transaction ownership and typed execution relations.
      client_uml.mmd  # End-to-end authenticated routing, actions, Realtime and recovery sequence.
    images/  # Final approved UX assets; never treat original assignment artwork as the final design.
      .gitkeep  # Track directory until a reviewed finalized product mockup is authored.
  PRD.md  # Product invariants, annotated source inventory, package ownership and requirements.
.github/  # DarkFactory governance, one documentation implementation, verification and release workflows.
  docs-ui/  # Existing ProperDocs template; no second architecture renderer.
    assets/  # Reader styles and controls.
      diagrams.js  # Shared SVG/Mermaid zoom, pan and modal viewer controls.
      theme.css  # Reader layout, theme and sidebar styles.
      theme.js  # Layout, navigation, fullscreen and version selection.
    partials/  # File-system-derived UI templates.
      nav.html  # Exact Git folder hierarchy, collapsible sections.
      switcher.html  # Published main/PR versions only.
    main.html  # ProperDocs template that consumes generated navigation.
  scripts/  # One Git-backed docs pipeline plus explicit contract verification.
    assemble_docs.py  # Assemble only independently staged successful HTML snapshots.
    build_docs.py  # Single source-page, navigation, compilation and deployed-manifest builder.
    check_spec_contracts.py  # Validate canonical JSON, OpenAPI, relational schema, SQL and Mermaid architecture.
    generate_diagrams.py  # Generate repository AST and implementation UML from actual tracked source.
  tests/  # User-visible documentation and publication tests.
    test_docs_publication.py  # Staging, missing-main behavior and preview filtering checks.
  workflows/  # Existing DarkFactory and GitHub Pages pipelines; no duplicate check workflow.
    build-main-docs.yml  # Independently stage passing main documentation.
    darkfactory-control.yml  # Execute delegated quality and governance.
    darkfactory.yml  # Invoke the canonical DarkFactory workflow.
    deploy-api.yml  # Deploy reviewed FastAPI service to its Vercel project.
    deploy-docs.yml  # Assemble published GitHub Pages snapshots without rebuilding PRs.
    deploy-web.yml  # Deploy reviewed React bundle to its Vercel project.
    native-ios-signed.yml  # Signed iOS release build gate.
    native-release.yml  # Native platform release automation.
    preview-docs.yml  # Build and browser-test each PR's own docs source.
data/  # Portable game configurations, typed operator registry and seed data.
  chess.json  # Complete portable orthodox chess definition interpreted by the generic engine
  configuration.schema.json  # JSON Schema 2020-12 for portable game configuration import and export
  english-draughts.json  # Portable English draughts definition using generic action and traversal operators
  international-draughts.json  # Portable international draughts definition with configured maximal capture
  moneyproperty.json  # Original Monopoly-like economic game configuration with forty spaces
  operators.json  # Finite, typed expression/effect operator registry with argument contracts, determinism and errors; imported by generic engine and validated with all games.
  seed.sql  # Supabase Storage bucket and hook/operator registry seed data applied after schema migration; never implements game-specific behavior.
packages/  # Deployable web, API/engine, native packages and schema.
  native/  # Remote-origin Tauri WebView wrapper.
    src-tauri/  # Rust host, platform manifests and native capabilities.
      capabilities/  # Tauri permission and origin allowlist.
        default.json  # least-privilege capabilities; Navigation capabilities restricted to production origin
      icons/  # OS installer and launcher artwork.
        icon.icns  # icon asset; App icon in platform-required format
        icon.ico  # icon asset; App icon in platform-required format
        icon.png  # icon asset; App icon in platform-required format
      src/  # Implementation source files within its owning package.
        main.rs  # main() -> run(); Rustdoc: Minimal native WebView lifecycle
      Cargo.lock  # Cargo dependency lock; Reproducible native build
      Cargo.toml  # crate manifest; Restricted host dependencies
      build.rs  # tauri_build::build(); Rustdoc: Tauri native resource setup
      tauri.conf.json  # production remote URL, ids, permissions; One remotely loaded frontend across targets
    package.json  # Tauri build scripts; Platform build toolchain
  server/  # Python API, pure engine and schema/provisioning definitions.
    api/  # FastAPI public HTTP DTOs, authorization and services.
      __init__.py  # module; Python package marker
      app.py  # create_app()->FastAPI; Construct middleware, session, routes, error handlers
      assets.py  # begin_upload(); finish_upload(); signed_url(); cleanup(); Supabase Storage signed upload, digest validation, publication immutability
      contracts.py  # Pydantic Models: Session, Game, Definition, Command, Event; HTTP DTOs conform exactly to OpenAPI
      index.py  # app: FastAPI; Serverless ASGI entrypoint
      realtime.py  # private_channel_grant(); authorize_subscription(); Supabase private Broadcast access for game members
      repository.py  # Repository.load/save/project + UOW; Psycopg relational hydration and atomic writes
      routes.py  # mount_routes(app); 33 operation IDs; Register all documented identity, definition, asset, and game endpoints
      security.py  # principal(); verify_csrf(); require_membership(); Supabase Auth session, Origin/CSRF, role and hidden-state authorization
      services.py  # create_game(); join_game(); submit_action(); publish_definition(); Transaction-aware API orchestration; no game rules
    configuration/  # Portable JSON import/export and definition validation.
      __init__.py  # module; Portable configuration package
      bootstrap.py  # import_builtins(repository); Load four portable game definitions into published versions
      models.py  # PortableConfig Pydantic + local references; Validate portable fields and structurally defined record types
      transfer.py  # import_json(); export_json(); canonicalize(); Deterministic relational import/export and asset bundling
      validation.py  # validate_references(); validate_types(); publish(); Validate cycles, budgets, signed assets, hook/effect signatures
    engine/  # Generic pure interpreter of actions, effects, hooks and typed state.
      __init__.py  # module; Generic engine package
      effects.py  # propose(effect,state,ctx)->Mutation[]; Controlled generic effect executor; never writes database
      events.py  # encode_mutations(); replay(); digest(); Reconstruct complete entity/link/value/turn changes from typed event rows
      expressions.py  # evaluate(expr,ctx); validate_dag(expr); Pure typed expression evaluator; no IO, deterministic budget
      hooks.py  # dispatch(hook,ctx)->ActionResult[]; Stratified hook scheduler, ordering, event queue and budgets
      model.py  # EntityType,Entity,ActionDef,GameState,Transition,Mutation; Frozen typed pure engine data models
      operators.py  # registry(); evaluate_op(); signature(); Finite generic pure operator catalog; no game-name branches
      randomness.py  # consume(trusted_stream,range)->RandomSample; Deterministic consumption of injected entropy; replay uses recorded values
      reachability.py  # exists_reachable(start,successors,target,canonical_key,max_states)->bool; no_reachable_terminal(...)->bool; ReachabilityLimit; Exact generic finite-state model checking; resource exhaustion never esta
      runtime.py  # initialize(); available_actions(); evaluate(); status(); The single authority for action semantics; immutable state transitions
      topology.py  # neighbors(); ray(); paths(); track_advance(); General topology and bounded traversal primitives
      types.py  # parse_type(); check_type(); TypedValue; Generic scalar, reference, optional, list, set, path, record typing
    supabase/  # Prisma declaration and database-only SQL integrity.
      config.toml  # Supabase local/auth/storage config; Local Supabase services and migrations
      schema.prisma  # Authoritative Prisma PostgreSQL 38-model relational declaration; migration-only tooling, no Node runtime.
    pyproject.toml  # Python dependencies and pytest; FastAPI psycopg Pydantic and validation dependencies
    vercel.json  # ASGI route and limits; Deploy Python entrypoint in separate Vercel project
  client/  # One React frontend on Vercel and in native WebView.
    src/  # Implementation source files within its owning package.
      api/  # FastAPI public HTTP DTOs, authorization and services.
        assets.ts  # assetUrl(); uploadAsset(); Bounded signed asset requests and downloads
        client.ts  # request<T>(); API error normalization; Same-origin cookie/CSRF-aware fetch
        realtime.ts  # subscribeGame(gameId, callback); Private Broadcast + reconnect revision invalidation
        types.ts  # Generated from implemented FastAPI OpenAPI, checked for compatibility with the PRD reference
      app/  # Own the declared files and their documented interfaces; no duplicate implementation.
        pages.tsx  # HomePage,AuthPage,AccountPage,DefinitionsPage,GamePage; All routed screens (not game-specific boards)
        query.ts  # QueryClient;invalidateOnRevision(); HTTP cache, retry and version synchronization
        router.tsx  # AppRoutes():ReactElement; Wouter Switch/Route navigation and guard
        session.tsx  # SessionProvider();useSession(); Cookie session and CSRF state
      editor/  # Typed entity/action/visual authoring controls.
        ActionEditor.tsx  # ActionEditor(); Manual/hook actions, conditions, parameter and effect lists
        AssetEditor.tsx  # AssetEditor(); Private binary upload and presentation assets
        DefinitionEditor.tsx  # DefinitionEditor(); Top-level unified configuration editor
        EntityEditor.tsx  # EntityEditor(); Types, seeds, field values and relationships
        ExpressionEditor.tsx  # ExpressionEditor(); Typed operator DAG builder with validation
        RolePhaseEditor.tsx  # RolePhaseEditor(); Participant roles, phases and eligible command forms
        SpaceEditor.tsx  # SpaceEditor(); Visual grid/graph/track and entity placement editor
        TransferEditor.tsx  # TransferEditor(); Canonical portable JSON import/export
        VisualEditor.tsx  # VisualEditor(); SVG template construction and asset binding
        useDraft.ts  # useDraft(); publish(); validate(); Autosave/publish conflict handling and draft revisions
      games/  # Config-driven multiplayer interaction and session panels.
        ActionPanel.tsx  # ActionPanel();ParameterInput(); Typed, dynamically generated action controls
        Clocks.tsx  # Clocks(); Nonauthoritative clock projection
        Decisions.tsx  # DecisionControls(); Generic multi-party decision/auction/trade controls
        GameView.tsx  # GameView({gameId}):ReactElement; Compose generic scene, actions, history, status and participants
        History.tsx  # History({events}); Generic revision and accepted-event timeline
        Invite.tsx  # Invite(); Invite URL, join state, pending expiration
        ObjectivePanel.tsx  # ObjectivePanel(); Generic objective state/progress including optional quests
        Participants.tsx  # ParticipantPanel(); Arbitrary participant counts, roles and eliminated state
        useGame.ts  # useGame(); useAvailableActions(); useSubmitAction(); Authoritative game queries, revisions, idempotent command sends
      rendering/  # Generic SVG/ARIA layout and scene interaction.
        Accessibility.ts  # getEntityAria(); focusNavigation(); Keyboard and screenreader metadata derived from scene
        Animation.tsx  # AnimatedEntity(); useMotionProjection(); Motion projections on authoritative state changes
        Interactions.tsx  # InteractionLayer(); usePointerActions(); Pointer/touch/keyboard access and action-source selection
        Layout.ts  # resolveLayouts(); projectLocations(); Grid, node graph, track and free placement transforms
        Primitive.tsx  # Primitive({definition}):ReactElement; Allowlisted safe SVG primitives; no arbitrary markup
        Scene.tsx  # Scene({entities,scene}):ReactElement; One dynamic SVG scene for all four game types
      ui/  # Accessible shadcn-derived presentational controls.
        button.tsx  # Button(props); Clickable semantic button
        card.tsx  # Card(props); Visual panel
        dialog.tsx  # Dialog(props); Accessible modal
        input.tsx  # Input(props); Accessible text input
        select.tsx  # Select(props); Typed selection control
        tabs.tsx  # Tabs(props); Accessible tab list
        toast.tsx  # Toast(props); Status and error announcement
        tooltip.tsx  # Tooltip(props); Contextual help
      App.tsx  # App():ReactElement; Auth/Query providers and Wouter Router
      main.tsx  # createRoot().render(<App/>); Browser root mounting
      styles.css  # Tailwind base + design tokens; Themes, typography and focus styles
    components.json  # shadcn registry configuration; UI composition and token aliases
    index.html  # root viewport; Application HTML shell
    package.json  # React + Wouter + Motion + shadcn + OpenAPI client; Locked frontend and tooling dependencies
    rsbuild.config.ts  # defineConfig(); Rsbuild bundling, alias, compile options
    tsconfig.json  # compilerOptions strict; Web TS project constraints
    vercel.json  # SPA rewrites + API proxy; Forward /api/* to separate Vercel deployment
tests/  # Observable API, engine, database and browser behavior.
  api/  # FastAPI public HTTP DTOs, authorization and services.
    test_contract.py  # test/assertions; OpenAPI and security errors
    test_realtime.py  # test/assertions; Private revision authorization
  browser/  # End-to-end web session and rendering tests.
    editor.spec.ts  # test/assertions; Structured authoring and import/export
    games.spec.ts  # test/assertions; Four full game scenarios
    package.json  # configuration; Browser test runner dependencies
    playwright.config.ts  # configuration; Cross-browser test configuration
    rendering.spec.ts  # test/assertions; SVG, accessibility and layout
  configuration/  # Portable JSON import/export and definition validation.
    test_assets.py  # test/assertions; Binary import/export digest parity
    test_roundtrip.py  # test/assertions; Structural and semantic JSON roundtrip
  database/  # Actual PostgreSQL constraints, events and transactions.
    test_integrity.py  # test/assertions; Published immutability, trigger and RLS checks
    test_schema.py  # test/assertions; Migrations/FKs/constraints in real PostgreSQL
    test_transactions.py  # test/assertions; Concurrent actions and exact idempotency
  engine/  # Generic pure interpreter of actions, effects, hooks and typed state.
    test_chess.py  # test/assertions; FIDE legal and forbidden actions
    test_draughts.py  # test/assertions; Capture/path and promotion edge cases
    test_execution.py  # test/assertions; Pure operator semantics
    test_game_contracts.py  # test_dice_moves_only_the_active_players_token(); test_pawn_promotion_occurs_before_advancing_turn(); test_economic_actions_do_not_embed_a_game_named_operator(); test_chess_dead_position_uses_sound_gen
    test_moneyproperty.py  # test/assertions; Economic decision and multi-party transactions
    test_reachability.py  # test_reachable_even_with_cycles(); test_unreachable_only_when_exhausted(); test_budget_does_not_produce_false_proof(); test_terminal_start_and_invalid_budget(); Check proof soundness, cycles and budge
  native/  # Remote-origin Tauri WebView wrapper.
    smoke.spec.ts  # test/assertions; Remote WebView and navigation restrictions
.editorconfig  # indent / whitespace; Consistent editor indentation
.env.example  # variable names only; Document public and server-only environment names
.gitignore  # build outputs; Exclude generated caches and binaries
LICENSE  # license text; Product distribution terms
README.md  # symlink -> .agents/PRD.md; Entry to source of truth
bun.lock  # Bun lockfile; Locked dependency graph
package.json  # bun workspaces; Root workspace and verify tasks
prisma.config.ts  # defineConfig({schema: packages/server/supabase/schema.prisma, migrations: packages/server/supabase/migrations}); Prisma CLI-only configuration; no generated runtime client.
tsconfig.json  # TS project base; Strict TS and module-resolution defaults
tsdoc.json  # TSDoc grammar; Single standard for structured TSDoc tags
typedoc.json  # TypeDoc configuration; Generate docs from structured TSDoc declarations
```

## Implementation order

Approve the complete, mutually consistent API/schema/interface graph before building the authoritative gameplay behavior. Implement the game-neutral client, API, state interpreter and database transactions first; deliver chess and both draughts as real two-account provider-backed games; validate variable participants and all general abstractions throughout; finish MoneyProperty's distinct economic behavior as the last game milestone. No two-player-only production shortcut or game-name-specific engine paths are permitted.

## Package boundaries

The API imports engine interfaces but the engine cannot import API or I/O modules. Configuration loading maps portable definition records to immutable typed engine structures. The frontend calls only the API and authorized asset/Realtime services; native is a constrained wrapper. Prisma never owns the Supabase-managed `auth.users` table. Database-changing code is transactional and backend-only. Scripts under `.github/scripts/` are repository/documentation tooling, not alternate application runtimes.

# 4. REFERENCE CONTRACTS

The following appendices are specification material, not deployed API handlers, production migrations, or evidence of gameplay implementation. Do **not** generate a runnable client/server solely from the reference examples. Once FastAPI routes and actual SQL migrations exist, verify their *external behavior* against this PRD.

## API reference — planned interfaces (not deployed)

A fresh anonymous browser obtains a pre-authentication CSRF cookie from `GET /session` before guest/login mutations. The example documents 33 proposed HTTP operations and their types, rather than claiming these endpoints currently exist. The eventual FastAPI-generated OpenAPI is authoritative for deployed endpoints.

```yaml
openapi: 3.1.0
info:
  title: BoardGamesWithQuests API
  version: 1.0.0
  description: Authoritative board game, configuration, identity, and asset API.
servers:
- url: /api/v1
security:
- cookieSession: []
paths:
  /session:
    get:
      tags:
      - Identity
      operationId: getSession
      summary: Read authenticated session or bootstrap anonymous CSRF cookie
      responses:
        '200':
          description: Read session
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Session'
        '401':
          description: Unauthenticated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '403':
          description: Forbidden
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '404':
          description: Not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '409':
          description: Conflict
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '422':
          description: Validation error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '429':
          description: Rate limited
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
      security: []
  /auth/guest:
    post:
      tags:
      - Identity
      operationId: createGuest
      summary: Create anonymous identity
      responses:
        '201':
          description: Create anonymous identity
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Session'
        '401':
          description: Unauthenticated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '403':
          description: Forbidden
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '404':
          description: Not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '409':
          description: Conflict
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '422':
          description: Validation error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '429':
          description: Rate limited
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
      security: []
      parameters:
      - $ref: '#/components/parameters/csrf'
  /auth/register:
    post:
      tags:
      - Identity
      operationId: register
      summary: Create account
      responses:
        '201':
          description: Create account
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Session'
        '401':
          description: Unauthenticated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '403':
          description: Forbidden
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '404':
          description: Not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '409':
          description: Conflict
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '422':
          description: Validation error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '429':
          description: Rate limited
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
      security: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Credentials'
      parameters:
      - $ref: '#/components/parameters/csrf'
  /auth/login:
    post:
      tags:
      - Identity
      operationId: login
      summary: Authenticate
      responses:
        '200':
          description: Authenticate
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Session'
        '401':
          description: Unauthenticated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '403':
          description: Forbidden
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '404':
          description: Not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '409':
          description: Conflict
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '422':
          description: Validation error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '429':
          description: Rate limited
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
      security: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Credentials'
      parameters:
      - $ref: '#/components/parameters/csrf'
  /auth/upgrade:
    post:
      tags:
      - Identity
      operationId: upgrade
      summary: Upgrade guest without changing user ID
      responses:
        '200':
          description: Upgrade guest without changing user ID
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Session'
        '401':
          description: Unauthenticated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '403':
          description: Forbidden
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '404':
          description: Not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '409':
          description: Conflict
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '422':
          description: Validation error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '429':
          description: Rate limited
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Credentials'
      parameters:
      - $ref: '#/components/parameters/csrf'
  /auth/logout:
    post:
      tags:
      - Identity
      operationId: logout
      summary: Invalidate session
      responses:
        '204':
          description: Invalidate session
        '401':
          description: Unauthenticated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '403':
          description: Forbidden
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '404':
          description: Not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '409':
          description: Conflict
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '422':
          description: Validation error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '429':
          description: Rate limited
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
      parameters:
      - $ref: '#/components/parameters/csrf'
  /me:
    get:
      tags:
      - Accounts
      operationId: getMe
      summary: Read profile
      responses:
        '200':
          description: Read profile
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Profile'
        '401':
          description: Unauthenticated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '403':
          description: Forbidden
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '404':
          description: Not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '409':
          description: Conflict
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '422':
          description: Validation error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '429':
          description: Rate limited
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
    patch:
      tags:
      - Accounts
      operationId: updateMe
      summary: Update profile
      responses:
        '200':
          description: Update profile
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Profile'
        '401':
          description: Unauthenticated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '403':
          description: Forbidden
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '404':
          description: Not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '409':
          description: Conflict
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '422':
          description: Validation error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '429':
          description: Rate limited
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ProfilePatch'
      parameters:
      - $ref: '#/components/parameters/csrf'
  /me/games:
    get:
      tags:
      - Accounts
      operationId: listMyGames
      summary: List games
      responses:
        '200':
          description: List games
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/GameSummary'
        '401':
          description: Unauthenticated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '403':
          description: Forbidden
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '404':
          description: Not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '409':
          description: Conflict
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '422':
          description: Validation error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '429':
          description: Rate limited
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
  /me/awards:
    get:
      tags:
      - Accounts
      operationId: listAwards
      summary: List awards
      responses:
        '200':
          description: List awards
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/Award'
        '401':
          description: Unauthenticated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '403':
          description: Forbidden
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '404':
          description: Not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '409':
          description: Conflict
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '422':
          description: Validation error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '429':
          description: Rate limited
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
  /me/ratings:
    get:
      tags:
      - Accounts
      operationId: listRatings
      summary: List ratings
      responses:
        '200':
          description: List ratings
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/Rating'
        '401':
          description: Unauthenticated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '403':
          description: Forbidden
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '404':
          description: Not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '409':
          description: Conflict
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '422':
          description: Validation error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '429':
          description: Rate limited
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
  /definitions:
    get:
      tags:
      - Definitions
      operationId: listDefinitions
      summary: List published definitions
      responses:
        '200':
          description: List published definitions
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/Definition'
        '401':
          description: Unauthenticated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '403':
          description: Forbidden
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '404':
          description: Not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '409':
          description: Conflict
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '422':
          description: Validation error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '429':
          description: Rate limited
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
    post:
      tags:
      - Definitions
      operationId: createDefinition
      summary: Create definition draft
      responses:
        '201':
          description: Create definition draft
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Definition'
        '401':
          description: Unauthenticated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '403':
          description: Forbidden
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '404':
          description: Not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '409':
          description: Conflict
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '422':
          description: Validation error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '429':
          description: Rate limited
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/DefinitionCreate'
      parameters:
      - $ref: '#/components/parameters/csrf'
  /definitions/import:
    post:
      tags:
      - Definitions
      operationId: importDefinition
      summary: Import portable JSON as draft
      responses:
        '201':
          description: Import portable JSON as draft
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Definition'
        '401':
          description: Unauthenticated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '403':
          description: Forbidden
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '404':
          description: Not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '409':
          description: Conflict
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '422':
          description: Validation error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '429':
          description: Rate limited
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ConfigDocument'
      parameters:
      - $ref: '#/components/parameters/csrf'
  /definitions/{definitionId}:
    get:
      tags:
      - Definitions
      operationId: getDefinition
      summary: Read definition
      responses:
        '200':
          description: Read definition
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Definition'
        '401':
          description: Unauthenticated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '403':
          description: Forbidden
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '404':
          description: Not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '409':
          description: Conflict
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '422':
          description: Validation error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '429':
          description: Rate limited
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
      parameters:
      - $ref: '#/components/parameters/definitionId'
    delete:
      tags:
      - Definitions
      operationId: deleteDefinition
      summary: Delete unreferenced draft-owned definition
      responses:
        '204':
          description: Delete unreferenced draft-owned definition
        '401':
          description: Unauthenticated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '403':
          description: Forbidden
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '404':
          description: Not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '409':
          description: Conflict
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '422':
          description: Validation error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '429':
          description: Rate limited
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
      parameters:
      - $ref: '#/components/parameters/definitionId'
      - $ref: '#/components/parameters/csrf'
  /definitions/{definitionId}/draft:
    get:
      tags:
      - Definitions
      operationId: getDraft
      summary: Read editable version
      responses:
        '200':
          description: Read editable version
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ConfigDocument'
        '401':
          description: Unauthenticated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '403':
          description: Forbidden
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '404':
          description: Not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '409':
          description: Conflict
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '422':
          description: Validation error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '429':
          description: Rate limited
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
      parameters:
      - $ref: '#/components/parameters/definitionId'
    put:
      tags:
      - Definitions
      operationId: saveDraft
      summary: Replace editable version transactionally
      responses:
        '200':
          description: Replace editable version transactionally
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ConfigDocument'
        '401':
          description: Unauthenticated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '403':
          description: Forbidden
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '404':
          description: Not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '409':
          description: Conflict
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '422':
          description: Validation error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '429':
          description: Rate limited
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ConfigDocument'
      parameters:
      - $ref: '#/components/parameters/definitionId'
      - $ref: '#/components/parameters/csrf'
  /definitions/{definitionId}/publish:
    post:
      tags:
      - Definitions
      operationId: publishDefinition
      summary: Validate and publish immutable version
      responses:
        '200':
          description: Validate and publish immutable version
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Definition'
        '401':
          description: Unauthenticated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '403':
          description: Forbidden
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '404':
          description: Not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '409':
          description: Conflict
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '422':
          description: Validation error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '429':
          description: Rate limited
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
      parameters:
      - $ref: '#/components/parameters/definitionId'
      - $ref: '#/components/parameters/csrf'
  /definitions/{definitionId}/duplicate:
    post:
      tags:
      - Definitions
      operationId: duplicateDefinition
      summary: Create an owned copy
      responses:
        '201':
          description: Create an owned copy
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Definition'
        '401':
          description: Unauthenticated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '403':
          description: Forbidden
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '404':
          description: Not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '409':
          description: Conflict
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '422':
          description: Validation error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '429':
          description: Rate limited
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
      parameters:
      - $ref: '#/components/parameters/definitionId'
      - $ref: '#/components/parameters/csrf'
  /definitions/{definitionId}/versions/{version}/export:
    get:
      tags:
      - Definitions
      operationId: exportVersion
      summary: Export portable JSON incl. assets
      responses:
        '200':
          description: Export portable JSON incl. assets
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ConfigDocument'
        '401':
          description: Unauthenticated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '403':
          description: Forbidden
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '404':
          description: Not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '409':
          description: Conflict
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '422':
          description: Validation error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '429':
          description: Rate limited
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
      parameters:
      - $ref: '#/components/parameters/definitionId'
      - $ref: '#/components/parameters/version'
  /definitions/{definitionId}/assets:
    post:
      tags:
      - Assets
      operationId: beginUpload
      summary: Create restricted temporary upload grant
      responses:
        '201':
          description: Create restricted temporary upload grant
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AssetUpload'
        '401':
          description: Unauthenticated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '403':
          description: Forbidden
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '404':
          description: Not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '409':
          description: Conflict
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '422':
          description: Validation error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '429':
          description: Rate limited
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/AssetUploadRequest'
      parameters:
      - $ref: '#/components/parameters/definitionId'
      - $ref: '#/components/parameters/csrf'
  /definitions/{definitionId}/assets/{assetId}/finalize:
    post:
      tags:
      - Assets
      operationId: finalizeUpload
      summary: Verify integrity and mark ready
      responses:
        '200':
          description: Verify integrity and mark ready
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Asset'
        '401':
          description: Unauthenticated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '403':
          description: Forbidden
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '404':
          description: Not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '409':
          description: Conflict
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '422':
          description: Validation error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '429':
          description: Rate limited
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
      parameters:
      - $ref: '#/components/parameters/definitionId'
      - $ref: '#/components/parameters/assetId'
      - $ref: '#/components/parameters/csrf'
  /definitions/{definitionId}/assets/{assetId}:
    delete:
      tags:
      - Assets
      operationId: deleteAsset
      summary: Delete unreferenced draft asset
      responses:
        '204':
          description: Delete unreferenced draft asset
        '401':
          description: Unauthenticated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '403':
          description: Forbidden
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '404':
          description: Not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '409':
          description: Conflict
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '422':
          description: Validation error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '429':
          description: Rate limited
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
      parameters:
      - $ref: '#/components/parameters/definitionId'
      - $ref: '#/components/parameters/assetId'
      - $ref: '#/components/parameters/csrf'
    get:
      tags:
      - Assets
      operationId: getAsset
      summary: Get authorized short-lived access
      responses:
        '200':
          description: Get authorized short-lived access
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AssetUpload'
        '401':
          description: Unauthenticated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '403':
          description: Forbidden
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '404':
          description: Not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '409':
          description: Conflict
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '422':
          description: Validation error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '429':
          description: Rate limited
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
      parameters:
      - $ref: '#/components/parameters/definitionId'
      - $ref: '#/components/parameters/assetId'
  /games:
    post:
      tags:
      - Games
      operationId: createGame
      summary: Create invitation
      responses:
        '201':
          description: Create invitation
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Game'
        '401':
          description: Unauthenticated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '403':
          description: Forbidden
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '404':
          description: Not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '409':
          description: Conflict
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '422':
          description: Validation error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '429':
          description: Rate limited
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/GameCreate'
      parameters:
      - $ref: '#/components/parameters/csrf'
  /games/{gameId}:
    get:
      tags:
      - Games
      operationId: getGame
      summary: Read authorized authoritative projection
      responses:
        '200':
          description: Read authorized authoritative projection
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Game'
        '401':
          description: Unauthenticated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '403':
          description: Forbidden
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '404':
          description: Not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '409':
          description: Conflict
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '422':
          description: Validation error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '429':
          description: Rate limited
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
      parameters:
      - $ref: '#/components/parameters/gameId'
  /games/{gameId}/invitation:
    get:
      tags:
      - Games
      operationId: getInvitation
      summary: Preview invitation
      responses:
        '200':
          description: Preview invitation
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Invitation'
        '401':
          description: Unauthenticated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '403':
          description: Forbidden
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '404':
          description: Not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '409':
          description: Conflict
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '422':
          description: Validation error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '429':
          description: Rate limited
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
      parameters:
      - $ref: '#/components/parameters/gameId'
  /games/{gameId}/join:
    post:
      tags:
      - Games
      operationId: joinGame
      summary: Join existing game idempotently
      responses:
        '200':
          description: Join existing game idempotently
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Game'
        '401':
          description: Unauthenticated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '403':
          description: Forbidden
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '404':
          description: Not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '409':
          description: Conflict
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '422':
          description: Validation error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '429':
          description: Rate limited
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/JoinRequest'
      parameters:
      - $ref: '#/components/parameters/gameId'
      - $ref: '#/components/parameters/csrf'
  /games/{gameId}/available-actions:
    get:
      tags:
      - Games
      operationId: availableActions
      summary: Generate available actor actions
      responses:
        '200':
          description: Generate available actor actions
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/AvailableAction'
        '401':
          description: Unauthenticated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '403':
          description: Forbidden
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '404':
          description: Not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '409':
          description: Conflict
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '422':
          description: Validation error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '429':
          description: Rate limited
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
      parameters:
      - $ref: '#/components/parameters/gameId'
  /games/{gameId}/actions:
    post:
      tags:
      - Games
      operationId: submitAction
      summary: Execute authoritative action
      responses:
        '200':
          description: Execute authoritative action
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ActionResult'
        '401':
          description: Unauthenticated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '403':
          description: Forbidden
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '404':
          description: Not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '409':
          description: Conflict
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '422':
          description: Validation error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '429':
          description: Rate limited
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ActionRequest'
      parameters:
      - $ref: '#/components/parameters/gameId'
      - $ref: '#/components/parameters/csrf'
  /games/{gameId}/events:
    get:
      tags:
      - Games
      operationId: getEvents
      summary: List accepted events
      responses:
        '200':
          description: List accepted events
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/GameEvent'
        '401':
          description: Unauthenticated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '403':
          description: Forbidden
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '404':
          description: Not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '409':
          description: Conflict
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '422':
          description: Validation error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '429':
          description: Rate limited
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
      parameters:
      - $ref: '#/components/parameters/gameId'
      - name: after
        in: query
        schema:
          type: integer
          minimum: 0
      - name: limit
        in: query
        schema:
          type: integer
          minimum: 1
          maximum: 100
          default: 50
  /games/{gameId}/realtime-grant:
    post:
      tags:
      - Games
      operationId: realtimeGrant
      summary: Authorize temporary game Broadcast subscription
      responses:
        '200':
          description: Authorize temporary game Broadcast subscription
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/RealtimeGrant'
        '401':
          description: Unauthenticated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '403':
          description: Forbidden
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '404':
          description: Not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '409':
          description: Conflict
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '422':
          description: Validation error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '429':
          description: Rate limited
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
      parameters:
      - $ref: '#/components/parameters/gameId'
      - $ref: '#/components/parameters/csrf'
components:
  securitySchemes:
    cookieSession:
      type: apiKey
      in: cookie
      name: bgwq_session
  parameters:
    definitionId:
      name: definitionId
      in: path
      required: true
      schema: &id001
        type: string
        format: uuid
    version:
      name: version
      in: path
      required: true
      schema:
        type: integer
        minimum: 1
    assetId:
      name: assetId
      in: path
      required: true
      schema: *id001
    gameId:
      name: gameId
      in: path
      required: true
      schema: *id001
    csrf:
      name: X-CSRF-Token
      in: header
      required: true
      schema: &id002
        type: string
  schemas:
    Error:
      type: object
      additionalProperties: false
      required:
      - code
      - message
      - request_id
      properties:
        code: *id002
        message: *id002
        request_id: *id001
        details:
          type: object
          additionalProperties: true
    Credentials:
      type: object
      additionalProperties: false
      required:
      - email
      - password
      properties:
        email:
          type: string
          format: email
        password:
          type: string
          minLength: 8
    Profile:
      type: object
      additionalProperties: false
      required:
      - id
      - display_name
      - anonymous
      properties:
        id: *id001
        display_name: *id002
        anonymous:
          type: boolean
        username:
          anyOf:
          - *id002
          - type: 'null'
    ProfilePatch:
      type: object
      additionalProperties: false
      required: []
      properties:
        display_name: *id002
        username:
          anyOf:
          - *id002
          - type: 'null'
    Session:
      type: object
      additionalProperties: false
      required:
      - authenticated
      - csrf_token
      properties:
        authenticated:
          type: boolean
        csrf_token: *id002
        profile:
          anyOf:
          - $ref: '#/components/schemas/Profile'
          - type: 'null'
    Definition:
      type: object
      additionalProperties: false
      required:
      - id
      - key
      - name
      - built_in
      - version
      - minimum_participants
      - maximum_participants
      properties:
        id: *id001
        key: *id002
        name: *id002
        built_in:
          type: boolean
        version: &id003
          type: integer
        minimum_participants: *id003
        maximum_participants: *id003
        description:
          anyOf:
          - *id002
          - type: 'null'
    DefinitionCreate:
      type: object
      additionalProperties: false
      required:
      - key
      - name
      properties:
        key: *id002
        name: *id002
        description: *id002
    ActionArgument:
      type: object
      additionalProperties: false
      required:
      - key
      - type
      - required
      properties:
        key: *id002
        type: *id002
        required:
          type: boolean
        choices:
          type: array
          items:
            type:
            - string
            - number
            - integer
            - boolean
            - 'null'
    AvailableAction:
      type: object
      additionalProperties: false
      required:
      - key
      - source_entity
      - parameters
      properties:
        key: *id002
        source_entity: *id001
        parameters:
          type: array
          items:
            $ref: '#/components/schemas/ActionArgument'
    Entity:
      type: object
      additionalProperties: false
      required:
      - id
      - type
      - kind
      - values
      properties:
        id: *id001
        type: *id002
        kind:
          enum:
          - game
          - space
          - item
          - objective
        owner:
          anyOf:
          - *id001
          - type: 'null'
        parent:
          anyOf:
          - *id001
          - type: 'null'
        location:
          anyOf:
          - *id001
          - type: 'null'
        values:
          type: object
          additionalProperties:
            type:
            - boolean
            - integer
            - number
            - string
            - 'null'
    Participant:
      type: object
      additionalProperties: false
      required:
      - id
      - user_id
      - role
      - seat
      - eliminated
      properties:
        id: *id001
        user_id: *id001
        role: *id002
        seat: *id003
        eliminated:
          type: boolean
    GameCreate:
      type: object
      additionalProperties: false
      required:
      - definition_id
      - version
      - idempotency_key
      - target_participants
      properties:
        definition_id: *id001
        version: *id003
        idempotency_key: *id002
        target_participants:
          type: integer
          minimum: 2
          maximum: 64
    GameSummary:
      type: object
      additionalProperties: false
      required:
      - id
      - status
      - revision
      - definition
      - target_participants
      properties:
        id: *id001
        status:
          enum:
          - pending
          - active
          - finished
          - expired
        revision: *id003
        target_participants:
          type: integer
          minimum: 2
          maximum: 64
        definition:
          $ref: '#/components/schemas/Definition'
    Game:
      type: object
      additionalProperties: false
      required:
      - id
      - status
      - revision
      - definition
      - target_participants
      - participants
      - entities
      - available_actions
      - server_time
      - outcomes
      properties:
        id: *id001
        status:
          enum:
          - pending
          - active
          - finished
          - expired
        revision: *id003
        target_participants:
          type: integer
          minimum: 2
          maximum: 64
        definition:
          $ref: '#/components/schemas/Definition'
        participants:
          type: array
          items:
            $ref: '#/components/schemas/Participant'
        entities:
          type: array
          items:
            $ref: '#/components/schemas/Entity'
        available_actions:
          type: array
          items:
            $ref: '#/components/schemas/AvailableAction'
        server_time: &id004
          type: string
          format: date-time
        outcomes:
          type: array
          description: Empty until the game is finished. Every participant has one outcome when finished.
          items:
            $ref: '#/components/schemas/GameOutcome'
    Invitation:
      type: object
      additionalProperties: false
      required:
      - game_id
      - status
      - expires_at
      - definition
      - target_participants
      properties:
        game_id: *id001
        status:
          enum:
          - pending
          - active
          - expired
        expires_at: *id004
        target_participants:
          type: integer
          minimum: 2
          maximum: 64
        definition:
          $ref: '#/components/schemas/Definition'
    JoinRequest:
      type: object
      additionalProperties: false
      required:
      - idempotency_key
      properties:
        idempotency_key: *id002
    Command:
      type: object
      additionalProperties: false
      required:
      - key
      - source_entity
      - parameters
      properties:
        key: *id002
        source_entity: *id001
        parameters:
          type: object
          additionalProperties: true
    ActionRequest:
      type: object
      additionalProperties: false
      required:
      - expected_revision
      - action_id
      - action
      properties:
        expected_revision:
          type: integer
          minimum: 0
        action_id: *id002
        action:
          $ref: '#/components/schemas/Command'
    GameEvent:
      type: object
      additionalProperties: false
      required:
      - id
      - revision
      - kind
      - occurred_at
      properties:
        id: *id001
        revision: *id003
        kind: *id002
        occurred_at: *id004
    ActionResult:
      type: object
      additionalProperties: false
      required:
      - revision
      - game
      - event
      properties:
        revision: *id003
        game:
          $ref: '#/components/schemas/Game'
        event:
          $ref: '#/components/schemas/GameEvent'
    Rating:
      type: object
      additionalProperties: false
      required:
      - definition_id
      - rating
      - games
      properties:
        definition_id: *id001
        rating: *id003
        games: *id003
    Award:
      type: object
      additionalProperties: false
      required:
      - game_id
      - objective_entity_id
      - points
      properties:
        game_id: *id001
        objective_entity_id: *id001
        points: *id003
    AssetUploadRequest:
      type: object
      additionalProperties: false
      required:
      - key
      - mime
      - bytes
      - sha256
      properties:
        key: *id002
        mime:
          enum:
          - image/png
          - image/webp
        bytes:
          type: integer
          minimum: 1
          maximum: 2097152
        sha256:
          type: string
          pattern: ^[a-f0-9]{64}$
    AssetUpload:
      type: object
      additionalProperties: false
      required:
      - asset_id
      - upload_url
      - expires_at
      properties:
        asset_id: *id001
        upload_url:
          type: string
          format: uri
        expires_at: *id004
    Asset:
      type: object
      additionalProperties: false
      required:
      - id
      - key
      - mime
      - bytes
      - sha256
      properties:
        id: *id001
        key: *id002
        mime: *id002
        bytes: *id003
        sha256: *id002
    RealtimeGrant:
      type: object
      additionalProperties: false
      required:
      - topic
      - token
      - expires_at
      properties:
        topic: *id002
        token: *id002
        expires_at: *id004
    ConfigDocument:
      title: BoardGamesWithQuests portable configuration v1
      description: Versioned, portable authoring format; database stores its normalized relational
        projection.
      type: object
      additionalProperties: false
      required:
      - format
      - format_version
      - definition
      - roles
      - phases
      - entities
      - seeds
      - links
      - fields
      - actions
      - visuals
      - assets
      properties:
        format:
          const: bgwq.configuration
        format_version:
          const: 1
        definition:
          type: object
          additionalProperties: false
          required:
          - key
          - name
          - min_participants
          - max_participants
          properties:
            key:
              $ref: '#/components/schemas/ConfigDocument/$defs/key'
            name:
              type: string
              minLength: 1
            description:
              type: string
            min_participants:
              type: integer
              minimum: 1
              maximum: 64
            max_participants:
              type: integer
              minimum: 1
              maximum: 64
            semantics_version:
              const: 1
        roles:
          type: array
          items:
            $ref: '#/components/schemas/ConfigDocument/$defs/role'
        phases:
          type: array
          minItems: 1
          items:
            $ref: '#/components/schemas/ConfigDocument/$defs/phase'
        entities:
          type: array
          minItems: 1
          items:
            $ref: '#/components/schemas/ConfigDocument/$defs/entity'
        seeds:
          type: array
          minItems: 1
          items:
            $ref: '#/components/schemas/ConfigDocument/$defs/seed'
        links:
          type: array
          items:
            $ref: '#/components/schemas/ConfigDocument/$defs/link'
        fields:
          type: array
          items:
            $ref: '#/components/schemas/ConfigDocument/$defs/field'
        actions:
          type: array
          minItems: 1
          items:
            $ref: '#/components/schemas/ConfigDocument/$defs/action'
        visuals:
          type: array
          items:
            $ref: '#/components/schemas/ConfigDocument/$defs/visual'
        assets:
          type: array
          items:
            $ref: '#/components/schemas/ConfigDocument/$defs/asset'
      $defs:
        key:
          type: string
          pattern: ^[a-z][a-z0-9_.-]*$
        role:
          type: object
          required:
          - key
          - name
          - min
          - max
          additionalProperties: false
          properties:
            key:
              $ref: '#/components/schemas/ConfigDocument/$defs/key'
            name:
              type: string
            min:
              type: integer
              minimum: 0
            max:
              type: integer
              minimum: 0
            forward_row:
              type:
              - integer
              - 'null'
              enum:
              - -1
              - 1
              - null
              description: Optional forward row orientation used by generic relative-vector operations.
        phase:
          type: object
          required:
          - key
          - name
          - initial
          - order
          additionalProperties: false
          properties:
            key:
              $ref: '#/components/schemas/ConfigDocument/$defs/key'
            name:
              type: string
            initial:
              type: boolean
            order:
              type: integer
        entity:
          type: object
          required:
          - key
          - kind
          - name
          additionalProperties: false
          properties:
            key:
              $ref: '#/components/schemas/ConfigDocument/$defs/key'
            kind:
              enum:
              - game
              - space
              - item
              - objective
            name:
              type: string
        seed:
          type: object
          required:
          - key
          - type
          additionalProperties: false
          properties:
            key:
              $ref: '#/components/schemas/ConfigDocument/$defs/key'
            type:
              $ref: '#/components/schemas/ConfigDocument/$defs/key'
            owner:
              type: integer
              minimum: 0
            parent:
              $ref: '#/components/schemas/ConfigDocument/$defs/key'
            location:
              $ref: '#/components/schemas/ConfigDocument/$defs/key'
            order:
              type: integer
            row:
              type: integer
            column:
              type: integer
            x:
              type: number
            y:
              type: number
            values:
              type: object
              additionalProperties:
                $ref: '#/components/schemas/ConfigDocument/$defs/value'
        link:
          type: object
          required:
          - source
          - target
          - relation
          additionalProperties: false
          properties:
            source:
              $ref: '#/components/schemas/ConfigDocument/$defs/key'
            target:
              $ref: '#/components/schemas/ConfigDocument/$defs/key'
            relation:
              $ref: '#/components/schemas/ConfigDocument/$defs/key'
            order:
              type: integer
        field:
          type: object
          required:
          - entity
          - key
          - type
          additionalProperties: false
          properties:
            entity:
              $ref: '#/components/schemas/ConfigDocument/$defs/key'
            key:
              $ref: '#/components/schemas/ConfigDocument/$defs/key'
            type:
              enum:
              - bool
              - int
              - decimal
              - text
              - instant
              - entity
              - participant
            nullable:
              type: boolean
            default:
              $ref: '#/components/schemas/ConfigDocument/$defs/value'
        value:
          type:
          - boolean
          - integer
          - number
          - string
          - 'null'
        expression:
          type: object
          required:
          - op
          additionalProperties: false
          properties:
            op:
              $ref: '#/components/schemas/ConfigDocument/$defs/key'
            args:
              type: object
              additionalProperties:
                anyOf:
                - $ref: '#/components/schemas/ConfigDocument/$defs/expression'
                - type: array
                  items:
                    $ref: '#/components/schemas/ConfigDocument/$defs/expression'
            value:
              $ref: '#/components/schemas/ConfigDocument/$defs/value'
            ref:
              type: string
            type:
              type: string
        effect:
          type: object
          required:
          - op
          additionalProperties: false
          properties:
            op:
              $ref: '#/components/schemas/ConfigDocument/$defs/key'
            when:
              $ref: '#/components/schemas/ConfigDocument/$defs/expression'
            args:
              type: object
              additionalProperties:
                anyOf:
                - $ref: '#/components/schemas/ConfigDocument/$defs/expression'
                - type: array
                  items:
                    $ref: '#/components/schemas/ConfigDocument/$defs/expression'
        action:
          type: object
          required:
          - key
          - entity
          - trigger
          - phase
          - condition
          - effects
          additionalProperties: false
          properties:
            key:
              $ref: '#/components/schemas/ConfigDocument/$defs/key'
            entity:
              $ref: '#/components/schemas/ConfigDocument/$defs/key'
            name:
              type: string
            trigger:
              enum:
              - command
              - hook
            hook:
              type: string
            phase:
              type: string
            parameters:
              type: array
              items:
                type: object
                required:
                - key
                - type
                additionalProperties: false
                properties:
                  key:
                    $ref: '#/components/schemas/ConfigDocument/$defs/key'
                  type:
                    type: string
                  required:
                    type: boolean
                  choices:
                    type: array
                    minItems: 1
                    uniqueItems: true
                    items:
                      type: string
            iterator:
              $ref: '#/components/schemas/ConfigDocument/$defs/expression'
            variable:
              type: string
            condition:
              $ref: '#/components/schemas/ConfigDocument/$defs/expression'
            effects:
              type: array
              items:
                $ref: '#/components/schemas/ConfigDocument/$defs/effect'
            priority:
              type: integer
        visual:
          type: object
          required:
          - entity
          - primitives
          additionalProperties: false
          properties:
            entity:
              $ref: '#/components/schemas/ConfigDocument/$defs/key'
            primitives:
              type: array
              items:
                type: object
                required:
                - kind
                additionalProperties: false
                properties:
                  kind:
                    enum:
                    - rectangle
                    - ellipse
                    - line
                    - path
                    - text
                    - image
                  x:
                    type: number
                  y:
                    type: number
                  width:
                    type: number
                  height:
                    type: number
                  fill:
                    type: string
                  stroke:
                    type: string
                  d:
                    type: string
                  text:
                    type: string
                  asset:
                    type: string
                  layer:
                    type: integer
        asset:
          type: object
          required:
          - key
          - mime
          - sha256
          - base64
          additionalProperties: false
          properties:
            key:
              $ref: '#/components/schemas/ConfigDocument/$defs/key'
            mime:
              enum:
              - image/png
              - image/webp
            sha256:
              type: string
              pattern: ^[0-9a-f]{64}$
            base64:
              type: string
    GameOutcome:
      type: object
      additionalProperties: false
      required:
      - participant_id
      - kind
      - score
      description: Immutable, participant-scoped settlement written atomically with the terminal
        accepted event.
      properties:
        participant_id:
          type: string
          format: uuid
        kind:
          type: string
          enum:
          - win
          - loss
          - draw
          - eliminated
        score:
          type: integer
          format: int64
```

## API ownership and persistence boundaries

This document fixes ownership and response behavior where a type schema alone cannot specify a transaction. The API reference above, [Prisma schema](../packages/server/supabase/schema.prisma), SQL design below, [engine UML](requirements/diagrams/engine_uml.mmd) and [client UML](requirements/diagrams/client_uml.mmd) must be reviewed together. No game-specific code paths are allowed in the interpreter.

| External actor operation | Authorization and persistent boundary | Commit/retry/failure observable contract |
| --- | --- | --- |
| Guest/login/upgrade/logout | Supabase verified identity; cookie/CSRF service boundary; `profiles.user_id` follows the stable Auth UUID | Guest upgrades preserve the identity and membership; expired or revoked sessions cannot read a private game |
| List/import/create/edit/publish definitions | Owner-bound `definitions`, `versions` and version-scoped rows; published versions immutable, all input through canonical JSON schema | Import validates every reference/operator; edit uses optimistic draft revision; publish is atomic or fully rejects without partial data |
| Create game | Authenticated creator, published pinned version, `games(creator_id, creation_key)` | Identical retry returns the one pending game; key reuse with different request is a conflict; no game-state seed until valid activation |
| Join game | Lock pending `games` row; authenticated `participants` seat/role scoped to the pinned version | Unique user and unique seat enforced, roles within bounded capacities; activation exactly once when defined minimum is reached |
| Read a game / available actions / events | `participants(game_id,user_id)` membership gate and pinned version; state in `game_entities`, `game_values`, links and clock rows | Viewer-specific redaction, no hidden data or action candidates leaked; cursor/history replay is revision-stable |
| Submit legal action | One SQL transaction: lock game, verify actor/role, check expected revision and digest/idempotency; run deterministic interpreter against isolated proposal | Append exactly one event with complete before/after mutations and trusted inputs; update game revision, state, active seats, clocks and terminal settlement atomically; same key+digest returns prior result, changed request rejects |
| Claim private Realtime grant | Membership-backed `bgwq.can_listen_to_game`, short-lived grant, private topic | Channel is revision hint only; reconnect and gaps require HTTP refetch, not trust of Broadcast payload |
| Terminal settlement | Same final action transaction; `game_outcomes` exactly one per occupied participant, optional authorized `awards` and `ratings` | Terminal state and rewards commit exactly once; no later gameplay commands except exact accepted idempotent retries |
| Attach visual asset | Owner draft and version-pinned Storage path, MIME/size/digest checks | Grant expiry and asset ownership enforced; staged asset is not published until verified |

## Complete HTTP operation ownership (33 operations)

Every design-reference `operationId` in API reference above has exactly one planned service transaction or query owner. The actual HTTP operation identifiers must be generated by implemented FastAPI routes, then compared with this reference. The example YAML captures proposed paths and verbs until FastAPI implements them; the table describes the intended persistence and failure boundary. The slash-separated Python files denote a call relationship, **not** duplicate service authorities.

| Operation ID | Owning service and collaborators | Authoritative data boundary | Externally observed contract |
| --- | --- | --- | --- |
| `getSession` | api/security.py → routes.py | Supabase Auth session; no private game query | 200 unauthenticated with valid pre-auth CSRF cookie; 401 only on malformed/hostile requests |
| `createGuest` | api/security.py → routes.py | Supabase anonymous Auth UUID, profile | 201 identity; rate-limited; no invalid cookie trust |
| `register` | api/security.py → routes.py | Supabase Auth registration; profile | 201 or typed validation; no duplicate profile |
| `login` | api/security.py → routes.py | Supabase Auth credentials/session | 200 session or typed 401 |
| `upgrade` | api/security.py → routes.py | Supabase Auth anonymous identity upgrade | 200 same Auth UUID; no loss of memberships |
| `logout` | api/security.py → routes.py | Supabase Auth token revocation | 204; old credentials denied |
| `getMe` | api/routes.py + repository.py | profiles by authenticated user_id | 200 own public-safe profile |
| `updateMe` | api/routes.py + repository.py | profiles by authenticated user_id | optimistic write; 403 cross-user |
| `listMyGames` | api/routes.py + repository.py | participants + games scoped by current user | 200 only own memberships |
| `listAwards` | api/routes.py + repository.py | awards + events for authenticated user | 200 only own durable rewards |
| `listRatings` | api/routes.py + repository.py | ratings keyed to user and eligible definition | 200 own ratings |
| `listDefinitions` | api/routes.py + repository.py | published versions + owned drafts | 200 public or permitted catalog |
| `createDefinition` | api/services.py + configuration/validation.py | definitions + version draft owner_id | 201 atomic draft; 409 conflict |
| `importDefinition` | api/services.py + configuration/transfer.py | owner draft relational version records | 201 validated JSON no dangling refs |
| `getDefinition` | api/routes.py + repository.py | definitions with published or authorized owner draft | 404 otherwise |
| `deleteDefinition` | api/services.py + repository.py | owner unpublished definition and version | reject referenced published versions |
| `getDraft` | api/routes.py + repository.py | owner-scoped unpublished version | 403/404 for others |
| `saveDraft` | api/services.py + repository.py | version-scoped relations optimistic draft state | 409 stale revision; no partial publication |
| `publishDefinition` | api/services.py + configuration/validation.py | version graph + protected publication timestamp | immutable published snapshot or rollback |
| `duplicateDefinition` | api/services.py + configuration/transfer.py | new owner version graph with remapped local ids | distinct ownership; no asset leaks |
| `exportVersion` | api/routes.py + configuration/transfer.py | immutable published version plus authorized assets | canonical portable JSON with stable local keys |
| `beginUpload` | api/assets.py + security.py | assets staged owner/version + Storage ticket | bounded scoped signed upload |
| `finalizeUpload` | api/assets.py + repository.py | assets digest/MIME verification and ready status | 409 mismatch; no published reference |
| `deleteAsset` | api/assets.py + repository.py | unpublished owner version and asset reference graph | reject linked or published resource |
| `getAsset` | api/assets.py + security.py | version-pinned authorized asset Storage grant | short-lived scoped retrieval |
| `createGame` | api/services.py + repository.py | games(creator_id,creation_key,target_participants) pinned versions | 201 pending game with immutable target; mismatching retry rejects |
| `getGame` | api/services.py + engine projection | games participants and viewer-redacted state | 401/404 unauthorized; latest revision |
| `getInvitation` | api/services.py + security.py | pending games and opaque invitation token | bounded pending eligibility; no private leak |
| `joinGame` | api/services.py + repository.py | locked game participant seat and role, target-bound capacity | join once, 409 occupied/stale; activate only at creator-selected target |
| `availableActions` | api/services.py + engine/runtime.py | pinned state plus authorized candidate enumeration | 200 legal viewer-scoped actions only |
| `submitAction` | api/services.py + engine/runtime.py | locked games state events mutations outcomes awards | atomic revision, idempotency, rollback |
| `getEvents` | api/services.py + repository.py | append-only events plus authorized redacted values | cursor/revision stable replay-safe history |
| `realtimeGrant` | api/realtime.py + security.py | membership gate and private Broadcast topic | short-lived participant-only grant |

## Global invariants

- `Version.minimumParticipants` and `maximumParticipants` are definition constraints, **not** a fixed two-seat engine. A creator picks `Game.targetParticipants` within the range; activation waits for exactly this size. `Participant.seat` is unique by game, and no unoccupied seat receives entities, wallets, active-turn rights or settlements.
- Runtime identifiers are always scoped by game; definition identifiers by immutable version. SQL composite foreign keys must reject cross-game and cross-version references.
- Client action arguments are untrusted. Evaluated conditions do no I/O; typed effects update a proposed state only. A committed event records server time and randomness, ensuring replay does not re-roll or recompute clocks.
- Read operations must never use a service role to bypass participant filtering without an explicit membership gate. Schema-only checks cannot certify these security obligations.
- Failure at any point before COMMIT leaves revision, game state, events, outcomes and awards unchanged; concurrently submitted actions cannot both accept an identical expected revision.

## Acceptance before implementation approval

Static validation must parse the canonical OpenAPI document, follow all schema references, validate all portable game JSON against the canonical JSON Schema, enforce a one-owner API operation map and check Prisma/SQL target relationships. The database baseline must additionally be applied from empty PostgreSQL/Supabase and tested with real Auth principals, RLS checks, conflicting actions, idempotent retries, disconnect/reconnect, and restart/replay. A blocked provider acceptance is **BLOCKED**, never reported as green.


## Supplemental PostgreSQL design reference (not an applied migration)

This SQL illustrates constraints that must be moved into **actual**, versioned database migrations and tested against Supabase/PostgreSQL before gameplay implementation can be considered finished. It is not executed by documentation builds. Prisma validation alone cannot prove these rules are enforced.

```sql
-- BoardGamesWithQuests supplemental PostgreSQL declarations.
-- schema.prisma is authoritative for tables, enums, indexes and intra-bgwq FKs.
-- This file defines features Prisma schema language cannot safely model:
-- CHECK constraints, partial unique indexes, Supabase-managed auth.users FKs,
-- private Broadcast policies, publication immutability and revision/event parity.
-- Reapply after Prisma Migrate; DO blocks are idempotent.
-- Changes to these contracts must be reviewed alongside schema.prisma.

-- definition_builtin_ownership: definitions schema-level invariant.
DO $bgwq_check$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'definition_builtin_ownership' AND conrelid = 'bgwq.definitions'::regclass) THEN
    ALTER TABLE bgwq."definitions" ADD CONSTRAINT "definition_builtin_ownership" CHECK ("built_in" = ("owner_id" IS NULL));
  END IF;
END $bgwq_check$;
-- definition_owner_key: filtered index not expressible without Prisma preview features.
CREATE UNIQUE INDEX IF NOT EXISTS "definition_owner_key" ON bgwq."definitions" ("owner_id", "key") WHERE "owner_id" IS NOT NULL;
-- builtin_definition_key: filtered index not expressible without Prisma preview features.
CREATE UNIQUE INDEX IF NOT EXISTS "builtin_definition_key" ON bgwq."definitions" ("key") WHERE "built_in";
-- version_bounds: versions schema-level invariant.
DO $bgwq_check$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'version_bounds' AND conrelid = 'bgwq.versions'::regclass) THEN
    ALTER TABLE bgwq."versions" ADD CONSTRAINT "version_bounds" CHECK ("minimum_participants">0 AND "maximum_participants">="minimum_participants");
  END IF;
END $bgwq_check$;
-- role_count: roles schema-level invariant.
DO $bgwq_check$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'role_count' AND conrelid = 'bgwq.roles'::regclass) THEN
    ALTER TABLE bgwq."roles" ADD CONSTRAINT "role_count" CHECK ("minimum_count">=0 AND "maximum_count">="minimum_count");
  END IF;
END $bgwq_check$;
-- role_forward_row: roles schema-level invariant.
DO $bgwq_check$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'role_forward_row' AND conrelid = 'bgwq.roles'::regclass) THEN
    ALTER TABLE bgwq."roles" ADD CONSTRAINT "role_forward_row" CHECK ("forward_row" IS NULL OR "forward_row" IN (-1,1));
  END IF;
END $bgwq_check$;
-- phase_single_initial: filtered index not expressible without Prisma preview features.
CREATE UNIQUE INDEX IF NOT EXISTS "phase_single_initial" ON bgwq."phases" ("version_id") WHERE "initial";
-- seed_not_self: entity_seeds schema-level invariant.
DO $bgwq_check$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'seed_not_self' AND conrelid = 'bgwq.entity_seeds'::regclass) THEN
    ALTER TABLE bgwq."entity_seeds" ADD CONSTRAINT "seed_not_self" CHECK ("parent_id" IS DISTINCT FROM "id" AND "location_id" IS DISTINCT FROM "id");
  END IF;
END $bgwq_check$;
-- seed_value_one_payload: seed_values schema-level invariant.
DO $bgwq_check$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'seed_value_one_payload' AND conrelid = 'bgwq.seed_values'::regclass) THEN
    ALTER TABLE bgwq."seed_values" ADD CONSTRAINT "seed_value_one_payload" CHECK (("kind"='none' AND num_nonnulls("bool_value","int_value","decimal_value","text_value","instant_value","ref_seed_id","ref_seat")=0) OR ("kind"='bool' AND "bool_value" IS NOT NULL AND num_nonnulls("bool_value","int_value","decimal_value","text_value","instant_value","ref_seed_id","ref_seat")=1) OR ("kind"='int' AND "int_value" IS NOT NULL AND num_nonnulls("bool_value","int_value","decimal_value","text_value","instant_value","ref_seed_id","ref_seat")=1) OR ("kind"='decimal' AND "decimal_value" IS NOT NULL AND num_nonnulls("bool_value","int_value","decimal_value","text_value","instant_value","ref_seed_id","ref_seat")=1) OR ("kind"='text' AND "text_value" IS NOT NULL AND num_nonnulls("bool_value","int_value","decimal_value","text_value","instant_value","ref_seed_id","ref_seat")=1) OR ("kind"='instant' AND "instant_value" IS NOT NULL AND num_nonnulls("bool_value","int_value","decimal_value","text_value","instant_value","ref_seed_id","ref_seat")=1) OR ("kind"='entity' AND "ref_seed_id" IS NOT NULL AND num_nonnulls("bool_value","int_value","decimal_value","text_value","instant_value","ref_seed_id","ref_seat")=1) OR ("kind"='participant' AND "ref_seat" IS NOT NULL AND num_nonnulls("bool_value","int_value","decimal_value","text_value","instant_value","ref_seed_id","ref_seat")=1));
  END IF;
END $bgwq_check$;
-- operator_kind: operators schema-level invariant.
DO $bgwq_check$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'operator_kind' AND conrelid = 'bgwq.operators'::regclass) THEN
    ALTER TABLE bgwq."operators" ADD CONSTRAINT "operator_kind" CHECK ("kind" IN ('expression','effect'));
  END IF;
END $bgwq_check$;
-- expression_kind: expressions schema-level invariant.
DO $bgwq_check$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'expression_kind' AND conrelid = 'bgwq.expressions'::regclass) THEN
    ALTER TABLE bgwq."expressions" ADD CONSTRAINT "expression_kind" CHECK ("kind" IN ('literal','context','field','local','call'));
  END IF;
END $bgwq_check$;
-- expression_not_self: expression_arguments schema-level invariant.
DO $bgwq_check$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'expression_not_self' AND conrelid = 'bgwq.expression_arguments'::regclass) THEN
    ALTER TABLE bgwq."expression_arguments" ADD CONSTRAINT "expression_not_self" CHECK ("parent_id"<>"child_id");
  END IF;
END $bgwq_check$;
-- action_trigger_check: actions schema-level invariant.
DO $bgwq_check$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'action_trigger_check' AND conrelid = 'bgwq.actions'::regclass) THEN
    ALTER TABLE bgwq."actions" ADD CONSTRAINT "action_trigger_check" CHECK (("trigger"='command' AND "hook_key" IS NULL) OR ("trigger"='hook' AND "hook_key" IS NOT NULL));
  END IF;
END $bgwq_check$;
-- action_iterator_pair: actions schema-level invariant.
DO $bgwq_check$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'action_iterator_pair' AND conrelid = 'bgwq.actions'::regclass) THEN
    ALTER TABLE bgwq."actions" ADD CONSTRAINT "action_iterator_pair" CHECK (("iterator_expression_id" IS NULL) = ("iterator_var" IS NULL));
  END IF;
END $bgwq_check$;
-- asset_size: assets schema-level invariant.
DO $bgwq_check$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'asset_size' AND conrelid = 'bgwq.assets'::regclass) THEN
    ALTER TABLE bgwq."assets" ADD CONSTRAINT "asset_size" CHECK ("bytes" BETWEEN 1 AND 2097152);
  END IF;
END $bgwq_check$;
-- asset_hash_lower_hex: assets schema-level invariant.
DO $bgwq_check$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'asset_hash_lower_hex' AND conrelid = 'bgwq.assets'::regclass) THEN
    ALTER TABLE bgwq."assets" ADD CONSTRAINT "asset_hash_lower_hex" CHECK ("sha256" ~ '^[0-9a-f]{64}$');
  END IF;
END $bgwq_check$;
-- asset_supported_mime: assets schema-level invariant.
DO $bgwq_check$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'asset_supported_mime' AND conrelid = 'bgwq.assets'::regclass) THEN
    ALTER TABLE bgwq."assets" ADD CONSTRAINT "asset_supported_mime" CHECK ("mime" IN ('image/png','image/webp'));
  END IF;
END $bgwq_check$;
-- asset_path_nonempty: assets schema-level invariant.
DO $bgwq_check$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'asset_path_nonempty' AND conrelid = 'bgwq.assets'::regclass) THEN
    ALTER TABLE bgwq."assets" ADD CONSTRAINT "asset_path_nonempty" CHECK (length(btrim("path"))>0);
  END IF;
END $bgwq_check$;
-- visual_primitive_kind: visual_primitives schema-level invariant.
DO $bgwq_check$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'visual_primitive_kind' AND conrelid = 'bgwq.visual_primitives'::regclass) THEN
    ALTER TABLE bgwq."visual_primitives" ADD CONSTRAINT "visual_primitive_kind" CHECK ("kind" IN ('rectangle','ellipse','line','path','text','image'));
  END IF;
END $bgwq_check$;
-- game_revision_nonnegative: games schema-level invariant.
DO $bgwq_check$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'game_revision_nonnegative' AND conrelid = 'bgwq.games'::regclass) THEN
    ALTER TABLE bgwq."games" ADD CONSTRAINT "game_revision_nonnegative" CHECK ("revision">=0 AND "turn">=0);
  END IF;
END $bgwq_check$;
-- game_lifecycle_timestamps: games schema-level invariant.
DO $bgwq_check$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'game_lifecycle_timestamps' AND conrelid = 'bgwq.games'::regclass) THEN
    ALTER TABLE bgwq."games" ADD CONSTRAINT "game_lifecycle_timestamps" CHECK (("status"='pending' AND "started_at" IS NULL AND "finished_at" IS NULL) OR ("status"='expired' AND "started_at" IS NULL AND "finished_at" IS NULL) OR ("status"='active' AND "started_at" IS NOT NULL AND "finished_at" IS NULL) OR ("status"='finished' AND "started_at" IS NOT NULL AND "finished_at" IS NOT NULL));
  END IF;
END $bgwq_check$;
-- participant_seat_nonnegative: participants schema-level invariant.
DO $bgwq_check$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'participant_seat_nonnegative' AND conrelid = 'bgwq.participants'::regclass) THEN
    ALTER TABLE bgwq."participants" ADD CONSTRAINT "participant_seat_nonnegative" CHECK ("seat">=0);
  END IF;
END $bgwq_check$;
-- runtime_entity_self: game_entities schema-level invariant.
DO $bgwq_check$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'runtime_entity_self' AND conrelid = 'bgwq.game_entities'::regclass) THEN
    ALTER TABLE bgwq."game_entities" ADD CONSTRAINT "runtime_entity_self" CHECK ("id" IS DISTINCT FROM "parent_id" AND "id" IS DISTINCT FROM "location_id");
  END IF;
END $bgwq_check$;
-- game_value_exactly_one: game_values schema-level invariant.
DO $bgwq_check$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'game_value_exactly_one' AND conrelid = 'bgwq.game_values'::regclass) THEN
    ALTER TABLE bgwq."game_values" ADD CONSTRAINT "game_value_exactly_one" CHECK (("kind"='none' AND num_nonnulls("bool_value","int_value","decimal_value","text_value","instant_value","ref_entity_id","ref_participant_id")=0) OR ("kind"='bool' AND "bool_value" IS NOT NULL AND num_nonnulls("bool_value","int_value","decimal_value","text_value","instant_value","ref_entity_id","ref_participant_id")=1) OR ("kind"='int' AND "int_value" IS NOT NULL AND num_nonnulls("bool_value","int_value","decimal_value","text_value","instant_value","ref_entity_id","ref_participant_id")=1) OR ("kind"='decimal' AND "decimal_value" IS NOT NULL AND num_nonnulls("bool_value","int_value","decimal_value","text_value","instant_value","ref_entity_id","ref_participant_id")=1) OR ("kind"='text' AND "text_value" IS NOT NULL AND num_nonnulls("bool_value","int_value","decimal_value","text_value","instant_value","ref_entity_id","ref_participant_id")=1) OR ("kind"='instant' AND "instant_value" IS NOT NULL AND num_nonnulls("bool_value","int_value","decimal_value","text_value","instant_value","ref_entity_id","ref_participant_id")=1) OR ("kind"='entity' AND "ref_entity_id" IS NOT NULL AND num_nonnulls("bool_value","int_value","decimal_value","text_value","instant_value","ref_entity_id","ref_participant_id")=1) OR ("kind"='participant' AND "ref_participant_id" IS NOT NULL AND num_nonnulls("bool_value","int_value","decimal_value","text_value","instant_value","ref_entity_id","ref_participant_id")=1));
  END IF;
END $bgwq_check$;
-- game_composite_kind: game_composites schema-level invariant.
DO $bgwq_check$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'game_composite_kind' AND conrelid = 'bgwq.game_composites'::regclass) THEN
    ALTER TABLE bgwq."game_composites" ADD CONSTRAINT "game_composite_kind" CHECK ("container_kind" IN ('list','record'));
  END IF;
END $bgwq_check$;
-- game_composite_entry_index: game_composite_entries schema-level invariant.
DO $bgwq_check$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'game_composite_entry_index' AND conrelid = 'bgwq.game_composite_entries'::regclass) THEN
    ALTER TABLE bgwq."game_composite_entries" ADD CONSTRAINT "game_composite_entry_index" CHECK ("ordinal">=0);
  END IF;
END $bgwq_check$;
-- game_composite_entry_value: game_composite_entries schema-level invariant.
DO $bgwq_check$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'game_composite_entry_value' AND conrelid = 'bgwq.game_composite_entries'::regclass) THEN
    ALTER TABLE bgwq."game_composite_entries" ADD CONSTRAINT "game_composite_entry_value" CHECK (("kind" IS NULL AND "child_composite_id" IS NOT NULL AND num_nonnulls("bool_value","int_value","decimal_value","text_value","instant_value","ref_entity_id","ref_participant_id","child_composite_id")=1) OR ("kind"='bool' AND "bool_value" IS NOT NULL AND num_nonnulls("bool_value","int_value","decimal_value","text_value","instant_value","ref_entity_id","ref_participant_id","child_composite_id")=1) OR ("kind"='int' AND "int_value" IS NOT NULL AND num_nonnulls("bool_value","int_value","decimal_value","text_value","instant_value","ref_entity_id","ref_participant_id","child_composite_id")=1) OR ("kind"='decimal' AND "decimal_value" IS NOT NULL AND num_nonnulls("bool_value","int_value","decimal_value","text_value","instant_value","ref_entity_id","ref_participant_id","child_composite_id")=1) OR ("kind"='text' AND "text_value" IS NOT NULL AND num_nonnulls("bool_value","int_value","decimal_value","text_value","instant_value","ref_entity_id","ref_participant_id","child_composite_id")=1) OR ("kind"='instant' AND "instant_value" IS NOT NULL AND num_nonnulls("bool_value","int_value","decimal_value","text_value","instant_value","ref_entity_id","ref_participant_id","child_composite_id")=1) OR ("kind"='entity' AND "ref_entity_id" IS NOT NULL AND num_nonnulls("bool_value","int_value","decimal_value","text_value","instant_value","ref_entity_id","ref_participant_id","child_composite_id")=1) OR ("kind"='participant' AND "ref_participant_id" IS NOT NULL AND num_nonnulls("bool_value","int_value","decimal_value","text_value","instant_value","ref_entity_id","ref_participant_id","child_composite_id")=1));
  END IF;
END $bgwq_check$;
-- game_composite_no_self: game_composite_entries schema-level invariant.
DO $bgwq_check$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'game_composite_no_self' AND conrelid = 'bgwq.game_composite_entries'::regclass) THEN
    ALTER TABLE bgwq."game_composite_entries" ADD CONSTRAINT "game_composite_no_self" CHECK ("composite_id" IS DISTINCT FROM "child_composite_id");
  END IF;
END $bgwq_check$;
-- clock_nonnegative: clocks schema-level invariant.
DO $bgwq_check$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'clock_nonnegative' AND conrelid = 'bgwq.clocks'::regclass) THEN
    ALTER TABLE bgwq."clocks" ADD CONSTRAINT "clock_nonnegative" CHECK ("remaining_ms">=0 AND "increment_ms">=0);
  END IF;
END $bgwq_check$;
-- event_value_one_payload: event_values schema-level invariant.
DO $bgwq_check$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'event_value_one_payload' AND conrelid = 'bgwq.event_values'::regclass) THEN
    ALTER TABLE bgwq."event_values" ADD CONSTRAINT "event_value_one_payload" CHECK (("kind"='none' AND num_nonnulls("bool_value","int_value","decimal_value","text_value","instant_value","entity_id","participant_id")=0) OR ("kind"='bool' AND "bool_value" IS NOT NULL AND num_nonnulls("bool_value","int_value","decimal_value","text_value","instant_value","entity_id","participant_id")=1) OR ("kind"='int' AND "int_value" IS NOT NULL AND num_nonnulls("bool_value","int_value","decimal_value","text_value","instant_value","entity_id","participant_id")=1) OR ("kind"='decimal' AND "decimal_value" IS NOT NULL AND num_nonnulls("bool_value","int_value","decimal_value","text_value","instant_value","entity_id","participant_id")=1) OR ("kind"='text' AND "text_value" IS NOT NULL AND num_nonnulls("bool_value","int_value","decimal_value","text_value","instant_value","entity_id","participant_id")=1) OR ("kind"='instant' AND "instant_value" IS NOT NULL AND num_nonnulls("bool_value","int_value","decimal_value","text_value","instant_value","entity_id","participant_id")=1) OR ("kind"='entity' AND "entity_id" IS NOT NULL AND num_nonnulls("bool_value","int_value","decimal_value","text_value","instant_value","entity_id","participant_id")=1) OR ("kind"='participant' AND "participant_id" IS NOT NULL AND num_nonnulls("bool_value","int_value","decimal_value","text_value","instant_value","entity_id","participant_id")=1));
  END IF;
END $bgwq_check$;
-- mutation_target_kind: event_mutations schema-level invariant.
DO $bgwq_check$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'mutation_target_kind' AND conrelid = 'bgwq.event_mutations'::regclass) THEN
    ALTER TABLE bgwq."event_mutations" ADD CONSTRAINT "mutation_target_kind" CHECK ("target_kind" IN ('entity','link','field','phase','active_participant','clock','award','game'));
  END IF;
END $bgwq_check$;
-- award_points: awards schema-level invariant.
DO $bgwq_check$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'award_points' AND conrelid = 'bgwq.awards'::regclass) THEN
    ALTER TABLE bgwq."awards" ADD CONSTRAINT "award_points" CHECK ("points">=0);
  END IF;
END $bgwq_check$;
-- rating_counts: ratings schema-level invariant.
DO $bgwq_check$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'rating_counts' AND conrelid = 'bgwq.ratings'::regclass) THEN
    ALTER TABLE bgwq."ratings" ADD CONSTRAINT "rating_counts" CHECK ("games"="wins"+"draws"+"losses");
  END IF;
END $bgwq_check$;
-- rating_nonnegative: ratings schema-level invariant.
DO $bgwq_check$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'rating_nonnegative' AND conrelid = 'bgwq.ratings'::regclass) THEN
    ALTER TABLE bgwq."ratings" ADD CONSTRAINT "rating_nonnegative" CHECK ("games">=0 AND "wins">=0 AND "draws">=0 AND "losses">=0 AND "rating">=0);
  END IF;
END $bgwq_check$;

-- A mutation's before/after payload is typed. Structural inserts/removals use
-- absent before/after respectively; scalar references remain UUIDs in the log.
DO $bgwq_check$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'mutation_typed_before' AND conrelid = 'bgwq.event_mutations'::regclass) THEN
    ALTER TABLE bgwq.event_mutations ADD CONSTRAINT mutation_typed_before CHECK (
      (before_kind IS NULL AND num_nonnulls(before_bool,before_int,before_decimal,before_text,before_instant,before_ref)=0)
      OR (before_kind='none' AND num_nonnulls(before_bool,before_int,before_decimal,before_text,before_instant,before_ref)=0)
      OR (before_kind='bool' AND before_bool IS NOT NULL AND num_nonnulls(before_bool,before_int,before_decimal,before_text,before_instant,before_ref)=1)
      OR (before_kind='int' AND before_int IS NOT NULL AND num_nonnulls(before_bool,before_int,before_decimal,before_text,before_instant,before_ref)=1)
      OR (before_kind='decimal' AND before_decimal IS NOT NULL AND num_nonnulls(before_bool,before_int,before_decimal,before_text,before_instant,before_ref)=1)
      OR (before_kind='text' AND before_text IS NOT NULL AND num_nonnulls(before_bool,before_int,before_decimal,before_text,before_instant,before_ref)=1)
      OR (before_kind='instant' AND before_instant IS NOT NULL AND num_nonnulls(before_bool,before_int,before_decimal,before_text,before_instant,before_ref)=1)
      OR (before_kind IN ('entity','participant') AND before_ref IS NOT NULL AND num_nonnulls(before_bool,before_int,before_decimal,before_text,before_instant,before_ref)=1)
    );
  END IF;
END $bgwq_check$;
DO $bgwq_check$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'mutation_typed_after' AND conrelid = 'bgwq.event_mutations'::regclass) THEN
    ALTER TABLE bgwq.event_mutations ADD CONSTRAINT mutation_typed_after CHECK (
      (after_kind IS NULL AND num_nonnulls(after_bool,after_int,after_decimal,after_text,after_instant,after_ref)=0)
      OR (after_kind='none' AND num_nonnulls(after_bool,after_int,after_decimal,after_text,after_instant,after_ref)=0)
      OR (after_kind='bool' AND after_bool IS NOT NULL AND num_nonnulls(after_bool,after_int,after_decimal,after_text,after_instant,after_ref)=1)
      OR (after_kind='int' AND after_int IS NOT NULL AND num_nonnulls(after_bool,after_int,after_decimal,after_text,after_instant,after_ref)=1)
      OR (after_kind='decimal' AND after_decimal IS NOT NULL AND num_nonnulls(after_bool,after_int,after_decimal,after_text,after_instant,after_ref)=1)
      OR (after_kind='text' AND after_text IS NOT NULL AND num_nonnulls(after_bool,after_int,after_decimal,after_text,after_instant,after_ref)=1)
      OR (after_kind='instant' AND after_instant IS NOT NULL AND num_nonnulls(after_bool,after_int,after_decimal,after_text,after_instant,after_ref)=1)
      OR (after_kind IN ('entity','participant') AND after_ref IS NOT NULL AND num_nonnulls(after_bool,after_int,after_decimal,after_text,after_instant,after_ref)=1)
    );
  END IF;
END $bgwq_check$;

-- Supabase-managed auth.users is NOT created, altered, or migrated by Prisma.
-- Its external identity foreign keys are declared only as constraints against
-- UUID columns in bgwq-owned tables. Their referential behavior is RESTRICT.
DO $bgwq_auth$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_profiles_user_id_auth_users' AND conrelid = 'bgwq.profiles'::regclass) THEN
    ALTER TABLE bgwq."profiles" ADD CONSTRAINT "fk_profiles_user_id_auth_users" FOREIGN KEY ("user_id") REFERENCES auth.users(id) ON DELETE RESTRICT;
  END IF;
END $bgwq_auth$;
DO $bgwq_auth$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_definitions_owner_id_auth_users' AND conrelid = 'bgwq.definitions'::regclass) THEN
    ALTER TABLE bgwq."definitions" ADD CONSTRAINT "fk_definitions_owner_id_auth_users" FOREIGN KEY ("owner_id") REFERENCES auth.users(id) ON DELETE RESTRICT;
  END IF;
END $bgwq_auth$;
DO $bgwq_auth$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_games_creator_id_auth_users' AND conrelid = 'bgwq.games'::regclass) THEN
    ALTER TABLE bgwq."games" ADD CONSTRAINT "fk_games_creator_id_auth_users" FOREIGN KEY ("creator_id") REFERENCES auth.users(id) ON DELETE RESTRICT;
  END IF;
END $bgwq_auth$;
DO $bgwq_auth$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_participants_user_id_auth_users' AND conrelid = 'bgwq.participants'::regclass) THEN
    ALTER TABLE bgwq."participants" ADD CONSTRAINT "fk_participants_user_id_auth_users" FOREIGN KEY ("user_id") REFERENCES auth.users(id) ON DELETE RESTRICT;
  END IF;
END $bgwq_auth$;
DO $bgwq_auth$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_ratings_user_id_auth_users' AND conrelid = 'bgwq.ratings'::regclass) THEN
    ALTER TABLE bgwq."ratings" ADD CONSTRAINT "fk_ratings_user_id_auth_users" FOREIGN KEY ("user_id") REFERENCES auth.users(id) ON DELETE RESTRICT;
  END IF;
END $bgwq_auth$;

-- Database security and runtime integrity beyond Prisma Schema Language.
-- PostgreSQL-only invariants not representable by Prisma Schema Language.
-- Apply AFTER the Prisma-generated schema migration; review before production deployment.
-- This file is part of the declarative contract, not gameplay scripting.

REVOKE ALL ON SCHEMA bgwq FROM PUBLIC, anon, authenticated;
REVOKE ALL ON ALL TABLES IN SCHEMA bgwq FROM PUBLIC, anon, authenticated;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA bgwq FROM PUBLIC, anon, authenticated;

-- A version is frozen after publication, and publishing a version never
-- changes definitions pinned by existing games.
CREATE OR REPLACE FUNCTION bgwq.reject_published_version_mutation()
RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = '' AS $$
DECLARE v_id uuid;
BEGIN
  v_id := CASE WHEN TG_OP = 'INSERT' THEN NEW.version_id ELSE OLD.version_id END;
  -- Check the old owner on UPDATE as well as the new owner. Otherwise a
  -- published row could be moved into a draft and modified.
  IF EXISTS (SELECT 1 FROM bgwq.versions WHERE id = v_id AND published_at IS NOT NULL) THEN
    RAISE EXCEPTION 'published configuration is immutable: %', v_id USING ERRCODE = '23514';
  END IF;
  IF TG_OP = 'UPDATE' THEN
    IF NEW.version_id IS DISTINCT FROM OLD.version_id
       AND EXISTS (SELECT 1 FROM bgwq.versions WHERE id = NEW.version_id AND published_at IS NOT NULL) THEN
      RAISE EXCEPTION 'destination published configuration is immutable: %', NEW.version_id USING ERRCODE = '23514';
    END IF;
  END IF;
  IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
  RETURN NEW;
END;
$$;

-- This dynamic loop is DDL setup, NOT a gameplay execution interpreter.
DO $$
DECLARE table_name text;
BEGIN
  FOREACH table_name IN ARRAY ARRAY[
    'roles','phases','entity_types','entity_seeds','seed_links','fields',
    'seed_values','expressions','expression_arguments','actions',
    'action_parameters','phase_actions','effects','effect_arguments',
    'assets','visual_templates','visual_primitives'
  ] LOOP
    EXECUTE format('DROP TRIGGER IF EXISTS immutable_published ON bgwq.%I', table_name);
    EXECUTE format(
      'CREATE TRIGGER immutable_published BEFORE INSERT OR UPDATE OR DELETE ON bgwq.%I '
      || 'FOR EACH ROW EXECUTE FUNCTION bgwq.reject_published_version_mutation()',
      table_name
    );
  END LOOP;
END;
$$;

CREATE OR REPLACE FUNCTION bgwq.protect_version_header()
RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = '' AS $$
BEGIN
  IF TG_OP = 'DELETE' AND OLD.published_at IS NOT NULL THEN
    RAISE EXCEPTION 'cannot delete published definition';
  END IF;
  IF TG_OP = 'UPDATE' AND OLD.published_at IS NOT NULL THEN
    RAISE EXCEPTION 'cannot mutate published definition';
  END IF;
  IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
  RETURN NEW;
END;
$$;
DROP TRIGGER IF EXISTS immutable_version_header ON bgwq.versions;
CREATE TRIGGER immutable_version_header
BEFORE UPDATE OR DELETE ON bgwq.versions
FOR EACH ROW EXECUTE FUNCTION bgwq.protect_version_header();

-- Accepted history is append-only, including mutation arguments.
CREATE OR REPLACE FUNCTION bgwq.reject_history_mutation()
RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = '' AS $$
BEGIN
  RAISE EXCEPTION 'accepted event log is append-only' USING ERRCODE = '23514';
END;
$$;
DROP TRIGGER IF EXISTS immutable_event ON bgwq.events;
CREATE TRIGGER immutable_event BEFORE UPDATE OR DELETE ON bgwq.events
FOR EACH ROW EXECUTE FUNCTION bgwq.reject_history_mutation();
DROP TRIGGER IF EXISTS immutable_event_values ON bgwq.event_values;
CREATE TRIGGER immutable_event_values BEFORE UPDATE OR DELETE ON bgwq.event_values
FOR EACH ROW EXECUTE FUNCTION bgwq.reject_history_mutation();
DROP TRIGGER IF EXISTS immutable_event_mutations ON bgwq.event_mutations;
CREATE TRIGGER immutable_event_mutations BEFORE UPDATE OR DELETE ON bgwq.event_mutations
FOR EACH ROW EXECUTE FUNCTION bgwq.reject_history_mutation();

-- Database-triggered revision hints never disclose hidden game state.
-- realtime.send takes JSONB because Supabase's transport requires JSON;
-- the payload is NOT an authoritative configuration/state JSONB column.
CREATE OR REPLACE FUNCTION bgwq.broadcast_revision()
RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = '' AS $$
BEGIN
  PERFORM realtime.send(
    jsonb_build_object('game_id', NEW.game_id, 'revision', NEW.revision),
    'revision',
    'game:' || NEW.game_id::text,
    true
  );
  RETURN NEW;
END;
$$;
DROP TRIGGER IF EXISTS emit_revision_hint ON bgwq.events;
CREATE TRIGGER emit_revision_hint AFTER INSERT ON bgwq.events
FOR EACH ROW EXECUTE FUNCTION bgwq.broadcast_revision();

-- Private realtime messages must only be readable by actual game members.
-- The database API remains private; this security-definer function reads
-- membership without granting table SELECT to frontend roles.
CREATE OR REPLACE FUNCTION bgwq.can_listen_to_game(topic text)
RETURNS boolean LANGUAGE sql STABLE SECURITY DEFINER SET search_path = '' AS $$
 SELECT topic LIKE 'game:%' AND (SELECT auth.uid()) IS NOT NULL AND EXISTS (
   SELECT 1 FROM bgwq.participants p
   WHERE p.game_id::text = split_part(topic, ':', 2)
     AND p.user_id = (SELECT auth.uid())
 );
$$;
REVOKE ALL ON FUNCTION bgwq.can_listen_to_game(text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION bgwq.can_listen_to_game(text) TO authenticated;

DROP POLICY IF EXISTS bgwq_game_broadcast_read ON realtime.messages;
CREATE POLICY bgwq_game_broadcast_read ON realtime.messages
FOR SELECT TO authenticated
USING (bgwq.can_listen_to_game(realtime.topic()));

-- Private schema usage permits the explicitly granted policy helper to be called;
-- no application table privileges are granted to browser roles.
GRANT USAGE ON SCHEMA bgwq TO authenticated;

-- A game must pin a published definition at creation. Publication is the only
-- point at which the complete type graph is accepted by the API validator.
CREATE OR REPLACE FUNCTION bgwq.assert_game_definition_published()
RETURNS trigger LANGUAGE plpgsql SECURITY INVOKER SET search_path = '' AS $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM bgwq.versions v
    WHERE v.id = NEW.version_id AND v.published_at IS NOT NULL
  ) THEN
    RAISE EXCEPTION 'a game must pin a published definition version'
      USING ERRCODE = '23514';
  END IF;
  RETURN NEW;
END;
$$;
DROP TRIGGER IF EXISTS game_requires_publication ON bgwq.games;
CREATE TRIGGER game_requires_publication
BEFORE INSERT OR UPDATE OF version_id ON bgwq.games
FOR EACH ROW EXECUTE FUNCTION bgwq.assert_game_definition_published();


-- A lobby starts only when its immutable creator-selected target is full.
CREATE OR REPLACE FUNCTION bgwq.enforce_game_target_size()
RETURNS trigger LANGUAGE plpgsql SECURITY INVOKER SET search_path = '' AS $
DECLARE
  minimum_size integer;
  maximum_size integer;
BEGIN
  SELECT v.minimum_participants, v.maximum_participants INTO minimum_size, maximum_size
    FROM bgwq.versions AS v WHERE v.id = NEW.version_id;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'game references an unknown definition version' USING ERRCODE = '23503';
  END IF;
  IF NEW.target_participants < minimum_size OR NEW.target_participants > maximum_size THEN
    RAISE EXCEPTION 'game target is outside published participant bounds' USING ERRCODE = '23514';
  END IF;
  IF TG_OP = 'UPDATE' THEN
    IF NEW.target_participants IS DISTINCT FROM OLD.target_participants THEN
      RAISE EXCEPTION 'game target participants are immutable' USING ERRCODE = '23514';
    END IF;
  END IF;
  RETURN NEW;
END;
$;
DROP TRIGGER IF EXISTS game_target_size_guard ON bgwq.games;
CREATE TRIGGER game_target_size_guard
BEFORE INSERT OR UPDATE OF target_participants, version_id ON bgwq.games
FOR EACH ROW EXECUTE FUNCTION bgwq.enforce_game_target_size();

-- Enforce variable participant bounds and per-role capacities at the database
-- boundary, independently of FastAPI checks. Locking the parent game row
-- serializes competing joins even under the default READ COMMITTED isolation.
CREATE OR REPLACE FUNCTION bgwq.enforce_participant_capacity()
RETURNS trigger LANGUAGE plpgsql SECURITY INVOKER SET search_path = '' AS $$
DECLARE
  g_version uuid;
  g_status bgwq.game_status;
  max_seats integer;
  max_role integer;
  used_seats integer;
  used_role integer;
BEGIN
  SELECT g.version_id, g.status, g.target_participants
    INTO g_version, g_status, max_seats
    FROM bgwq.games AS g
    JOIN bgwq.versions AS v ON v.id = g.version_id
    WHERE g.id = NEW.game_id FOR UPDATE OF g;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'participant game is not available' USING ERRCODE = '23503';
  END IF;
  IF g_status <> 'pending' THEN
    RAISE EXCEPTION 'participants may join only pending games' USING ERRCODE = '23514';
  END IF;
  IF NEW.version_id <> g_version OR NEW.seat < 0 OR NEW.seat >= max_seats THEN
    RAISE EXCEPTION 'seat is outside the pinned definition capacity' USING ERRCODE = '23514';
  END IF;
  SELECT r.maximum_count INTO max_role
    FROM bgwq.roles AS r WHERE r.version_id = g_version AND r.id = NEW.role_id;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'participant role is not part of the pinned version' USING ERRCODE = '23503';
  END IF;
  SELECT count(*) INTO used_seats FROM bgwq.participants p
    WHERE p.game_id = NEW.game_id AND p.id IS DISTINCT FROM NEW.id;
  SELECT count(*) INTO used_role FROM bgwq.participants p
    WHERE p.game_id = NEW.game_id AND p.role_id = NEW.role_id
      AND p.id IS DISTINCT FROM NEW.id;
  IF used_seats >= max_seats OR used_role >= max_role THEN
    RAISE EXCEPTION 'configured game or role capacity exceeded' USING ERRCODE = '23514';
  END IF;
  RETURN NEW;
END;
$$;
DROP TRIGGER IF EXISTS participant_capacity_guard ON bgwq.participants;
CREATE TRIGGER participant_capacity_guard
BEFORE INSERT OR UPDATE OF game_id, version_id, role_id, seat ON bgwq.participants
FOR EACH ROW EXECUTE FUNCTION bgwq.enforce_participant_capacity();

-- Outcome rows are immutable settlement records; account ratings/awards may be
-- updated by authorized settlement services but never by author-defined effects.
DROP TRIGGER IF EXISTS immutable_game_outcomes ON bgwq.game_outcomes;
CREATE TRIGGER immutable_game_outcomes BEFORE UPDATE OR DELETE ON bgwq.game_outcomes
FOR EACH ROW EXECUTE FUNCTION bgwq.reject_history_mutation();

-- Check event/revision parity at COMMIT, after the service has written both the
-- materialized state and its immutable event. This detects missing or orphan
-- accepted events without requiring the HTTP layer to write event logs first.
CREATE OR REPLACE FUNCTION bgwq.assert_game_event_parity()
RETURNS trigger LANGUAGE plpgsql SECURITY INVOKER SET search_path = '' AS $$
DECLARE
  the_game uuid;
  g bgwq.games%ROWTYPE;
  n bigint;
  top_revision bigint;
BEGIN
  the_game := CASE WHEN TG_TABLE_NAME = 'games' THEN NEW.id ELSE NEW.game_id END;
  SELECT * INTO g FROM bgwq.games WHERE id = the_game;
  IF NOT FOUND THEN RETURN NULL; END IF;
  SELECT count(*), max(revision) INTO n, top_revision
    FROM bgwq.events WHERE game_id = the_game;
  IF g.status = 'finished' AND
     (SELECT count(*) FROM bgwq.game_outcomes WHERE game_id = the_game)
         <> (SELECT count(*) FROM bgwq.participants WHERE game_id = the_game) THEN
    RAISE EXCEPTION 'finished game requires a final result for each participant' USING ERRCODE='23514';
  END IF;
  IF g.status IN ('pending','expired') THEN
    IF n <> 0 THEN
      RAISE EXCEPTION 'pre-activation game has accepted events' USING ERRCODE='23514';
    END IF;
  ELSIF n <> g.revision + 1 OR top_revision <> g.revision THEN
    RAISE EXCEPTION 'game revision % differs from immutable event history for %',g.revision,the_game
      USING ERRCODE='23514';
  END IF;
  RETURN NULL;
END;
$$;
DROP TRIGGER IF EXISTS check_game_revision_history ON bgwq.games;
CREATE CONSTRAINT TRIGGER check_game_revision_history
AFTER INSERT OR UPDATE ON bgwq.games
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION bgwq.assert_game_event_parity();
DROP TRIGGER IF EXISTS check_event_revision_history ON bgwq.events;
CREATE CONSTRAINT TRIGGER check_event_revision_history
AFTER INSERT ON bgwq.events
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION bgwq.assert_game_event_parity();
```
