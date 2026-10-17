# ARCHITECTURE — source tree, tooling and components

This is the **intended tracked source layout**, not a claim that the implementation files already exist. The merged Git-backed documentation pipeline is authoritative; the target-source graph below is a specification, distinct from source-derived diagrams of code actually present. Every leaf carries a source-level responsibility or documentation contract inline. The [Mermaid AST](AST.mmd) declares the same leaf paths, public interfaces and actual typed dependencies; game-specific JSON action instances do not become source files or AST execution modules.

## Stack and authority

| Concern | Normative choice |
| --- | --- |
| Frontend | Bun, React, TypeScript, Wouter, Rsbuild, Tailwind, shadcn/ui and Motion; SVG scene renderer |
| Native | Tauri 2 WebView of the same HTTPS frontend (not a second UI or engine) |
| API | Python FastAPI and Pydantic on a separate Vercel project |
| Engine | Pure deterministic Python interpreter over entities, actions, conditions, effects and hooks |
| Database | Supabase PostgreSQL, Prisma Schema Language for schema/migration authoring, Python psycopg for runtime I/O |
| Security | Supabase Auth, private Realtime Broadcast, private Storage, backend-enforced authorization and CSRF |
| Documentation | TSDoc, Python docstrings, Rustdoc, OpenAPI and a live interactive Mermaid AST |
| Verification | pytest, Playwright, native smoke tests, real database migrations and cross-contract validation |

Prisma is **schema authoring tooling**, not a production Node.js database runtime. PostgreSQL-specific SQL in [integrity.sql](../../../packages/server/supabase/integrity.sql) is mandatory only for guarantees PSL cannot represent: CHECK constraints, partial indexes, Supabase Auth references, trigger-based immutability, event parity, and private Broadcast authorization. The SQL must be applied after Prisma's schema-generated migration and verified against real PostgreSQL; it never implements gameplay rules.

## Intended source tree

```text
.agents/  # Product and architectural requirements; implementation lives in packages, not here.
  notes/  # Source-authored product requirements and referenced design material.
    diagrams/  # Source-backed Mermaid diagrams; rendered SVGs are deployment artifacts, not committed diagram sources.
      implementation/  # Generated from actual tracked source declarations.
        ast.mmd  # Repository-wide cross-language file/declaration graph.
        uml.mmd  # Actual Python class signatures, inheritance and typed associations.
      reference/  # Authored design references, not verified runtime architecture.
        mvc.mmd  # Reference MVC diagram.
        uml.mmd  # Reference UML diagram.
    images/  # Immutable original visual references.
      GUI_mockup.svg  # Excalidraw image retained as original SVG, not converted to Mermaid.
    requirements/  # Normative interfaces, annotated architecture and the source-only Mermaid diagram.
      ARCHITECTURE.md  # Annotated source inventory and exact package ownership; every file has inline input/output/invariant documentation and graph counterpart.
      AST.mmd  # Single Mermaid declaration/dependency/control-flow graph; each implementation declaration has typed contract and deterministic operation semantics.
  PRD.md  # Product invariants, user journeys and behavior acceptance only; links to canonical architecture, API, Prisma schema, AST and portable data.
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
    test_docs_browser.mjs  # Browser-level reader, image zoom/modal and collapsible-navigation checks.
    test_docs_publication.py  # Staging, missing-main behavior and preview filtering checks.
    test_documentation_site.py  # Verify all Git-tracked pages and compiled Mermaid diagrams.
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
      openapi.yaml  # Canonical OpenAPI 3.1 paths, operation IDs and typed request/response bodies; API Python contracts and web generated types must match.
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
      integrity.sql  # Database-only constraints, cross-version guards, Supabase Auth FKs, immutable publication and event parity, private Realtime; companion to Prisma migrations.
      schema.prisma  # Authoritative Prisma PostgreSQL 38-model relational declaration; migration-only tooling, no Node runtime.
    pyproject.toml  # Python dependencies and pytest; FastAPI psycopg Pydantic and validation dependencies
    vercel.json  # ASGI route and limits; Deploy Python entrypoint in separate Vercel project
  web/  # One React frontend on Vercel and in native WebView.
    src/  # Implementation source files within its owning package.
      api/  # FastAPI public HTTP DTOs, authorization and services.
        assets.ts  # assetUrl(); uploadAsset(); Bounded signed asset requests and downloads
        client.ts  # request<T>(); API error normalization; Same-origin cookie/CSRF-aware fetch
        realtime.ts  # subscribeGame(gameId, callback); Private Broadcast + reconnect revision invalidation
        types.ts  # generated OpenAPI types; Generated from normative OpenAPI YAML; not manually edited
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

## Package boundaries

The API imports engine interfaces but the engine cannot import API or I/O modules. Configuration loading maps portable definition records to immutable typed engine structures. The frontend calls only the API and authorized asset/Realtime services; native is a constrained wrapper. Prisma never owns the Supabase-managed `auth.users` table. Database-changing code is transactional and backend-only. Scripts under `.github/scripts/` are repository/documentation tooling, not alternate application runtimes.

## Single-source contract dependencies

The requirements start at [PRD](../../PRD.md). HTTP payloads are specified by [openapi.yaml](../../../packages/server/api/openapi.yaml), database tables and constraints by [schema.prisma](../../../packages/server/supabase/schema.prisma) and [integrity.sql](../../../packages/server/supabase/integrity.sql), source file interfaces by [AST.mmd](AST.mmd), and built-in game data by the files under `data/`. These files refer to one another rather than embedding duplicate authoritative copies. A CI verifier checks their identities, type references, documented responsibilities, and graph connectivity.
