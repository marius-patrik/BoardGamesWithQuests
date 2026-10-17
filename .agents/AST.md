# BoardGamesWithQuests — AST


One diagram declares one node per tracked source file with the interface/documentation requirements and declared dependency graph. It is a file/declaration contract; method bodies are constrained by DATA operator semantics and observable acceptance requirements, not inferred from arrow labels.

```mermaid
flowchart TB
  %% Each box maps to exactly one tracked source file.
  %% HTML label line 1: file; line 2: exported declarations; line 3: source documentation contract.
  subgraph META["META — tracked source"]
    F149[".agents/AST.md<br/>exports: Single Mermaid file/declaration/action AST diagram<br/>Markdown: Normative source-declaration dependency and configuration expression graph."]
    F150[".agents/SCHEMA.md<br/>exports: Drizzle table schema and PostgreSQL security/Realtime routines<br/>Markdown: Normative documented Drizzle schema and PostgreSQL-specific DDL."]
    F001[".agents/PRD.md<br/>exports: architecture: INVARIANTS, COMPONENTS, API, DATA; links SCHEMA and AST<br/>Markdown: Normative product contract linking standalone SCHEMA and AST specifications."]
    F002[".editorconfig<br/>exports: indent / whitespace<br/>File contract: Consistent editor indentation."]
    F003[".env.example<br/>exports: variable names only<br/>File contract: Document public and server-only environment names."]
    F004[".github/workflows/deploy-api.yml<br/>exports: deploy-api workflow<br/>Workflow comments: Deploy FastAPI Vercel project"]
    F005[".github/workflows/deploy-web.yml<br/>exports: deploy-web workflow<br/>Workflow comments: Deploy web Vercel project"]
    F006[".github/workflows/release-native.yml<br/>exports: release-native workflow<br/>Workflow comments: Build and sign native artifacts"]
    F007[".github/workflows/verify.yml<br/>exports: verify workflow<br/>Workflow comments: Check AST/schema/API/data/tests and code docs"]
    F008[".gitignore<br/>exports: build outputs<br/>File contract: Exclude generated caches and binaries."]
    F009["LICENSE<br/>exports: license text<br/>File contract: Product distribution terms."]
    F010["README.md<br/>exports: symlink -&gt; .agents/PRD.md<br/>Markdown: Entry to source of truth."]
    F011["bun.lock<br/>exports: Bun lockfile<br/>File contract: Locked dependency graph."]
    F012["package.json<br/>exports: bun workspaces<br/>Schema/document metadata: Root workspace and verify tasks."]
    F130["tools/build_docs.py<br/>exports: render_source_docs()<br/>Python docstring: Generate Python, TSDoc and Rustdoc source/API documentation."]
    F131["tools/check_spec.py<br/>exports: verify_document(); verify_builtin_shape(); verify_api(); verify_ast(); operator_inventory(); main()<br/>Python docstring: Validate typed seed references, four concrete fixtures, JSON/OpenAPI equivalence, AST and operator inventory."]
    F132["tools/migrate_schema.py<br/>exports: emit() -&gt; list[Path]<br/>Python docstring: Convert reviewed Drizzle SQL to Supabase versioned migrations without executing them."]
    F133["tsconfig.json<br/>exports: TS project base<br/>Schema/document metadata: Strict TS and module-resolution defaults."]
    F134["tsdoc.json<br/>exports: TSDoc grammar<br/>Schema/document metadata: Single standard for structured TSDoc tags."]
    F135["typedoc.json<br/>exports: TypeDoc configuration<br/>Schema/document metadata: Generate docs from structured TSDoc declarations."]
    F136["tools/generate_ast.py<br/>exports: compile_mermaid() -&gt; str; main() -&gt; None<br/>Python docstring: Build single Mermaid source and configuration AST"]
    F137["tools/check_semantics.py<br/>exports: check() -&gt; list[str]<br/>Python docstring: Validate cross-configuration hooks, fields and AST synchronization"]
    F138["tools/build_operator_contract.py<br/>exports: operator_contract.json compiler<br/>Python docstring: Emit normative operator contracts from used typed calls"]
    F139["packages/server/configuration/operator_contract.json<br/>exports: 101 generic operator names with observed argument signatures and deterministic semantic descriptions<br/>Machine contract: Required pure/effect signatures and semantics; implementations must conform and be behaviorally tested."]
    F140["packages/server/engine/reachability.py<br/>exports: exists_reachable(start,successors,target,canonical_key,max_states)-&gt;bool; no_reachable_terminal(...)-&gt;bool; ReachabilityLimit<br/>Python docstring: Exact generic finite-state model checking; resource exhaustion never establishes a draw."]
    F141["tests/engine/test_reachability.py<br/>exports: test_reachable_even_with_cycles(); test_unreachable_only_when_exhausted(); test_budget_does_not_produce_false_proof(); test_terminal_start_and_invalid_budget()<br/>Python docstring: Check proof soundness, cycles and budget exceptions against observable graph behavior."]
    F144["tools/sync_api_schema.py<br/>exports: sync_config_schema()<br/>Python docstring: Embed canonical portable JSON Schema in OpenAPI without drift."]
    F145["tests/engine/test_game_contracts.py<br/>exports: test_dice_moves_only_the_active_players_token(); test_pawn_promotion_occurs_before_advancing_turn(); test_economic_actions_do_not_embed_a_game_named_operator(); test_chess_dead_position_uses_sound_generic_reachability(); test_moneyproperty_doubles_detention_and_release_use_actions(); test_game_definition_is_built_from_entities_actions_and_objectives(); test_card_resolution_is_scoped_to_the_single_drawn_card(); test_chess_moves_cannot_capture_the_opposing_king()<br/>Python docstring: Exercise observed per-player action eligibility and atomic promotion ordering."]
    F146["tools/build_prd.py<br/>exports: build()-&gt;str; replace_first(text,language,content)-&gt;str<br/>Python docstring: Regenerate linked PRD with canonical API, DATA, and source-tree listings; never embed schema or AST."]
    F147["tools/register_manifest.py<br/>exports: register_manifest()-&gt;None<br/>Python docstring: Synchronize one source-file node per contract and exact tracked source tree."]
    F148["tools/check_prd.py<br/>exports: verify()-&gt;None<br/>Python docstring: Verify linked SCHEMA and AST exist, source-tree and graph align, and inline API and DATA are fresh."]
  end
  subgraph DATABASE["DATABASE — tracked source"]
    F013["packages/database/drizzle.config.ts<br/>exports: defineConfig({dialect:postgresql,schema})<br/>TSDoc: Generate reviewed migrations; auth schema filtered."]
    F014["packages/database/package.json<br/>exports: drizzle-kit toolchain<br/>Schema/document metadata: Schema generation isolated from Python production runtime."]
    F015["packages/database/src/schema.ts<br/>exports: pgSchema(bgwq): tables, enum, indexes, FK, checks<br/>TSDoc: Sole authored relational table/type declaration; all runtime authority database-side."]
  end
  subgraph NATIVE["NATIVE — tracked source"]
    F016["packages/native/package.json<br/>exports: Tauri build scripts<br/>Schema/document metadata: Platform build toolchain."]
    F017["packages/native/src-tauri/Cargo.lock<br/>exports: Cargo dependency lock<br/>File contract: Reproducible native build."]
    F018["packages/native/src-tauri/Cargo.toml<br/>exports: crate manifest<br/>File contract: Restricted host dependencies."]
    F019["packages/native/src-tauri/build.rs<br/>exports: tauri_build::build()<br/>Rustdoc: Tauri native resource setup."]
    F020["packages/native/src-tauri/capabilities/default.json<br/>exports: least-privilege capabilities<br/>Schema/document metadata: Navigation capabilities restricted to production origin."]
    F021["packages/native/src-tauri/icons/icon.icns<br/>exports: icon asset<br/>File contract: App icon in platform-required format."]
    F022["packages/native/src-tauri/icons/icon.ico<br/>exports: icon asset<br/>File contract: App icon in platform-required format."]
    F023["packages/native/src-tauri/icons/icon.png<br/>exports: icon asset<br/>File contract: App icon in platform-required format."]
    F024["packages/native/src-tauri/src/main.rs<br/>exports: main() -&gt; run()<br/>Rustdoc: Minimal native WebView lifecycle."]
    F025["packages/native/src-tauri/tauri.conf.json<br/>exports: production remote URL, ids, permissions<br/>Schema/document metadata: One remotely loaded frontend across targets."]
  end
  subgraph API["API — tracked source"]
    F026["packages/server/api/__init__.py<br/>exports: module<br/>Python docstring: Python package marker."]
    F027["packages/server/api/app.py<br/>exports: create_app()-&gt;FastAPI<br/>Python docstring: Construct middleware, session, routes, error handlers."]
    F028["packages/server/api/assets.py<br/>exports: begin_upload(); finish_upload(); signed_url(); cleanup()<br/>Python docstring: Supabase Storage signed upload, digest validation, publication immutability."]
    F029["packages/server/api/contracts.py<br/>exports: Pydantic Models: Session, Game, Definition, Command, Event<br/>Python docstring: HTTP DTOs conform exactly to OpenAPI."]
    F030["packages/server/api/index.py<br/>exports: app: FastAPI<br/>Python docstring: Serverless ASGI entrypoint."]
    F031["packages/server/api/openapi.yaml<br/>exports: OpenAPI 3.1 contract<br/>Workflow comments: Normative HTTP operations and request/response schemas."]
    F032["packages/server/api/realtime.py<br/>exports: private_channel_grant(); authorize_subscription()<br/>Python docstring: Supabase private Broadcast access for game members."]
    F033["packages/server/api/repository.py<br/>exports: Repository.load/save/project + UOW<br/>Python docstring: Psycopg relational hydration and atomic writes."]
    F034["packages/server/api/routes.py<br/>exports: mount_routes(app); 33 operation IDs<br/>Python docstring: Register all documented identity, definition, asset, and game endpoints."]
    F035["packages/server/api/security.py<br/>exports: principal(); verify_csrf(); require_membership()<br/>Python docstring: Supabase Auth session, Origin/CSRF, role and hidden-state authorization."]
    F036["packages/server/api/services.py<br/>exports: create_game(); join_game(); submit_action(); publish_definition()<br/>Python docstring: Transaction-aware API orchestration; no game rules."]
  end
  subgraph CONFIG["CONFIG — tracked source"]
    F037["packages/server/configuration/__init__.py<br/>exports: module<br/>Python docstring: Portable configuration package."]
    F038["packages/server/configuration/bootstrap.py<br/>exports: import_builtins(repository)<br/>Python docstring: Load four portable game definitions into published versions."]
    F039["packages/server/configuration/configuration.schema.json<br/>exports: JSON Schema draft2020-12<br/>Schema/document metadata: Complete typed portable configuration grammar."]
    F040["packages/server/configuration/models.py<br/>exports: PortableConfig Pydantic + local references<br/>Python docstring: Validate portable fields and structurally defined record types."]
    F041["packages/server/configuration/transfer.py<br/>exports: import_json(); export_json(); canonicalize()<br/>Python docstring: Deterministic relational import/export and asset bundling."]
    F042["packages/server/configuration/validation.py<br/>exports: validate_references(); validate_types(); publish()<br/>Python docstring: Validate cycles, budgets, signed assets, hook/effect signatures."]
  end
  subgraph SERVERDATA["SERVERDATA — tracked source"]
    F043["packages/server/data/chess.json<br/>exports: PortableGameDefinition v1<br/>Schema/document metadata: Complete seeded layout, declared actions, generic expressions and visual primitives."]
    F044["packages/server/data/english-draughts.json<br/>exports: PortableGameDefinition v1<br/>Schema/document metadata: Complete seeded layout, declared actions, generic expressions and visual primitives."]
    F045["packages/server/data/international-draughts.json<br/>exports: PortableGameDefinition v1<br/>Schema/document metadata: Complete seeded layout, declared actions, generic expressions and visual primitives."]
    F046["packages/server/data/moneyproperty.json<br/>exports: PortableGameDefinition v1<br/>Schema/document metadata: Complete seeded layout, declared actions, generic expressions and visual primitives."]
    F058["packages/server/pyproject.toml<br/>exports: Python dependencies and pytest<br/>File contract: FastAPI psycopg Pydantic and validation dependencies."]
    F059["packages/server/supabase/config.toml<br/>exports: Supabase local/auth/storage config<br/>File contract: Local Supabase services and migrations."]
    F060["packages/server/supabase/security.sql<br/>exports: RLS, grants, functions, triggers, Broadcast<br/>SQL documentation: SQL exception: engine-independent PostgreSQL routines Drizzle cannot model."]
    F061["packages/server/supabase/seed.sql<br/>exports: Operator registry, hooks, buckets DML<br/>SQL documentation: Reference data is data, not schema; deployed after migration."]
    F062["packages/server/vercel.json<br/>exports: ASGI route and limits<br/>Schema/document metadata: Deploy Python entrypoint in separate Vercel project."]
  end
  subgraph ENGINE["ENGINE — tracked source"]
    F047["packages/server/engine/__init__.py<br/>exports: module<br/>Python docstring: Generic engine package."]
    F048["packages/server/engine/effects.py<br/>exports: propose(effect,state,ctx)-&gt;Mutation[]<br/>Python docstring: Controlled generic effect executor; never writes database."]
    F049["packages/server/engine/events.py<br/>exports: encode_mutations(); replay(); digest()<br/>Python docstring: Reconstruct complete entity/link/value/turn changes from typed event rows."]
    F050["packages/server/engine/expressions.py<br/>exports: evaluate(expr,ctx); validate_dag(expr)<br/>Python docstring: Pure typed expression evaluator; no IO, deterministic budget."]
    F051["packages/server/engine/hooks.py<br/>exports: dispatch(hook,ctx)-&gt;ActionResult[]<br/>Python docstring: Stratified hook scheduler, ordering, event queue and budgets."]
    F052["packages/server/engine/model.py<br/>exports: EntityType,Entity,ActionDef,GameState,Transition,Mutation<br/>Python docstring: Frozen typed pure engine data models."]
    F053["packages/server/engine/operators.py<br/>exports: registry(); evaluate_op(); signature()<br/>Python docstring: Finite generic pure operator catalog; no game-name branches."]
    F054["packages/server/engine/randomness.py<br/>exports: consume(trusted_stream,range)-&gt;RandomSample<br/>Python docstring: Deterministic consumption of injected entropy; replay uses recorded values."]
    F055["packages/server/engine/runtime.py<br/>exports: initialize(); available_actions(); evaluate(); status()<br/>Python docstring: The single authority for action semantics; immutable state transitions."]
    F056["packages/server/engine/topology.py<br/>exports: neighbors(); ray(); paths(); track_advance()<br/>Python docstring: General topology and bounded traversal primitives."]
    F057["packages/server/engine/types.py<br/>exports: parse_type(); check_type(); TypedValue<br/>Python docstring: Generic scalar, reference, optional, list, set, path, record typing."]
  end
  subgraph WEB["WEB — tracked source"]
    F063["packages/web/components.json<br/>exports: shadcn registry configuration<br/>Schema/document metadata: UI composition and token aliases."]
    F064["packages/web/index.html<br/>exports: root viewport<br/>File contract: Application HTML shell."]
    F065["packages/web/package.json<br/>exports: React + Wouter + Motion + shadcn + OpenAPI client<br/>Schema/document metadata: Locked frontend and tooling dependencies."]
    F066["packages/web/rsbuild.config.ts<br/>exports: defineConfig()<br/>TSDoc: Rsbuild bundling, alias, compile options."]
    F067["packages/web/src/App.tsx<br/>exports: App():ReactElement<br/>TSDoc: Auth/Query providers and Wouter Router."]
    F068["packages/web/src/api/assets.ts<br/>exports: assetUrl(); uploadAsset()<br/>TSDoc: Bounded signed asset requests and downloads."]
    F069["packages/web/src/api/client.ts<br/>exports: request&lt;T&gt;(); API error normalization<br/>TSDoc: Same-origin cookie/CSRF-aware fetch."]
    F070["packages/web/src/api/realtime.ts<br/>exports: subscribeGame(gameId, callback)<br/>TSDoc: Private Broadcast + reconnect revision invalidation."]
    F071["packages/web/src/api/types.ts<br/>exports: generated OpenAPI types<br/>TSDoc: Generated from normative OpenAPI YAML; not manually edited."]
    F072["packages/web/src/app/pages.tsx<br/>exports: HomePage,AuthPage,AccountPage,DefinitionsPage,GamePage<br/>TSDoc: All routed screens (not game-specific boards)."]
    F073["packages/web/src/app/query.ts<br/>exports: QueryClient;invalidateOnRevision()<br/>TSDoc: HTTP cache, retry and version synchronization."]
    F074["packages/web/src/app/router.tsx<br/>exports: AppRoutes():ReactElement<br/>TSDoc: Wouter Switch/Route navigation and guard."]
    F075["packages/web/src/app/session.tsx<br/>exports: SessionProvider();useSession()<br/>TSDoc: Cookie session and CSRF state."]
    F076["packages/web/src/editor/ActionEditor.tsx<br/>exports: ActionEditor()<br/>TSDoc: Manual/hook actions, conditions, parameter and effect lists."]
    F077["packages/web/src/editor/AssetEditor.tsx<br/>exports: AssetEditor()<br/>TSDoc: Private binary upload and presentation assets."]
    F078["packages/web/src/editor/DefinitionEditor.tsx<br/>exports: DefinitionEditor()<br/>TSDoc: Top-level unified configuration editor."]
    F079["packages/web/src/editor/EntityEditor.tsx<br/>exports: EntityEditor()<br/>TSDoc: Types, seeds, field values and relationships."]
    F080["packages/web/src/editor/ExpressionEditor.tsx<br/>exports: ExpressionEditor()<br/>TSDoc: Typed operator DAG builder with validation."]
    F081["packages/web/src/editor/RolePhaseEditor.tsx<br/>exports: RolePhaseEditor()<br/>TSDoc: Participant roles, phases and eligible command forms."]
    F082["packages/web/src/editor/SpaceEditor.tsx<br/>exports: SpaceEditor()<br/>TSDoc: Visual grid/graph/track and entity placement editor."]
    F083["packages/web/src/editor/TransferEditor.tsx<br/>exports: TransferEditor()<br/>TSDoc: Canonical portable JSON import/export."]
    F084["packages/web/src/editor/VisualEditor.tsx<br/>exports: VisualEditor()<br/>TSDoc: SVG template construction and asset binding."]
    F085["packages/web/src/editor/useDraft.ts<br/>exports: useDraft(); publish(); validate()<br/>TSDoc: Autosave/publish conflict handling and draft revisions."]
    F086["packages/web/src/games/ActionPanel.tsx<br/>exports: ActionPanel();ParameterInput()<br/>TSDoc: Typed, dynamically generated action controls."]
    F087["packages/web/src/games/Clocks.tsx<br/>exports: Clocks()<br/>TSDoc: Nonauthoritative clock projection."]
    F088["packages/web/src/games/Decisions.tsx<br/>exports: DecisionControls()<br/>TSDoc: Generic multi-party decision/auction/trade controls."]
    F089["packages/web/src/games/GameView.tsx<br/>exports: GameView({gameId}):ReactElement<br/>TSDoc: Compose generic scene, actions, history, status and participants."]
    F090["packages/web/src/games/History.tsx<br/>exports: History({events})<br/>TSDoc: Generic revision and accepted-event timeline."]
    F091["packages/web/src/games/Invite.tsx<br/>exports: Invite()<br/>TSDoc: Invite URL, join state, pending expiration."]
    F092["packages/web/src/games/ObjectivePanel.tsx<br/>exports: ObjectivePanel()<br/>TSDoc: Generic objective state/progress including optional quests."]
    F093["packages/web/src/games/Participants.tsx<br/>exports: ParticipantPanel()<br/>TSDoc: Arbitrary participant counts, roles and eliminated state."]
    F094["packages/web/src/games/useGame.ts<br/>exports: useGame(); useAvailableActions(); useSubmitAction()<br/>TSDoc: Authoritative game queries, revisions, idempotent command sends."]
    F095["packages/web/src/main.tsx<br/>exports: createRoot().render(&lt;App/&gt;)<br/>TSDoc: Browser root mounting."]
    F096["packages/web/src/rendering/Accessibility.ts<br/>exports: getEntityAria(); focusNavigation()<br/>TSDoc: Keyboard and screenreader metadata derived from scene."]
    F097["packages/web/src/rendering/Animation.tsx<br/>exports: AnimatedEntity(); useMotionProjection()<br/>TSDoc: Motion projections on authoritative state changes."]
    F098["packages/web/src/rendering/Interactions.tsx<br/>exports: InteractionLayer(); usePointerActions()<br/>TSDoc: Pointer/touch/keyboard access and action-source selection."]
    F099["packages/web/src/rendering/Layout.ts<br/>exports: resolveLayouts(); projectLocations()<br/>TSDoc: Grid, node graph, track and free placement transforms."]
    F100["packages/web/src/rendering/Primitive.tsx<br/>exports: Primitive({definition}):ReactElement<br/>TSDoc: Allowlisted safe SVG primitives; no arbitrary markup."]
    F101["packages/web/src/rendering/Scene.tsx<br/>exports: Scene({entities,scene}):ReactElement<br/>TSDoc: One dynamic SVG scene for all four game types."]
    F102["packages/web/src/styles.css<br/>exports: Tailwind base + design tokens<br/>File contract: Themes, typography and focus styles."]
    F103["packages/web/src/ui/button.tsx<br/>exports: Button(props)<br/>TSDoc: Clickable semantic button"]
    F104["packages/web/src/ui/card.tsx<br/>exports: Card(props)<br/>TSDoc: Visual panel"]
    F105["packages/web/src/ui/dialog.tsx<br/>exports: Dialog(props)<br/>TSDoc: Accessible modal"]
    F106["packages/web/src/ui/input.tsx<br/>exports: Input(props)<br/>TSDoc: Accessible text input"]
    F107["packages/web/src/ui/select.tsx<br/>exports: Select(props)<br/>TSDoc: Typed selection control"]
    F108["packages/web/src/ui/tabs.tsx<br/>exports: Tabs(props)<br/>TSDoc: Accessible tab list"]
    F109["packages/web/src/ui/toast.tsx<br/>exports: Toast(props)<br/>TSDoc: Status and error announcement"]
    F110["packages/web/src/ui/tooltip.tsx<br/>exports: Tooltip(props)<br/>TSDoc: Contextual help"]
    F111["packages/web/tsconfig.json<br/>exports: compilerOptions strict<br/>Schema/document metadata: Web TS project constraints."]
    F112["packages/web/vercel.json<br/>exports: SPA rewrites + API proxy<br/>Schema/document metadata: Forward /api/* to separate Vercel deployment."]
  end
  subgraph TESTS["TESTS — tracked source"]
    F113["tests/api/test_contract.py<br/>exports: test/assertions<br/>Python docstring: OpenAPI and security errors"]
    F114["tests/api/test_realtime.py<br/>exports: test/assertions<br/>Python docstring: Private revision authorization"]
    F115["tests/browser/editor.spec.ts<br/>exports: test/assertions<br/>TSDoc: Structured authoring and import/export"]
    F116["tests/browser/games.spec.ts<br/>exports: test/assertions<br/>TSDoc: Four full game scenarios"]
    F117["tests/browser/package.json<br/>exports: configuration<br/>Schema/document metadata: Browser test runner dependencies"]
    F118["tests/browser/playwright.config.ts<br/>exports: configuration<br/>TSDoc: Cross-browser test configuration"]
    F119["tests/browser/rendering.spec.ts<br/>exports: test/assertions<br/>TSDoc: SVG, accessibility and layout"]
    F120["tests/configuration/test_assets.py<br/>exports: test/assertions<br/>Python docstring: Binary import/export digest parity"]
    F121["tests/configuration/test_roundtrip.py<br/>exports: test/assertions<br/>Python docstring: Structural and semantic JSON roundtrip"]
    F122["tests/database/test_integrity.py<br/>exports: test/assertions<br/>Python docstring: Published immutability, trigger and RLS checks"]
    F123["tests/database/test_schema.py<br/>exports: test/assertions<br/>Python docstring: Migrations/FKs/constraints in real PostgreSQL"]
    F124["tests/database/test_transactions.py<br/>exports: test/assertions<br/>Python docstring: Concurrent actions and exact idempotency"]
    F125["tests/engine/test_chess.py<br/>exports: test/assertions<br/>Python docstring: FIDE legal and forbidden actions"]
    F126["tests/engine/test_draughts.py<br/>exports: test/assertions<br/>Python docstring: Capture/path and promotion edge cases"]
    F127["tests/engine/test_execution.py<br/>exports: test/assertions<br/>Python docstring: Pure operator semantics"]
    F128["tests/engine/test_moneyproperty.py<br/>exports: test/assertions<br/>Python docstring: Economic decision and multi-party transactions"]
    F129["tests/native/smoke.spec.ts<br/>exports: test/assertions<br/>TSDoc: Remote WebView and navigation restrictions"]
  end
  F027 -->|uses| F034
  F027 -->|uses| F035
  F029 -->|uses| F031
  F030 -->|uses| F027
  F033 -->|uses| F015
  F034 -->|uses| F036
  F034 -->|uses| F029
  F036 -->|uses| F033
  F036 -->|uses| F055
  F038 -->|uses| F041
  F040 -->|uses| F039
  F041 -->|uses| F033
  F041 -->|uses| F040
  F042 -->|uses| F057
  F042 -->|uses| F053
  F043 -->|uses| F039
  F044 -->|uses| F039
  F045 -->|uses| F039
  F046 -->|uses| F039
  F055 -->|uses| F051
  F055 -->|uses| F050
  F055 -->|uses| F048
  F055 -->|uses| F052
  F067 -->|uses| F074
  F067 -->|uses| F075
  F071 -->|uses| F031
  F072 -->|uses| F089
  F072 -->|uses| F078
  F074 -->|uses| F072
  F089 -->|uses| F101
  F089 -->|uses| F086
  F094 -->|uses| F069
  F095 -->|uses| F067
  F101 -->|uses| F100
  F101 -->|uses| F099
  F132 -->|uses| F015
  F001 -.-> F149
  F001 -.-> F150
  %% BEGIN GENERATED ENTITY-ACTION EXPRESSION AST
  subgraph ACTION_AST["CONFIGURATION ACTION AST — full expression and effect structure"]
    A000001["chess: rook.move | command | phase:turn"]
    F043 -.-> A000001
    X000002["and"]
    A000001 -->|"condition"| X000002
    X000003["eq"]
    X000002 -->|"values[0]"| X000003
    X000004["owner"]
    X000003 -->|"a"| X000004
    X000005["context | self"]
    X000004 -->|"entity"| X000005
    X000006["context | actor"]
    X000003 -->|"b"| X000006
    X000007["phase_is"]
    X000002 -->|"values[1]"| X000007
    X000008["literal | turn"]
    X000007 -->|"phase"| X000008
    X000009["is_active"]
    X000002 -->|"values[2]"| X000009
    X000010["context | actor"]
    X000009 -->|"participant"| X000010
    X000011["contains"]
    X000002 -->|"values[3]"| X000011
    X000012["reachable_grid_nodes"]
    X000011 -->|"items"| X000012
    X000013["context | self"]
    X000012 -->|"entity"| X000013
    X000014["list"]
    X000012 -->|"directions"| X000014
    X000015["vector"]
    X000014 -->|"values[0]"| X000015
    X000016["literal | 1"]
    X000015 -->|"row"| X000016
    X000017["literal | 0"]
    X000015 -->|"column"| X000017
    X000018["vector"]
    X000014 -->|"values[1]"| X000018
    X000019["literal | -1"]
    X000018 -->|"row"| X000019
    X000020["literal | 0"]
    X000018 -->|"column"| X000020
    X000021["vector"]
    X000014 -->|"values[2]"| X000021
    X000022["literal | 0"]
    X000021 -->|"row"| X000022
    X000023["literal | 1"]
    X000021 -->|"column"| X000023
    X000024["vector"]
    X000014 -->|"values[3]"| X000024
    X000025["literal | 0"]
    X000024 -->|"row"| X000025
    X000026["literal | -1"]
    X000024 -->|"column"| X000026
    X000027["literal | 7"]
    X000012 -->|"max_steps"| X000027
    X000028["literal | False"]
    X000012 -->|"leap"| X000028
    X000029["literal | 1"]
    X000012 -->|"orientation"| X000029
    X000030["literal | empty_or_opponent"]
    X000012 -->|"target_occupancy"| X000030
    X000031["context | observed_state"]
    X000012 -->|"state"| X000031
    X000032["context | argument.to"]
    X000011 -->|"value"| X000032
    X000033["none_match"]
    X000002 -->|"values[4]"| X000033
    X000034["entities_at"]
    X000033 -->|"items"| X000034
    X000035["context | argument.to"]
    X000034 -->|"node"| X000035
    X000036["literal | other"]
    X000033 -->|"variable"| X000036
    X000037["eq"]
    X000033 -->|"predicate"| X000037
    X000038["owner"]
    X000037 -->|"a"| X000038
    X000039["context | local.other"]
    X000038 -->|"entity"| X000039
    X000040["owner"]
    X000037 -->|"b"| X000040
    X000041["context | self"]
    X000040 -->|"entity"| X000041
    X000042["none_match"]
    X000002 -->|"values[5]"| X000042
    X000043["entities_matching"]
    X000042 -->|"items"| X000043
    X000044["literal | king"]
    X000043 -->|"entity_type"| X000044
    X000045["context | actor"]
    X000043 -->|"owner"| X000045
    X000046["preview"]
    X000043 -->|"state"| X000046
    X000047["context | observed_state"]
    X000046 -->|"state"| X000047
    X000048["list"]
    X000046 -->|"effects"| X000048
    X000049["effect_value"]
    X000048 -->|"values[0]"| X000049
    X000050["literal | move_entity"]
    X000049 -->|"name"| X000050
    X000051["context | self"]
    X000049 -->|"entity"| X000051
    X000052["context | argument.to"]
    X000049 -->|"destination"| X000052
    X000053["literal | protected"]
    X000042 -->|"variable"| X000053
    X000054["threatened"]
    X000042 -->|"predicate"| X000054
    X000055["context | local.protected"]
    X000054 -->|"entity"| X000055
    X000056["preview"]
    X000054 -->|"state"| X000056
    X000057["context | observed_state"]
    X000056 -->|"state"| X000057
    X000058["list"]
    X000056 -->|"effects"| X000058
    X000059["effect_value"]
    X000058 -->|"values[0]"| X000059
    X000060["literal | move_entity"]
    X000059 -->|"name"| X000060
    X000061["context | self"]
    X000059 -->|"entity"| X000061
    X000062["context | argument.to"]
    X000059 -->|"destination"| X000062
    X000063["none_match"]
    X000002 -->|"values[6]"| X000063
    X000064["entities_at"]
    X000063 -->|"items"| X000064
    X000065["context | argument.to"]
    X000064 -->|"node"| X000065
    X000066["literal | occupant"]
    X000063 -->|"variable"| X000066
    X000067["contains"]
    X000063 -->|"predicate"| X000067
    X000068["entities_of_type"]
    X000067 -->|"items"| X000068
    X000069["literal | king"]
    X000068 -->|"entity_type"| X000069
    X000070["context | local.occupant"]
    X000067 -->|"value"| X000070
    E000071["effect[0]: remove_matching_entities"]
    A000001 --> E000071
    X000072["context | argument.to"]
    E000071 -->|"node"| X000072
    X000073["context | actor"]
    E000071 -->|"exclude_owner"| X000073
    E000074["effect[1]: move_entity"]
    A000001 --> E000074
    X000075["context | self"]
    E000074 -->|"entity"| X000075
    X000076["context | argument.to"]
    E000074 -->|"destination"| X000076
    E000077["effect[2]: emit_event"]
    A000001 --> E000077
    X000078["literal | piece.moved"]
    E000077 -->|"name"| X000078
    E000079["effect[3]: set_field"]
    A000001 --> E000079
    X000080["context | self"]
    E000079 -->|"entity"| X000080
    X000081["literal | moved"]
    E000079 -->|"field"| X000081
    X000082["literal | True"]
    E000079 -->|"value"| X000082
    E000083["effect[4]: advance_turn"]
    A000001 --> E000083
    A000084["chess: rook.generate | hook | phase:turn | hook:action.generate"]
    F043 -.-> A000084
    X000085["eq"]
    A000084 -->|"condition"| X000085
    X000086["owner"]
    X000085 -->|"a"| X000086
    X000087["context | self"]
    X000086 -->|"entity"| X000087
    X000088["context | actor"]
    X000085 -->|"b"| X000088
    X000089["reachable_grid_nodes"]
    A000084 -->|"iterator"| X000089
    X000090["context | self"]
    X000089 -->|"entity"| X000090
    X000091["list"]
    X000089 -->|"directions"| X000091
    X000092["vector"]
    X000091 -->|"values[0]"| X000092
    X000093["literal | 1"]
    X000092 -->|"row"| X000093
    X000094["literal | 0"]
    X000092 -->|"column"| X000094
    X000095["vector"]
    X000091 -->|"values[1]"| X000095
    X000096["literal | -1"]
    X000095 -->|"row"| X000096
    X000097["literal | 0"]
    X000095 -->|"column"| X000097
    X000098["vector"]
    X000091 -->|"values[2]"| X000098
    X000099["literal | 0"]
    X000098 -->|"row"| X000099
    X000100["literal | 1"]
    X000098 -->|"column"| X000100
    X000101["vector"]
    X000091 -->|"values[3]"| X000101
    X000102["literal | 0"]
    X000101 -->|"row"| X000102
    X000103["literal | -1"]
    X000101 -->|"column"| X000103
    X000104["literal | 7"]
    X000089 -->|"max_steps"| X000104
    X000105["literal | False"]
    X000089 -->|"leap"| X000105
    X000106["literal | 1"]
    X000089 -->|"orientation"| X000106
    X000107["literal | empty_or_opponent"]
    X000089 -->|"target_occupancy"| X000107
    X000108["context | observed_state"]
    X000089 -->|"state"| X000108
    E000109["effect[0]: emit_candidate"]
    A000084 --> E000109
    X000110["context | self"]
    E000109 -->|"source"| X000110
    X000111["context | candidate"]
    E000109 -->|"destination"| X000111
    A000112["chess: bishop.move | command | phase:turn"]
    F043 -.-> A000112
    X000113["and"]
    A000112 -->|"condition"| X000113
    X000114["eq"]
    X000113 -->|"values[0]"| X000114
    X000115["owner"]
    X000114 -->|"a"| X000115
    X000116["context | self"]
    X000115 -->|"entity"| X000116
    X000117["context | actor"]
    X000114 -->|"b"| X000117
    X000118["phase_is"]
    X000113 -->|"values[1]"| X000118
    X000119["literal | turn"]
    X000118 -->|"phase"| X000119
    X000120["is_active"]
    X000113 -->|"values[2]"| X000120
    X000121["context | actor"]
    X000120 -->|"participant"| X000121
    X000122["contains"]
    X000113 -->|"values[3]"| X000122
    X000123["reachable_grid_nodes"]
    X000122 -->|"items"| X000123
    X000124["context | self"]
    X000123 -->|"entity"| X000124
    X000125["list"]
    X000123 -->|"directions"| X000125
    X000126["vector"]
    X000125 -->|"values[0]"| X000126
    X000127["literal | 1"]
    X000126 -->|"row"| X000127
    X000128["literal | 1"]
    X000126 -->|"column"| X000128
    X000129["vector"]
    X000125 -->|"values[1]"| X000129
    X000130["literal | 1"]
    X000129 -->|"row"| X000130
    X000131["literal | -1"]
    X000129 -->|"column"| X000131
    X000132["vector"]
    X000125 -->|"values[2]"| X000132
    X000133["literal | -1"]
    X000132 -->|"row"| X000133
    X000134["literal | 1"]
    X000132 -->|"column"| X000134
    X000135["vector"]
    X000125 -->|"values[3]"| X000135
    X000136["literal | -1"]
    X000135 -->|"row"| X000136
    X000137["literal | -1"]
    X000135 -->|"column"| X000137
    X000138["literal | 7"]
    X000123 -->|"max_steps"| X000138
    X000139["literal | False"]
    X000123 -->|"leap"| X000139
    X000140["literal | 1"]
    X000123 -->|"orientation"| X000140
    X000141["literal | empty_or_opponent"]
    X000123 -->|"target_occupancy"| X000141
    X000142["context | observed_state"]
    X000123 -->|"state"| X000142
    X000143["context | argument.to"]
    X000122 -->|"value"| X000143
    X000144["none_match"]
    X000113 -->|"values[4]"| X000144
    X000145["entities_at"]
    X000144 -->|"items"| X000145
    X000146["context | argument.to"]
    X000145 -->|"node"| X000146
    X000147["literal | other"]
    X000144 -->|"variable"| X000147
    X000148["eq"]
    X000144 -->|"predicate"| X000148
    X000149["owner"]
    X000148 -->|"a"| X000149
    X000150["context | local.other"]
    X000149 -->|"entity"| X000150
    X000151["owner"]
    X000148 -->|"b"| X000151
    X000152["context | self"]
    X000151 -->|"entity"| X000152
    X000153["none_match"]
    X000113 -->|"values[5]"| X000153
    X000154["entities_matching"]
    X000153 -->|"items"| X000154
    X000155["literal | king"]
    X000154 -->|"entity_type"| X000155
    X000156["context | actor"]
    X000154 -->|"owner"| X000156
    X000157["preview"]
    X000154 -->|"state"| X000157
    X000158["context | observed_state"]
    X000157 -->|"state"| X000158
    X000159["list"]
    X000157 -->|"effects"| X000159
    X000160["effect_value"]
    X000159 -->|"values[0]"| X000160
    X000161["literal | move_entity"]
    X000160 -->|"name"| X000161
    X000162["context | self"]
    X000160 -->|"entity"| X000162
    X000163["context | argument.to"]
    X000160 -->|"destination"| X000163
    X000164["literal | protected"]
    X000153 -->|"variable"| X000164
    X000165["threatened"]
    X000153 -->|"predicate"| X000165
    X000166["context | local.protected"]
    X000165 -->|"entity"| X000166
    X000167["preview"]
    X000165 -->|"state"| X000167
    X000168["context | observed_state"]
    X000167 -->|"state"| X000168
    X000169["list"]
    X000167 -->|"effects"| X000169
    X000170["effect_value"]
    X000169 -->|"values[0]"| X000170
    X000171["literal | move_entity"]
    X000170 -->|"name"| X000171
    X000172["context | self"]
    X000170 -->|"entity"| X000172
    X000173["context | argument.to"]
    X000170 -->|"destination"| X000173
    X000174["none_match"]
    X000113 -->|"values[6]"| X000174
    X000175["entities_at"]
    X000174 -->|"items"| X000175
    X000176["context | argument.to"]
    X000175 -->|"node"| X000176
    X000177["literal | occupant"]
    X000174 -->|"variable"| X000177
    X000178["contains"]
    X000174 -->|"predicate"| X000178
    X000179["entities_of_type"]
    X000178 -->|"items"| X000179
    X000180["literal | king"]
    X000179 -->|"entity_type"| X000180
    X000181["context | local.occupant"]
    X000178 -->|"value"| X000181
    E000182["effect[0]: remove_matching_entities"]
    A000112 --> E000182
    X000183["context | argument.to"]
    E000182 -->|"node"| X000183
    X000184["context | actor"]
    E000182 -->|"exclude_owner"| X000184
    E000185["effect[1]: move_entity"]
    A000112 --> E000185
    X000186["context | self"]
    E000185 -->|"entity"| X000186
    X000187["context | argument.to"]
    E000185 -->|"destination"| X000187
    E000188["effect[2]: emit_event"]
    A000112 --> E000188
    X000189["literal | piece.moved"]
    E000188 -->|"name"| X000189
    E000190["effect[3]: advance_turn"]
    A000112 --> E000190
    A000191["chess: bishop.generate | hook | phase:turn | hook:action.generate"]
    F043 -.-> A000191
    X000192["eq"]
    A000191 -->|"condition"| X000192
    X000193["owner"]
    X000192 -->|"a"| X000193
    X000194["context | self"]
    X000193 -->|"entity"| X000194
    X000195["context | actor"]
    X000192 -->|"b"| X000195
    X000196["reachable_grid_nodes"]
    A000191 -->|"iterator"| X000196
    X000197["context | self"]
    X000196 -->|"entity"| X000197
    X000198["list"]
    X000196 -->|"directions"| X000198
    X000199["vector"]
    X000198 -->|"values[0]"| X000199
    X000200["literal | 1"]
    X000199 -->|"row"| X000200
    X000201["literal | 1"]
    X000199 -->|"column"| X000201
    X000202["vector"]
    X000198 -->|"values[1]"| X000202
    X000203["literal | 1"]
    X000202 -->|"row"| X000203
    X000204["literal | -1"]
    X000202 -->|"column"| X000204
    X000205["vector"]
    X000198 -->|"values[2]"| X000205
    X000206["literal | -1"]
    X000205 -->|"row"| X000206
    X000207["literal | 1"]
    X000205 -->|"column"| X000207
    X000208["vector"]
    X000198 -->|"values[3]"| X000208
    X000209["literal | -1"]
    X000208 -->|"row"| X000209
    X000210["literal | -1"]
    X000208 -->|"column"| X000210
    X000211["literal | 7"]
    X000196 -->|"max_steps"| X000211
    X000212["literal | False"]
    X000196 -->|"leap"| X000212
    X000213["literal | 1"]
    X000196 -->|"orientation"| X000213
    X000214["literal | empty_or_opponent"]
    X000196 -->|"target_occupancy"| X000214
    X000215["context | observed_state"]
    X000196 -->|"state"| X000215
    E000216["effect[0]: emit_candidate"]
    A000191 --> E000216
    X000217["context | self"]
    E000216 -->|"source"| X000217
    X000218["context | candidate"]
    E000216 -->|"destination"| X000218
    A000219["chess: queen.move | command | phase:turn"]
    F043 -.-> A000219
    X000220["and"]
    A000219 -->|"condition"| X000220
    X000221["eq"]
    X000220 -->|"values[0]"| X000221
    X000222["owner"]
    X000221 -->|"a"| X000222
    X000223["context | self"]
    X000222 -->|"entity"| X000223
    X000224["context | actor"]
    X000221 -->|"b"| X000224
    X000225["phase_is"]
    X000220 -->|"values[1]"| X000225
    X000226["literal | turn"]
    X000225 -->|"phase"| X000226
    X000227["is_active"]
    X000220 -->|"values[2]"| X000227
    X000228["context | actor"]
    X000227 -->|"participant"| X000228
    X000229["contains"]
    X000220 -->|"values[3]"| X000229
    X000230["reachable_grid_nodes"]
    X000229 -->|"items"| X000230
    X000231["context | self"]
    X000230 -->|"entity"| X000231
    X000232["list"]
    X000230 -->|"directions"| X000232
    X000233["vector"]
    X000232 -->|"values[0]"| X000233
    X000234["literal | 1"]
    X000233 -->|"row"| X000234
    X000235["literal | 0"]
    X000233 -->|"column"| X000235
    X000236["vector"]
    X000232 -->|"values[1]"| X000236
    X000237["literal | -1"]
    X000236 -->|"row"| X000237
    X000238["literal | 0"]
    X000236 -->|"column"| X000238
    X000239["vector"]
    X000232 -->|"values[2]"| X000239
    X000240["literal | 0"]
    X000239 -->|"row"| X000240
    X000241["literal | 1"]
    X000239 -->|"column"| X000241
    X000242["vector"]
    X000232 -->|"values[3]"| X000242
    X000243["literal | 0"]
    X000242 -->|"row"| X000243
    X000244["literal | -1"]
    X000242 -->|"column"| X000244
    X000245["vector"]
    X000232 -->|"values[4]"| X000245
    X000246["literal | 1"]
    X000245 -->|"row"| X000246
    X000247["literal | 1"]
    X000245 -->|"column"| X000247
    X000248["vector"]
    X000232 -->|"values[5]"| X000248
    X000249["literal | 1"]
    X000248 -->|"row"| X000249
    X000250["literal | -1"]
    X000248 -->|"column"| X000250
    X000251["vector"]
    X000232 -->|"values[6]"| X000251
    X000252["literal | -1"]
    X000251 -->|"row"| X000252
    X000253["literal | 1"]
    X000251 -->|"column"| X000253
    X000254["vector"]
    X000232 -->|"values[7]"| X000254
    X000255["literal | -1"]
    X000254 -->|"row"| X000255
    X000256["literal | -1"]
    X000254 -->|"column"| X000256
    X000257["literal | 7"]
    X000230 -->|"max_steps"| X000257
    X000258["literal | False"]
    X000230 -->|"leap"| X000258
    X000259["literal | 1"]
    X000230 -->|"orientation"| X000259
    X000260["literal | empty_or_opponent"]
    X000230 -->|"target_occupancy"| X000260
    X000261["context | observed_state"]
    X000230 -->|"state"| X000261
    X000262["context | argument.to"]
    X000229 -->|"value"| X000262
    X000263["none_match"]
    X000220 -->|"values[4]"| X000263
    X000264["entities_at"]
    X000263 -->|"items"| X000264
    X000265["context | argument.to"]
    X000264 -->|"node"| X000265
    X000266["literal | other"]
    X000263 -->|"variable"| X000266
    X000267["eq"]
    X000263 -->|"predicate"| X000267
    X000268["owner"]
    X000267 -->|"a"| X000268
    X000269["context | local.other"]
    X000268 -->|"entity"| X000269
    X000270["owner"]
    X000267 -->|"b"| X000270
    X000271["context | self"]
    X000270 -->|"entity"| X000271
    X000272["none_match"]
    X000220 -->|"values[5]"| X000272
    X000273["entities_matching"]
    X000272 -->|"items"| X000273
    X000274["literal | king"]
    X000273 -->|"entity_type"| X000274
    X000275["context | actor"]
    X000273 -->|"owner"| X000275
    X000276["preview"]
    X000273 -->|"state"| X000276
    X000277["context | observed_state"]
    X000276 -->|"state"| X000277
    X000278["list"]
    X000276 -->|"effects"| X000278
    X000279["effect_value"]
    X000278 -->|"values[0]"| X000279
    X000280["literal | move_entity"]
    X000279 -->|"name"| X000280
    X000281["context | self"]
    X000279 -->|"entity"| X000281
    X000282["context | argument.to"]
    X000279 -->|"destination"| X000282
    X000283["literal | protected"]
    X000272 -->|"variable"| X000283
    X000284["threatened"]
    X000272 -->|"predicate"| X000284
    X000285["context | local.protected"]
    X000284 -->|"entity"| X000285
    X000286["preview"]
    X000284 -->|"state"| X000286
    X000287["context | observed_state"]
    X000286 -->|"state"| X000287
    X000288["list"]
    X000286 -->|"effects"| X000288
    X000289["effect_value"]
    X000288 -->|"values[0]"| X000289
    X000290["literal | move_entity"]
    X000289 -->|"name"| X000290
    X000291["context | self"]
    X000289 -->|"entity"| X000291
    X000292["context | argument.to"]
    X000289 -->|"destination"| X000292
    X000293["none_match"]
    X000220 -->|"values[6]"| X000293
    X000294["entities_at"]
    X000293 -->|"items"| X000294
    X000295["context | argument.to"]
    X000294 -->|"node"| X000295
    X000296["literal | occupant"]
    X000293 -->|"variable"| X000296
    X000297["contains"]
    X000293 -->|"predicate"| X000297
    X000298["entities_of_type"]
    X000297 -->|"items"| X000298
    X000299["literal | king"]
    X000298 -->|"entity_type"| X000299
    X000300["context | local.occupant"]
    X000297 -->|"value"| X000300
    E000301["effect[0]: remove_matching_entities"]
    A000219 --> E000301
    X000302["context | argument.to"]
    E000301 -->|"node"| X000302
    X000303["context | actor"]
    E000301 -->|"exclude_owner"| X000303
    E000304["effect[1]: move_entity"]
    A000219 --> E000304
    X000305["context | self"]
    E000304 -->|"entity"| X000305
    X000306["context | argument.to"]
    E000304 -->|"destination"| X000306
    E000307["effect[2]: emit_event"]
    A000219 --> E000307
    X000308["literal | piece.moved"]
    E000307 -->|"name"| X000308
    E000309["effect[3]: advance_turn"]
    A000219 --> E000309
    A000310["chess: queen.generate | hook | phase:turn | hook:action.generate"]
    F043 -.-> A000310
    X000311["eq"]
    A000310 -->|"condition"| X000311
    X000312["owner"]
    X000311 -->|"a"| X000312
    X000313["context | self"]
    X000312 -->|"entity"| X000313
    X000314["context | actor"]
    X000311 -->|"b"| X000314
    X000315["reachable_grid_nodes"]
    A000310 -->|"iterator"| X000315
    X000316["context | self"]
    X000315 -->|"entity"| X000316
    X000317["list"]
    X000315 -->|"directions"| X000317
    X000318["vector"]
    X000317 -->|"values[0]"| X000318
    X000319["literal | 1"]
    X000318 -->|"row"| X000319
    X000320["literal | 0"]
    X000318 -->|"column"| X000320
    X000321["vector"]
    X000317 -->|"values[1]"| X000321
    X000322["literal | -1"]
    X000321 -->|"row"| X000322
    X000323["literal | 0"]
    X000321 -->|"column"| X000323
    X000324["vector"]
    X000317 -->|"values[2]"| X000324
    X000325["literal | 0"]
    X000324 -->|"row"| X000325
    X000326["literal | 1"]
    X000324 -->|"column"| X000326
    X000327["vector"]
    X000317 -->|"values[3]"| X000327
    X000328["literal | 0"]
    X000327 -->|"row"| X000328
    X000329["literal | -1"]
    X000327 -->|"column"| X000329
    X000330["vector"]
    X000317 -->|"values[4]"| X000330
    X000331["literal | 1"]
    X000330 -->|"row"| X000331
    X000332["literal | 1"]
    X000330 -->|"column"| X000332
    X000333["vector"]
    X000317 -->|"values[5]"| X000333
    X000334["literal | 1"]
    X000333 -->|"row"| X000334
    X000335["literal | -1"]
    X000333 -->|"column"| X000335
    X000336["vector"]
    X000317 -->|"values[6]"| X000336
    X000337["literal | -1"]
    X000336 -->|"row"| X000337
    X000338["literal | 1"]
    X000336 -->|"column"| X000338
    X000339["vector"]
    X000317 -->|"values[7]"| X000339
    X000340["literal | -1"]
    X000339 -->|"row"| X000340
    X000341["literal | -1"]
    X000339 -->|"column"| X000341
    X000342["literal | 7"]
    X000315 -->|"max_steps"| X000342
    X000343["literal | False"]
    X000315 -->|"leap"| X000343
    X000344["literal | 1"]
    X000315 -->|"orientation"| X000344
    X000345["literal | empty_or_opponent"]
    X000315 -->|"target_occupancy"| X000345
    X000346["context | observed_state"]
    X000315 -->|"state"| X000346
    E000347["effect[0]: emit_candidate"]
    A000310 --> E000347
    X000348["context | self"]
    E000347 -->|"source"| X000348
    X000349["context | candidate"]
    E000347 -->|"destination"| X000349
    A000350["chess: king.move | command | phase:turn"]
    F043 -.-> A000350
    X000351["and"]
    A000350 -->|"condition"| X000351
    X000352["eq"]
    X000351 -->|"values[0]"| X000352
    X000353["owner"]
    X000352 -->|"a"| X000353
    X000354["context | self"]
    X000353 -->|"entity"| X000354
    X000355["context | actor"]
    X000352 -->|"b"| X000355
    X000356["phase_is"]
    X000351 -->|"values[1]"| X000356
    X000357["literal | turn"]
    X000356 -->|"phase"| X000357
    X000358["is_active"]
    X000351 -->|"values[2]"| X000358
    X000359["context | actor"]
    X000358 -->|"participant"| X000359
    X000360["contains"]
    X000351 -->|"values[3]"| X000360
    X000361["reachable_grid_nodes"]
    X000360 -->|"items"| X000361
    X000362["context | self"]
    X000361 -->|"entity"| X000362
    X000363["list"]
    X000361 -->|"directions"| X000363
    X000364["vector"]
    X000363 -->|"values[0]"| X000364
    X000365["literal | 1"]
    X000364 -->|"row"| X000365
    X000366["literal | 0"]
    X000364 -->|"column"| X000366
    X000367["vector"]
    X000363 -->|"values[1]"| X000367
    X000368["literal | -1"]
    X000367 -->|"row"| X000368
    X000369["literal | 0"]
    X000367 -->|"column"| X000369
    X000370["vector"]
    X000363 -->|"values[2]"| X000370
    X000371["literal | 0"]
    X000370 -->|"row"| X000371
    X000372["literal | 1"]
    X000370 -->|"column"| X000372
    X000373["vector"]
    X000363 -->|"values[3]"| X000373
    X000374["literal | 0"]
    X000373 -->|"row"| X000374
    X000375["literal | -1"]
    X000373 -->|"column"| X000375
    X000376["vector"]
    X000363 -->|"values[4]"| X000376
    X000377["literal | 1"]
    X000376 -->|"row"| X000377
    X000378["literal | 1"]
    X000376 -->|"column"| X000378
    X000379["vector"]
    X000363 -->|"values[5]"| X000379
    X000380["literal | 1"]
    X000379 -->|"row"| X000380
    X000381["literal | -1"]
    X000379 -->|"column"| X000381
    X000382["vector"]
    X000363 -->|"values[6]"| X000382
    X000383["literal | -1"]
    X000382 -->|"row"| X000383
    X000384["literal | 1"]
    X000382 -->|"column"| X000384
    X000385["vector"]
    X000363 -->|"values[7]"| X000385
    X000386["literal | -1"]
    X000385 -->|"row"| X000386
    X000387["literal | -1"]
    X000385 -->|"column"| X000387
    X000388["literal | 1"]
    X000361 -->|"max_steps"| X000388
    X000389["literal | False"]
    X000361 -->|"leap"| X000389
    X000390["literal | 1"]
    X000361 -->|"orientation"| X000390
    X000391["literal | empty_or_opponent"]
    X000361 -->|"target_occupancy"| X000391
    X000392["context | observed_state"]
    X000361 -->|"state"| X000392
    X000393["context | argument.to"]
    X000360 -->|"value"| X000393
    X000394["none_match"]
    X000351 -->|"values[4]"| X000394
    X000395["entities_at"]
    X000394 -->|"items"| X000395
    X000396["context | argument.to"]
    X000395 -->|"node"| X000396
    X000397["literal | other"]
    X000394 -->|"variable"| X000397
    X000398["eq"]
    X000394 -->|"predicate"| X000398
    X000399["owner"]
    X000398 -->|"a"| X000399
    X000400["context | local.other"]
    X000399 -->|"entity"| X000400
    X000401["owner"]
    X000398 -->|"b"| X000401
    X000402["context | self"]
    X000401 -->|"entity"| X000402
    X000403["none_match"]
    X000351 -->|"values[5]"| X000403
    X000404["entities_matching"]
    X000403 -->|"items"| X000404
    X000405["literal | king"]
    X000404 -->|"entity_type"| X000405
    X000406["context | actor"]
    X000404 -->|"owner"| X000406
    X000407["preview"]
    X000404 -->|"state"| X000407
    X000408["context | observed_state"]
    X000407 -->|"state"| X000408
    X000409["list"]
    X000407 -->|"effects"| X000409
    X000410["effect_value"]
    X000409 -->|"values[0]"| X000410
    X000411["literal | move_entity"]
    X000410 -->|"name"| X000411
    X000412["context | self"]
    X000410 -->|"entity"| X000412
    X000413["context | argument.to"]
    X000410 -->|"destination"| X000413
    X000414["literal | protected"]
    X000403 -->|"variable"| X000414
    X000415["threatened"]
    X000403 -->|"predicate"| X000415
    X000416["context | local.protected"]
    X000415 -->|"entity"| X000416
    X000417["preview"]
    X000415 -->|"state"| X000417
    X000418["context | observed_state"]
    X000417 -->|"state"| X000418
    X000419["list"]
    X000417 -->|"effects"| X000419
    X000420["effect_value"]
    X000419 -->|"values[0]"| X000420
    X000421["literal | move_entity"]
    X000420 -->|"name"| X000421
    X000422["context | self"]
    X000420 -->|"entity"| X000422
    X000423["context | argument.to"]
    X000420 -->|"destination"| X000423
    X000424["none_match"]
    X000351 -->|"values[6]"| X000424
    X000425["entities_at"]
    X000424 -->|"items"| X000425
    X000426["context | argument.to"]
    X000425 -->|"node"| X000426
    X000427["literal | occupant"]
    X000424 -->|"variable"| X000427
    X000428["contains"]
    X000424 -->|"predicate"| X000428
    X000429["entities_of_type"]
    X000428 -->|"items"| X000429
    X000430["literal | king"]
    X000429 -->|"entity_type"| X000430
    X000431["context | local.occupant"]
    X000428 -->|"value"| X000431
    E000432["effect[0]: remove_matching_entities"]
    A000350 --> E000432
    X000433["context | argument.to"]
    E000432 -->|"node"| X000433
    X000434["context | actor"]
    E000432 -->|"exclude_owner"| X000434
    E000435["effect[1]: move_entity"]
    A000350 --> E000435
    X000436["context | self"]
    E000435 -->|"entity"| X000436
    X000437["context | argument.to"]
    E000435 -->|"destination"| X000437
    E000438["effect[2]: emit_event"]
    A000350 --> E000438
    X000439["literal | piece.moved"]
    E000438 -->|"name"| X000439
    E000440["effect[3]: set_field"]
    A000350 --> E000440
    X000441["context | self"]
    E000440 -->|"entity"| X000441
    X000442["literal | moved"]
    E000440 -->|"field"| X000442
    X000443["literal | True"]
    E000440 -->|"value"| X000443
    E000444["effect[4]: advance_turn"]
    A000350 --> E000444
    A000445["chess: king.generate | hook | phase:turn | hook:action.generate"]
    F043 -.-> A000445
    X000446["eq"]
    A000445 -->|"condition"| X000446
    X000447["owner"]
    X000446 -->|"a"| X000447
    X000448["context | self"]
    X000447 -->|"entity"| X000448
    X000449["context | actor"]
    X000446 -->|"b"| X000449
    X000450["reachable_grid_nodes"]
    A000445 -->|"iterator"| X000450
    X000451["context | self"]
    X000450 -->|"entity"| X000451
    X000452["list"]
    X000450 -->|"directions"| X000452
    X000453["vector"]
    X000452 -->|"values[0]"| X000453
    X000454["literal | 1"]
    X000453 -->|"row"| X000454
    X000455["literal | 0"]
    X000453 -->|"column"| X000455
    X000456["vector"]
    X000452 -->|"values[1]"| X000456
    X000457["literal | -1"]
    X000456 -->|"row"| X000457
    X000458["literal | 0"]
    X000456 -->|"column"| X000458
    X000459["vector"]
    X000452 -->|"values[2]"| X000459
    X000460["literal | 0"]
    X000459 -->|"row"| X000460
    X000461["literal | 1"]
    X000459 -->|"column"| X000461
    X000462["vector"]
    X000452 -->|"values[3]"| X000462
    X000463["literal | 0"]
    X000462 -->|"row"| X000463
    X000464["literal | -1"]
    X000462 -->|"column"| X000464
    X000465["vector"]
    X000452 -->|"values[4]"| X000465
    X000466["literal | 1"]
    X000465 -->|"row"| X000466
    X000467["literal | 1"]
    X000465 -->|"column"| X000467
    X000468["vector"]
    X000452 -->|"values[5]"| X000468
    X000469["literal | 1"]
    X000468 -->|"row"| X000469
    X000470["literal | -1"]
    X000468 -->|"column"| X000470
    X000471["vector"]
    X000452 -->|"values[6]"| X000471
    X000472["literal | -1"]
    X000471 -->|"row"| X000472
    X000473["literal | 1"]
    X000471 -->|"column"| X000473
    X000474["vector"]
    X000452 -->|"values[7]"| X000474
    X000475["literal | -1"]
    X000474 -->|"row"| X000475
    X000476["literal | -1"]
    X000474 -->|"column"| X000476
    X000477["literal | 1"]
    X000450 -->|"max_steps"| X000477
    X000478["literal | False"]
    X000450 -->|"leap"| X000478
    X000479["literal | 1"]
    X000450 -->|"orientation"| X000479
    X000480["literal | empty_or_opponent"]
    X000450 -->|"target_occupancy"| X000480
    X000481["context | observed_state"]
    X000450 -->|"state"| X000481
    E000482["effect[0]: emit_candidate"]
    A000445 --> E000482
    X000483["context | self"]
    E000482 -->|"source"| X000483
    X000484["context | candidate"]
    E000482 -->|"destination"| X000484
    A000485["chess: knight.move | command | phase:turn"]
    F043 -.-> A000485
    X000486["and"]
    A000485 -->|"condition"| X000486
    X000487["eq"]
    X000486 -->|"values[0]"| X000487
    X000488["owner"]
    X000487 -->|"a"| X000488
    X000489["context | self"]
    X000488 -->|"entity"| X000489
    X000490["context | actor"]
    X000487 -->|"b"| X000490
    X000491["phase_is"]
    X000486 -->|"values[1]"| X000491
    X000492["literal | turn"]
    X000491 -->|"phase"| X000492
    X000493["is_active"]
    X000486 -->|"values[2]"| X000493
    X000494["context | actor"]
    X000493 -->|"participant"| X000494
    X000495["contains"]
    X000486 -->|"values[3]"| X000495
    X000496["reachable_grid_nodes"]
    X000495 -->|"items"| X000496
    X000497["context | self"]
    X000496 -->|"entity"| X000497
    X000498["list"]
    X000496 -->|"directions"| X000498
    X000499["vector"]
    X000498 -->|"values[0]"| X000499
    X000500["literal | 2"]
    X000499 -->|"row"| X000500
    X000501["literal | 1"]
    X000499 -->|"column"| X000501
    X000502["vector"]
    X000498 -->|"values[1]"| X000502
    X000503["literal | 2"]
    X000502 -->|"row"| X000503
    X000504["literal | -1"]
    X000502 -->|"column"| X000504
    X000505["vector"]
    X000498 -->|"values[2]"| X000505
    X000506["literal | -2"]
    X000505 -->|"row"| X000506
    X000507["literal | 1"]
    X000505 -->|"column"| X000507
    X000508["vector"]
    X000498 -->|"values[3]"| X000508
    X000509["literal | -2"]
    X000508 -->|"row"| X000509
    X000510["literal | -1"]
    X000508 -->|"column"| X000510
    X000511["vector"]
    X000498 -->|"values[4]"| X000511
    X000512["literal | 1"]
    X000511 -->|"row"| X000512
    X000513["literal | 2"]
    X000511 -->|"column"| X000513
    X000514["vector"]
    X000498 -->|"values[5]"| X000514
    X000515["literal | 1"]
    X000514 -->|"row"| X000515
    X000516["literal | -2"]
    X000514 -->|"column"| X000516
    X000517["vector"]
    X000498 -->|"values[6]"| X000517
    X000518["literal | -1"]
    X000517 -->|"row"| X000518
    X000519["literal | 2"]
    X000517 -->|"column"| X000519
    X000520["vector"]
    X000498 -->|"values[7]"| X000520
    X000521["literal | -1"]
    X000520 -->|"row"| X000521
    X000522["literal | -2"]
    X000520 -->|"column"| X000522
    X000523["literal | 1"]
    X000496 -->|"max_steps"| X000523
    X000524["literal | True"]
    X000496 -->|"leap"| X000524
    X000525["literal | 1"]
    X000496 -->|"orientation"| X000525
    X000526["literal | empty_or_opponent"]
    X000496 -->|"target_occupancy"| X000526
    X000527["context | observed_state"]
    X000496 -->|"state"| X000527
    X000528["context | argument.to"]
    X000495 -->|"value"| X000528
    X000529["none_match"]
    X000486 -->|"values[4]"| X000529
    X000530["entities_at"]
    X000529 -->|"items"| X000530
    X000531["context | argument.to"]
    X000530 -->|"node"| X000531
    X000532["literal | other"]
    X000529 -->|"variable"| X000532
    X000533["eq"]
    X000529 -->|"predicate"| X000533
    X000534["owner"]
    X000533 -->|"a"| X000534
    X000535["context | local.other"]
    X000534 -->|"entity"| X000535
    X000536["owner"]
    X000533 -->|"b"| X000536
    X000537["context | self"]
    X000536 -->|"entity"| X000537
    X000538["none_match"]
    X000486 -->|"values[5]"| X000538
    X000539["entities_matching"]
    X000538 -->|"items"| X000539
    X000540["literal | king"]
    X000539 -->|"entity_type"| X000540
    X000541["context | actor"]
    X000539 -->|"owner"| X000541
    X000542["preview"]
    X000539 -->|"state"| X000542
    X000543["context | observed_state"]
    X000542 -->|"state"| X000543
    X000544["list"]
    X000542 -->|"effects"| X000544
    X000545["effect_value"]
    X000544 -->|"values[0]"| X000545
    X000546["literal | move_entity"]
    X000545 -->|"name"| X000546
    X000547["context | self"]
    X000545 -->|"entity"| X000547
    X000548["context | argument.to"]
    X000545 -->|"destination"| X000548
    X000549["literal | protected"]
    X000538 -->|"variable"| X000549
    X000550["threatened"]
    X000538 -->|"predicate"| X000550
    X000551["context | local.protected"]
    X000550 -->|"entity"| X000551
    X000552["preview"]
    X000550 -->|"state"| X000552
    X000553["context | observed_state"]
    X000552 -->|"state"| X000553
    X000554["list"]
    X000552 -->|"effects"| X000554
    X000555["effect_value"]
    X000554 -->|"values[0]"| X000555
    X000556["literal | move_entity"]
    X000555 -->|"name"| X000556
    X000557["context | self"]
    X000555 -->|"entity"| X000557
    X000558["context | argument.to"]
    X000555 -->|"destination"| X000558
    X000559["none_match"]
    X000486 -->|"values[6]"| X000559
    X000560["entities_at"]
    X000559 -->|"items"| X000560
    X000561["context | argument.to"]
    X000560 -->|"node"| X000561
    X000562["literal | occupant"]
    X000559 -->|"variable"| X000562
    X000563["contains"]
    X000559 -->|"predicate"| X000563
    X000564["entities_of_type"]
    X000563 -->|"items"| X000564
    X000565["literal | king"]
    X000564 -->|"entity_type"| X000565
    X000566["context | local.occupant"]
    X000563 -->|"value"| X000566
    E000567["effect[0]: remove_matching_entities"]
    A000485 --> E000567
    X000568["context | argument.to"]
    E000567 -->|"node"| X000568
    X000569["context | actor"]
    E000567 -->|"exclude_owner"| X000569
    E000570["effect[1]: move_entity"]
    A000485 --> E000570
    X000571["context | self"]
    E000570 -->|"entity"| X000571
    X000572["context | argument.to"]
    E000570 -->|"destination"| X000572
    E000573["effect[2]: emit_event"]
    A000485 --> E000573
    X000574["literal | piece.moved"]
    E000573 -->|"name"| X000574
    E000575["effect[3]: advance_turn"]
    A000485 --> E000575
    A000576["chess: knight.generate | hook | phase:turn | hook:action.generate"]
    F043 -.-> A000576
    X000577["eq"]
    A000576 -->|"condition"| X000577
    X000578["owner"]
    X000577 -->|"a"| X000578
    X000579["context | self"]
    X000578 -->|"entity"| X000579
    X000580["context | actor"]
    X000577 -->|"b"| X000580
    X000581["reachable_grid_nodes"]
    A000576 -->|"iterator"| X000581
    X000582["context | self"]
    X000581 -->|"entity"| X000582
    X000583["list"]
    X000581 -->|"directions"| X000583
    X000584["vector"]
    X000583 -->|"values[0]"| X000584
    X000585["literal | 2"]
    X000584 -->|"row"| X000585
    X000586["literal | 1"]
    X000584 -->|"column"| X000586
    X000587["vector"]
    X000583 -->|"values[1]"| X000587
    X000588["literal | 2"]
    X000587 -->|"row"| X000588
    X000589["literal | -1"]
    X000587 -->|"column"| X000589
    X000590["vector"]
    X000583 -->|"values[2]"| X000590
    X000591["literal | -2"]
    X000590 -->|"row"| X000591
    X000592["literal | 1"]
    X000590 -->|"column"| X000592
    X000593["vector"]
    X000583 -->|"values[3]"| X000593
    X000594["literal | -2"]
    X000593 -->|"row"| X000594
    X000595["literal | -1"]
    X000593 -->|"column"| X000595
    X000596["vector"]
    X000583 -->|"values[4]"| X000596
    X000597["literal | 1"]
    X000596 -->|"row"| X000597
    X000598["literal | 2"]
    X000596 -->|"column"| X000598
    X000599["vector"]
    X000583 -->|"values[5]"| X000599
    X000600["literal | 1"]
    X000599 -->|"row"| X000600
    X000601["literal | -2"]
    X000599 -->|"column"| X000601
    X000602["vector"]
    X000583 -->|"values[6]"| X000602
    X000603["literal | -1"]
    X000602 -->|"row"| X000603
    X000604["literal | 2"]
    X000602 -->|"column"| X000604
    X000605["vector"]
    X000583 -->|"values[7]"| X000605
    X000606["literal | -1"]
    X000605 -->|"row"| X000606
    X000607["literal | -2"]
    X000605 -->|"column"| X000607
    X000608["literal | 1"]
    X000581 -->|"max_steps"| X000608
    X000609["literal | True"]
    X000581 -->|"leap"| X000609
    X000610["literal | 1"]
    X000581 -->|"orientation"| X000610
    X000611["literal | empty_or_opponent"]
    X000581 -->|"target_occupancy"| X000611
    X000612["context | observed_state"]
    X000581 -->|"state"| X000612
    E000613["effect[0]: emit_candidate"]
    A000576 --> E000613
    X000614["context | self"]
    E000613 -->|"source"| X000614
    X000615["context | candidate"]
    E000613 -->|"destination"| X000615
    A000616["chess: pawn.move | command | phase:turn"]
    F043 -.-> A000616
    X000617["and"]
    A000616 -->|"condition"| X000617
    X000618["eq"]
    X000617 -->|"values[0]"| X000618
    X000619["owner"]
    X000618 -->|"a"| X000619
    X000620["context | self"]
    X000619 -->|"entity"| X000620
    X000621["context | actor"]
    X000618 -->|"b"| X000621
    X000622["phase_is"]
    X000617 -->|"values[1]"| X000622
    X000623["literal | turn"]
    X000622 -->|"phase"| X000623
    X000624["is_active"]
    X000617 -->|"values[2]"| X000624
    X000625["context | actor"]
    X000624 -->|"participant"| X000625
    X000626["contains"]
    X000617 -->|"values[3]"| X000626
    X000627["concat"]
    X000626 -->|"items"| X000627
    X000628["reachable_grid_nodes"]
    X000627 -->|"a"| X000628
    X000629["context | self"]
    X000628 -->|"entity"| X000629
    X000630["list"]
    X000628 -->|"directions"| X000630
    X000631["vector"]
    X000630 -->|"values[0]"| X000631
    X000632["literal | 1"]
    X000631 -->|"row"| X000632
    X000633["literal | 0"]
    X000631 -->|"column"| X000633
    X000634["literal | 1"]
    X000628 -->|"max_steps"| X000634
    X000635["literal | False"]
    X000628 -->|"leap"| X000635
    X000636["owner_orientation"]
    X000628 -->|"orientation"| X000636
    X000637["context | self"]
    X000636 -->|"entity"| X000637
    X000638["literal | empty"]
    X000628 -->|"target_occupancy"| X000638
    X000639["context | observed_state"]
    X000628 -->|"state"| X000639
    X000640["concat"]
    X000627 -->|"b"| X000640
    X000641["if"]
    X000640 -->|"a"| X000641
    X000642["not"]
    X000641 -->|"condition"| X000642
    X000643["field"]
    X000642 -->|"value"| X000643
    X000644["context | self"]
    X000643 -->|"entity"| X000644
    X000645["literal | moved"]
    X000643 -->|"key"| X000645
    X000646["only_path_distance"]
    X000641 -->|"then"| X000646
    X000647["reachable_grid_nodes"]
    X000646 -->|"nodes"| X000647
    X000648["context | self"]
    X000647 -->|"entity"| X000648
    X000649["list"]
    X000647 -->|"directions"| X000649
    X000650["vector"]
    X000649 -->|"values[0]"| X000650
    X000651["literal | 1"]
    X000650 -->|"row"| X000651
    X000652["literal | 0"]
    X000650 -->|"column"| X000652
    X000653["literal | 2"]
    X000647 -->|"max_steps"| X000653
    X000654["literal | False"]
    X000647 -->|"leap"| X000654
    X000655["owner_orientation"]
    X000647 -->|"orientation"| X000655
    X000656["context | self"]
    X000655 -->|"entity"| X000656
    X000657["literal | empty"]
    X000647 -->|"target_occupancy"| X000657
    X000658["context | observed_state"]
    X000647 -->|"state"| X000658
    X000659["literal | 2"]
    X000646 -->|"distance"| X000659
    X000660["list"]
    X000641 -->|"otherwise"| X000660
    X000661["reachable_grid_nodes"]
    X000640 -->|"b"| X000661
    X000662["context | self"]
    X000661 -->|"entity"| X000662
    X000663["list"]
    X000661 -->|"directions"| X000663
    X000664["vector"]
    X000663 -->|"values[0]"| X000664
    X000665["literal | 1"]
    X000664 -->|"row"| X000665
    X000666["literal | -1"]
    X000664 -->|"column"| X000666
    X000667["vector"]
    X000663 -->|"values[1]"| X000667
    X000668["literal | 1"]
    X000667 -->|"row"| X000668
    X000669["literal | 1"]
    X000667 -->|"column"| X000669
    X000670["literal | 1"]
    X000661 -->|"max_steps"| X000670
    X000671["literal | False"]
    X000661 -->|"leap"| X000671
    X000672["owner_orientation"]
    X000661 -->|"orientation"| X000672
    X000673["context | self"]
    X000672 -->|"entity"| X000673
    X000674["literal | opponent"]
    X000661 -->|"target_occupancy"| X000674
    X000675["context | observed_state"]
    X000661 -->|"state"| X000675
    X000676["context | argument.to"]
    X000626 -->|"value"| X000676
    X000677["none_match"]
    X000617 -->|"values[4]"| X000677
    X000678["entities_at"]
    X000677 -->|"items"| X000678
    X000679["context | argument.to"]
    X000678 -->|"node"| X000679
    X000680["literal | other"]
    X000677 -->|"variable"| X000680
    X000681["eq"]
    X000677 -->|"predicate"| X000681
    X000682["owner"]
    X000681 -->|"a"| X000682
    X000683["context | local.other"]
    X000682 -->|"entity"| X000683
    X000684["owner"]
    X000681 -->|"b"| X000684
    X000685["context | self"]
    X000684 -->|"entity"| X000685
    X000686["none_match"]
    X000617 -->|"values[5]"| X000686
    X000687["entities_matching"]
    X000686 -->|"items"| X000687
    X000688["literal | king"]
    X000687 -->|"entity_type"| X000688
    X000689["context | actor"]
    X000687 -->|"owner"| X000689
    X000690["preview"]
    X000687 -->|"state"| X000690
    X000691["context | observed_state"]
    X000690 -->|"state"| X000691
    X000692["list"]
    X000690 -->|"effects"| X000692
    X000693["effect_value"]
    X000692 -->|"values[0]"| X000693
    X000694["literal | move_entity"]
    X000693 -->|"name"| X000694
    X000695["context | self"]
    X000693 -->|"entity"| X000695
    X000696["context | argument.to"]
    X000693 -->|"destination"| X000696
    X000697["literal | protected"]
    X000686 -->|"variable"| X000697
    X000698["threatened"]
    X000686 -->|"predicate"| X000698
    X000699["context | local.protected"]
    X000698 -->|"entity"| X000699
    X000700["preview"]
    X000698 -->|"state"| X000700
    X000701["context | observed_state"]
    X000700 -->|"state"| X000701
    X000702["list"]
    X000700 -->|"effects"| X000702
    X000703["effect_value"]
    X000702 -->|"values[0]"| X000703
    X000704["literal | move_entity"]
    X000703 -->|"name"| X000704
    X000705["context | self"]
    X000703 -->|"entity"| X000705
    X000706["context | argument.to"]
    X000703 -->|"destination"| X000706
    X000707["none_match"]
    X000617 -->|"values[6]"| X000707
    X000708["entities_at"]
    X000707 -->|"items"| X000708
    X000709["context | argument.to"]
    X000708 -->|"node"| X000709
    X000710["literal | occupant"]
    X000707 -->|"variable"| X000710
    X000711["contains"]
    X000707 -->|"predicate"| X000711
    X000712["entities_of_type"]
    X000711 -->|"items"| X000712
    X000713["literal | king"]
    X000712 -->|"entity_type"| X000713
    X000714["context | local.occupant"]
    X000711 -->|"value"| X000714
    E000715["effect[0]: remove_matching_entities"]
    A000616 --> E000715
    X000716["context | argument.to"]
    E000715 -->|"node"| X000716
    X000717["context | actor"]
    E000715 -->|"exclude_owner"| X000717
    E000718["effect[1]: move_entity"]
    A000616 --> E000718
    X000719["context | self"]
    E000718 -->|"entity"| X000719
    X000720["context | argument.to"]
    E000718 -->|"destination"| X000720
    E000721["effect[2]: emit_event"]
    A000616 --> E000721
    X000722["literal | piece.moved"]
    E000721 -->|"name"| X000722
    E000723["effect[3]: set_field"]
    A000616 --> E000723
    X000724["context | self"]
    E000723 -->|"entity"| X000724
    X000725["literal | moved"]
    E000723 -->|"field"| X000725
    X000726["literal | True"]
    E000723 -->|"value"| X000726
    E000727["effect[4]: change_entity_type"]
    A000616 --> E000727
    X000728["on_board_edge"]
    E000727 -->|"when"| X000728
    X000729["context | self"]
    X000728 -->|"entity"| X000729
    X000730["literal | promotion"]
    X000728 -->|"edge"| X000730
    X000731["context | self"]
    E000727 -->|"entity"| X000731
    X000732["if"]
    E000727 -->|"to"| X000732
    X000733["is_present"]
    X000732 -->|"condition"| X000733
    X000734["context | argument.promotion"]
    X000733 -->|"value"| X000734
    X000735["context | argument.promotion"]
    X000732 -->|"then"| X000735
    X000736["literal | queen"]
    X000732 -->|"otherwise"| X000736
    E000737["effect[5]: advance_turn"]
    A000616 --> E000737
    A000738["chess: pawn.generate | hook | phase:turn | hook:action.generate"]
    F043 -.-> A000738
    X000739["eq"]
    A000738 -->|"condition"| X000739
    X000740["owner"]
    X000739 -->|"a"| X000740
    X000741["context | self"]
    X000740 -->|"entity"| X000741
    X000742["context | actor"]
    X000739 -->|"b"| X000742
    X000743["concat"]
    A000738 -->|"iterator"| X000743
    X000744["reachable_grid_nodes"]
    X000743 -->|"a"| X000744
    X000745["context | self"]
    X000744 -->|"entity"| X000745
    X000746["list"]
    X000744 -->|"directions"| X000746
    X000747["vector"]
    X000746 -->|"values[0]"| X000747
    X000748["literal | 1"]
    X000747 -->|"row"| X000748
    X000749["literal | 0"]
    X000747 -->|"column"| X000749
    X000750["literal | 1"]
    X000744 -->|"max_steps"| X000750
    X000751["literal | False"]
    X000744 -->|"leap"| X000751
    X000752["owner_orientation"]
    X000744 -->|"orientation"| X000752
    X000753["context | self"]
    X000752 -->|"entity"| X000753
    X000754["literal | empty"]
    X000744 -->|"target_occupancy"| X000754
    X000755["context | observed_state"]
    X000744 -->|"state"| X000755
    X000756["concat"]
    X000743 -->|"b"| X000756
    X000757["if"]
    X000756 -->|"a"| X000757
    X000758["not"]
    X000757 -->|"condition"| X000758
    X000759["field"]
    X000758 -->|"value"| X000759
    X000760["context | self"]
    X000759 -->|"entity"| X000760
    X000761["literal | moved"]
    X000759 -->|"key"| X000761
    X000762["only_path_distance"]
    X000757 -->|"then"| X000762
    X000763["reachable_grid_nodes"]
    X000762 -->|"nodes"| X000763
    X000764["context | self"]
    X000763 -->|"entity"| X000764
    X000765["list"]
    X000763 -->|"directions"| X000765
    X000766["vector"]
    X000765 -->|"values[0]"| X000766
    X000767["literal | 1"]
    X000766 -->|"row"| X000767
    X000768["literal | 0"]
    X000766 -->|"column"| X000768
    X000769["literal | 2"]
    X000763 -->|"max_steps"| X000769
    X000770["literal | False"]
    X000763 -->|"leap"| X000770
    X000771["owner_orientation"]
    X000763 -->|"orientation"| X000771
    X000772["context | self"]
    X000771 -->|"entity"| X000772
    X000773["literal | empty"]
    X000763 -->|"target_occupancy"| X000773
    X000774["context | observed_state"]
    X000763 -->|"state"| X000774
    X000775["literal | 2"]
    X000762 -->|"distance"| X000775
    X000776["list"]
    X000757 -->|"otherwise"| X000776
    X000777["reachable_grid_nodes"]
    X000756 -->|"b"| X000777
    X000778["context | self"]
    X000777 -->|"entity"| X000778
    X000779["list"]
    X000777 -->|"directions"| X000779
    X000780["vector"]
    X000779 -->|"values[0]"| X000780
    X000781["literal | 1"]
    X000780 -->|"row"| X000781
    X000782["literal | -1"]
    X000780 -->|"column"| X000782
    X000783["vector"]
    X000779 -->|"values[1]"| X000783
    X000784["literal | 1"]
    X000783 -->|"row"| X000784
    X000785["literal | 1"]
    X000783 -->|"column"| X000785
    X000786["literal | 1"]
    X000777 -->|"max_steps"| X000786
    X000787["literal | False"]
    X000777 -->|"leap"| X000787
    X000788["owner_orientation"]
    X000777 -->|"orientation"| X000788
    X000789["context | self"]
    X000788 -->|"entity"| X000789
    X000790["literal | opponent"]
    X000777 -->|"target_occupancy"| X000790
    X000791["context | observed_state"]
    X000777 -->|"state"| X000791
    E000792["effect[0]: emit_candidate"]
    A000738 --> E000792
    X000793["context | self"]
    E000792 -->|"source"| X000793
    X000794["context | candidate"]
    E000792 -->|"destination"| X000794
    A000795["chess: king.castle_king | command | phase:turn"]
    F043 -.-> A000795
    X000796["and"]
    A000795 -->|"condition"| X000796
    X000797["not"]
    X000796 -->|"values[0]"| X000797
    X000798["field"]
    X000797 -->|"value"| X000798
    X000799["context | self"]
    X000798 -->|"entity"| X000799
    X000800["literal | moved"]
    X000798 -->|"key"| X000800
    X000801["is_present"]
    X000796 -->|"values[1]"| X000801
    X000802["first"]
    X000801 -->|"value"| X000802
    X000803["filter"]
    X000802 -->|"items"| X000803
    X000804["entities_of_type"]
    X000803 -->|"items"| X000804
    X000805["literal | rook"]
    X000804 -->|"entity_type"| X000805
    X000806["literal | r"]
    X000803 -->|"variable"| X000806
    X000807["and"]
    X000803 -->|"predicate"| X000807
    X000808["eq"]
    X000807 -->|"values[0]"| X000808
    X000809["owner"]
    X000808 -->|"a"| X000809
    X000810["context | local.r"]
    X000809 -->|"entity"| X000810
    X000811["context | actor"]
    X000808 -->|"b"| X000811
    X000812["not"]
    X000807 -->|"values[1]"| X000812
    X000813["field"]
    X000812 -->|"value"| X000813
    X000814["context | local.r"]
    X000813 -->|"entity"| X000814
    X000815["literal | moved"]
    X000813 -->|"key"| X000815
    X000816["eq"]
    X000807 -->|"values[2]"| X000816
    X000817["entity_location"]
    X000816 -->|"a"| X000817
    X000818["context | local.r"]
    X000817 -->|"entity"| X000818
    X000819["grid_edge"]
    X000816 -->|"b"| X000819
    X000820["context | self"]
    X000819 -->|"entity"| X000820
    X000821["literal | right"]
    X000819 -->|"horizontal"| X000821
    X000822["path_clear"]
    X000796 -->|"values[2]"| X000822
    X000823["grid_between"]
    X000822 -->|"nodes"| X000823
    X000824["entity_location"]
    X000823 -->|"first"| X000824
    X000825["context | self"]
    X000824 -->|"entity"| X000825
    X000826["entity_location"]
    X000823 -->|"last"| X000826
    X000827["first"]
    X000826 -->|"entity"| X000827
    X000828["filter"]
    X000827 -->|"items"| X000828
    X000829["entities_of_type"]
    X000828 -->|"items"| X000829
    X000830["literal | rook"]
    X000829 -->|"entity_type"| X000830
    X000831["literal | r"]
    X000828 -->|"variable"| X000831
    X000832["and"]
    X000828 -->|"predicate"| X000832
    X000833["eq"]
    X000832 -->|"values[0]"| X000833
    X000834["owner"]
    X000833 -->|"a"| X000834
    X000835["context | local.r"]
    X000834 -->|"entity"| X000835
    X000836["context | actor"]
    X000833 -->|"b"| X000836
    X000837["not"]
    X000832 -->|"values[1]"| X000837
    X000838["field"]
    X000837 -->|"value"| X000838
    X000839["context | local.r"]
    X000838 -->|"entity"| X000839
    X000840["literal | moved"]
    X000838 -->|"key"| X000840
    X000841["eq"]
    X000832 -->|"values[2]"| X000841
    X000842["entity_location"]
    X000841 -->|"a"| X000842
    X000843["context | local.r"]
    X000842 -->|"entity"| X000843
    X000844["grid_edge"]
    X000841 -->|"b"| X000844
    X000845["context | self"]
    X000844 -->|"entity"| X000845
    X000846["literal | right"]
    X000844 -->|"horizontal"| X000846
    X000847["none_match"]
    X000796 -->|"values[3]"| X000847
    X000848["list"]
    X000847 -->|"items"| X000848
    X000849["entity_location"]
    X000848 -->|"values[0]"| X000849
    X000850["context | self"]
    X000849 -->|"entity"| X000850
    X000851["grid_offset"]
    X000848 -->|"values[1]"| X000851
    X000852["context | self"]
    X000851 -->|"entity"| X000852
    X000853["literal | 0"]
    X000851 -->|"row"| X000853
    X000854["literal | 1"]
    X000851 -->|"column"| X000854
    X000855["grid_offset"]
    X000848 -->|"values[2]"| X000855
    X000856["context | self"]
    X000855 -->|"entity"| X000856
    X000857["literal | 0"]
    X000855 -->|"row"| X000857
    X000858["literal | 2"]
    X000855 -->|"column"| X000858
    X000859["literal | square"]
    X000847 -->|"variable"| X000859
    X000860["attacked_node"]
    X000847 -->|"predicate"| X000860
    X000861["context | local.square"]
    X000860 -->|"node"| X000861
    X000862["opponents"]
    X000860 -->|"by"| X000862
    X000863["context | actor"]
    X000862 -->|"participant"| X000863
    E000864["effect[0]: move_entity"]
    A000795 --> E000864
    X000865["context | self"]
    E000864 -->|"entity"| X000865
    X000866["grid_offset"]
    E000864 -->|"destination"| X000866
    X000867["context | self"]
    X000866 -->|"entity"| X000867
    X000868["literal | 0"]
    X000866 -->|"row"| X000868
    X000869["literal | 2"]
    X000866 -->|"column"| X000869
    E000870["effect[1]: move_entity"]
    A000795 --> E000870
    X000871["first"]
    E000870 -->|"entity"| X000871
    X000872["filter"]
    X000871 -->|"items"| X000872
    X000873["entities_of_type"]
    X000872 -->|"items"| X000873
    X000874["literal | rook"]
    X000873 -->|"entity_type"| X000874
    X000875["literal | r"]
    X000872 -->|"variable"| X000875
    X000876["and"]
    X000872 -->|"predicate"| X000876
    X000877["eq"]
    X000876 -->|"values[0]"| X000877
    X000878["owner"]
    X000877 -->|"a"| X000878
    X000879["context | local.r"]
    X000878 -->|"entity"| X000879
    X000880["context | actor"]
    X000877 -->|"b"| X000880
    X000881["not"]
    X000876 -->|"values[1]"| X000881
    X000882["field"]
    X000881 -->|"value"| X000882
    X000883["context | local.r"]
    X000882 -->|"entity"| X000883
    X000884["literal | moved"]
    X000882 -->|"key"| X000884
    X000885["eq"]
    X000876 -->|"values[2]"| X000885
    X000886["entity_location"]
    X000885 -->|"a"| X000886
    X000887["context | local.r"]
    X000886 -->|"entity"| X000887
    X000888["grid_edge"]
    X000885 -->|"b"| X000888
    X000889["context | self"]
    X000888 -->|"entity"| X000889
    X000890["literal | right"]
    X000888 -->|"horizontal"| X000890
    X000891["grid_offset"]
    E000870 -->|"destination"| X000891
    X000892["context | self"]
    X000891 -->|"entity"| X000892
    X000893["literal | 0"]
    X000891 -->|"row"| X000893
    X000894["literal | 1"]
    X000891 -->|"column"| X000894
    E000895["effect[2]: set_field"]
    A000795 --> E000895
    X000896["context | self"]
    E000895 -->|"entity"| X000896
    X000897["literal | moved"]
    E000895 -->|"field"| X000897
    X000898["literal | True"]
    E000895 -->|"value"| X000898
    E000899["effect[3]: set_field"]
    A000795 --> E000899
    X000900["first"]
    E000899 -->|"entity"| X000900
    X000901["filter"]
    X000900 -->|"items"| X000901
    X000902["entities_of_type"]
    X000901 -->|"items"| X000902
    X000903["literal | rook"]
    X000902 -->|"entity_type"| X000903
    X000904["literal | r"]
    X000901 -->|"variable"| X000904
    X000905["and"]
    X000901 -->|"predicate"| X000905
    X000906["eq"]
    X000905 -->|"values[0]"| X000906
    X000907["owner"]
    X000906 -->|"a"| X000907
    X000908["context | local.r"]
    X000907 -->|"entity"| X000908
    X000909["context | actor"]
    X000906 -->|"b"| X000909
    X000910["not"]
    X000905 -->|"values[1]"| X000910
    X000911["field"]
    X000910 -->|"value"| X000911
    X000912["context | local.r"]
    X000911 -->|"entity"| X000912
    X000913["literal | moved"]
    X000911 -->|"key"| X000913
    X000914["eq"]
    X000905 -->|"values[2]"| X000914
    X000915["entity_location"]
    X000914 -->|"a"| X000915
    X000916["context | local.r"]
    X000915 -->|"entity"| X000916
    X000917["grid_edge"]
    X000914 -->|"b"| X000917
    X000918["context | self"]
    X000917 -->|"entity"| X000918
    X000919["literal | right"]
    X000917 -->|"horizontal"| X000919
    X000920["literal | moved"]
    E000899 -->|"field"| X000920
    X000921["literal | True"]
    E000899 -->|"value"| X000921
    E000922["effect[4]: emit_event"]
    A000795 --> E000922
    X000923["literal | piece.castled"]
    E000922 -->|"name"| X000923
    E000924["effect[5]: advance_turn"]
    A000795 --> E000924
    A000925["chess: king.castle_queen | command | phase:turn"]
    F043 -.-> A000925
    X000926["and"]
    A000925 -->|"condition"| X000926
    X000927["not"]
    X000926 -->|"values[0]"| X000927
    X000928["field"]
    X000927 -->|"value"| X000928
    X000929["context | self"]
    X000928 -->|"entity"| X000929
    X000930["literal | moved"]
    X000928 -->|"key"| X000930
    X000931["is_present"]
    X000926 -->|"values[1]"| X000931
    X000932["first"]
    X000931 -->|"value"| X000932
    X000933["filter"]
    X000932 -->|"items"| X000933
    X000934["entities_of_type"]
    X000933 -->|"items"| X000934
    X000935["literal | rook"]
    X000934 -->|"entity_type"| X000935
    X000936["literal | r"]
    X000933 -->|"variable"| X000936
    X000937["and"]
    X000933 -->|"predicate"| X000937
    X000938["eq"]
    X000937 -->|"values[0]"| X000938
    X000939["owner"]
    X000938 -->|"a"| X000939
    X000940["context | local.r"]
    X000939 -->|"entity"| X000940
    X000941["context | actor"]
    X000938 -->|"b"| X000941
    X000942["not"]
    X000937 -->|"values[1]"| X000942
    X000943["field"]
    X000942 -->|"value"| X000943
    X000944["context | local.r"]
    X000943 -->|"entity"| X000944
    X000945["literal | moved"]
    X000943 -->|"key"| X000945
    X000946["eq"]
    X000937 -->|"values[2]"| X000946
    X000947["entity_location"]
    X000946 -->|"a"| X000947
    X000948["context | local.r"]
    X000947 -->|"entity"| X000948
    X000949["grid_edge"]
    X000946 -->|"b"| X000949
    X000950["context | self"]
    X000949 -->|"entity"| X000950
    X000951["literal | left"]
    X000949 -->|"horizontal"| X000951
    X000952["path_clear"]
    X000926 -->|"values[2]"| X000952
    X000953["grid_between"]
    X000952 -->|"nodes"| X000953
    X000954["entity_location"]
    X000953 -->|"first"| X000954
    X000955["context | self"]
    X000954 -->|"entity"| X000955
    X000956["entity_location"]
    X000953 -->|"last"| X000956
    X000957["first"]
    X000956 -->|"entity"| X000957
    X000958["filter"]
    X000957 -->|"items"| X000958
    X000959["entities_of_type"]
    X000958 -->|"items"| X000959
    X000960["literal | rook"]
    X000959 -->|"entity_type"| X000960
    X000961["literal | r"]
    X000958 -->|"variable"| X000961
    X000962["and"]
    X000958 -->|"predicate"| X000962
    X000963["eq"]
    X000962 -->|"values[0]"| X000963
    X000964["owner"]
    X000963 -->|"a"| X000964
    X000965["context | local.r"]
    X000964 -->|"entity"| X000965
    X000966["context | actor"]
    X000963 -->|"b"| X000966
    X000967["not"]
    X000962 -->|"values[1]"| X000967
    X000968["field"]
    X000967 -->|"value"| X000968
    X000969["context | local.r"]
    X000968 -->|"entity"| X000969
    X000970["literal | moved"]
    X000968 -->|"key"| X000970
    X000971["eq"]
    X000962 -->|"values[2]"| X000971
    X000972["entity_location"]
    X000971 -->|"a"| X000972
    X000973["context | local.r"]
    X000972 -->|"entity"| X000973
    X000974["grid_edge"]
    X000971 -->|"b"| X000974
    X000975["context | self"]
    X000974 -->|"entity"| X000975
    X000976["literal | left"]
    X000974 -->|"horizontal"| X000976
    X000977["none_match"]
    X000926 -->|"values[3]"| X000977
    X000978["list"]
    X000977 -->|"items"| X000978
    X000979["entity_location"]
    X000978 -->|"values[0]"| X000979
    X000980["context | self"]
    X000979 -->|"entity"| X000980
    X000981["grid_offset"]
    X000978 -->|"values[1]"| X000981
    X000982["context | self"]
    X000981 -->|"entity"| X000982
    X000983["literal | 0"]
    X000981 -->|"row"| X000983
    X000984["literal | -1"]
    X000981 -->|"column"| X000984
    X000985["grid_offset"]
    X000978 -->|"values[2]"| X000985
    X000986["context | self"]
    X000985 -->|"entity"| X000986
    X000987["literal | 0"]
    X000985 -->|"row"| X000987
    X000988["literal | -2"]
    X000985 -->|"column"| X000988
    X000989["literal | square"]
    X000977 -->|"variable"| X000989
    X000990["attacked_node"]
    X000977 -->|"predicate"| X000990
    X000991["context | local.square"]
    X000990 -->|"node"| X000991
    X000992["opponents"]
    X000990 -->|"by"| X000992
    X000993["context | actor"]
    X000992 -->|"participant"| X000993
    E000994["effect[0]: move_entity"]
    A000925 --> E000994
    X000995["context | self"]
    E000994 -->|"entity"| X000995
    X000996["grid_offset"]
    E000994 -->|"destination"| X000996
    X000997["context | self"]
    X000996 -->|"entity"| X000997
    X000998["literal | 0"]
    X000996 -->|"row"| X000998
    X000999["literal | -2"]
    X000996 -->|"column"| X000999
    E001000["effect[1]: move_entity"]
    A000925 --> E001000
    X001001["first"]
    E001000 -->|"entity"| X001001
    X001002["filter"]
    X001001 -->|"items"| X001002
    X001003["entities_of_type"]
    X001002 -->|"items"| X001003
    X001004["literal | rook"]
    X001003 -->|"entity_type"| X001004
    X001005["literal | r"]
    X001002 -->|"variable"| X001005
    X001006["and"]
    X001002 -->|"predicate"| X001006
    X001007["eq"]
    X001006 -->|"values[0]"| X001007
    X001008["owner"]
    X001007 -->|"a"| X001008
    X001009["context | local.r"]
    X001008 -->|"entity"| X001009
    X001010["context | actor"]
    X001007 -->|"b"| X001010
    X001011["not"]
    X001006 -->|"values[1]"| X001011
    X001012["field"]
    X001011 -->|"value"| X001012
    X001013["context | local.r"]
    X001012 -->|"entity"| X001013
    X001014["literal | moved"]
    X001012 -->|"key"| X001014
    X001015["eq"]
    X001006 -->|"values[2]"| X001015
    X001016["entity_location"]
    X001015 -->|"a"| X001016
    X001017["context | local.r"]
    X001016 -->|"entity"| X001017
    X001018["grid_edge"]
    X001015 -->|"b"| X001018
    X001019["context | self"]
    X001018 -->|"entity"| X001019
    X001020["literal | left"]
    X001018 -->|"horizontal"| X001020
    X001021["grid_offset"]
    E001000 -->|"destination"| X001021
    X001022["context | self"]
    X001021 -->|"entity"| X001022
    X001023["literal | 0"]
    X001021 -->|"row"| X001023
    X001024["literal | -1"]
    X001021 -->|"column"| X001024
    E001025["effect[2]: set_field"]
    A000925 --> E001025
    X001026["context | self"]
    E001025 -->|"entity"| X001026
    X001027["literal | moved"]
    E001025 -->|"field"| X001027
    X001028["literal | True"]
    E001025 -->|"value"| X001028
    E001029["effect[3]: set_field"]
    A000925 --> E001029
    X001030["first"]
    E001029 -->|"entity"| X001030
    X001031["filter"]
    X001030 -->|"items"| X001031
    X001032["entities_of_type"]
    X001031 -->|"items"| X001032
    X001033["literal | rook"]
    X001032 -->|"entity_type"| X001033
    X001034["literal | r"]
    X001031 -->|"variable"| X001034
    X001035["and"]
    X001031 -->|"predicate"| X001035
    X001036["eq"]
    X001035 -->|"values[0]"| X001036
    X001037["owner"]
    X001036 -->|"a"| X001037
    X001038["context | local.r"]
    X001037 -->|"entity"| X001038
    X001039["context | actor"]
    X001036 -->|"b"| X001039
    X001040["not"]
    X001035 -->|"values[1]"| X001040
    X001041["field"]
    X001040 -->|"value"| X001041
    X001042["context | local.r"]
    X001041 -->|"entity"| X001042
    X001043["literal | moved"]
    X001041 -->|"key"| X001043
    X001044["eq"]
    X001035 -->|"values[2]"| X001044
    X001045["entity_location"]
    X001044 -->|"a"| X001045
    X001046["context | local.r"]
    X001045 -->|"entity"| X001046
    X001047["grid_edge"]
    X001044 -->|"b"| X001047
    X001048["context | self"]
    X001047 -->|"entity"| X001048
    X001049["literal | left"]
    X001047 -->|"horizontal"| X001049
    X001050["literal | moved"]
    E001029 -->|"field"| X001050
    X001051["literal | True"]
    E001029 -->|"value"| X001051
    E001052["effect[4]: emit_event"]
    A000925 --> E001052
    X001053["literal | piece.castled"]
    E001052 -->|"name"| X001053
    E001054["effect[5]: advance_turn"]
    A000925 --> E001054
    A001055["chess: pawn.en_passant | command | phase:turn"]
    F043 -.-> A001055
    X001056["and"]
    A001055 -->|"condition"| X001056
    X001057["eq"]
    X001056 -->|"values[0]"| X001057
    X001058["context | argument.to"]
    X001057 -->|"a"| X001058
    X001059["field"]
    X001057 -->|"b"| X001059
    X001060["context | game"]
    X001059 -->|"entity"| X001060
    X001061["literal | en_passant"]
    X001059 -->|"key"| X001061
    X001062["is_present"]
    X001056 -->|"values[1]"| X001062
    X001063["first"]
    X001062 -->|"value"| X001063
    X001064["filter"]
    X001063 -->|"items"| X001064
    X001065["entities_of_type"]
    X001064 -->|"items"| X001065
    X001066["literal | pawn"]
    X001065 -->|"entity_type"| X001066
    X001067["literal | p"]
    X001064 -->|"variable"| X001067
    X001068["and"]
    X001064 -->|"predicate"| X001068
    X001069["not"]
    X001068 -->|"values[0]"| X001069
    X001070["eq"]
    X001069 -->|"value"| X001070
    X001071["owner"]
    X001070 -->|"a"| X001071
    X001072["context | local.p"]
    X001071 -->|"entity"| X001072
    X001073["context | actor"]
    X001070 -->|"b"| X001073
    X001074["eq"]
    X001068 -->|"values[1]"| X001074
    X001075["entity_location"]
    X001074 -->|"a"| X001075
    X001076["context | local.p"]
    X001075 -->|"entity"| X001076
    X001077["grid_offset"]
    X001074 -->|"b"| X001077
    X001078["context | argument.to"]
    X001077 -->|"entity"| X001078
    X001079["negate"]
    X001077 -->|"row"| X001079
    X001080["owner_orientation"]
    X001079 -->|"value"| X001080
    X001081["context | self"]
    X001080 -->|"entity"| X001081
    X001082["literal | 0"]
    X001077 -->|"column"| X001082
    E001083["effect[0]: remove_entity"]
    A001055 --> E001083
    X001084["first"]
    E001083 -->|"entity"| X001084
    X001085["filter"]
    X001084 -->|"items"| X001085
    X001086["entities_of_type"]
    X001085 -->|"items"| X001086
    X001087["literal | pawn"]
    X001086 -->|"entity_type"| X001087
    X001088["literal | p"]
    X001085 -->|"variable"| X001088
    X001089["and"]
    X001085 -->|"predicate"| X001089
    X001090["not"]
    X001089 -->|"values[0]"| X001090
    X001091["eq"]
    X001090 -->|"value"| X001091
    X001092["owner"]
    X001091 -->|"a"| X001092
    X001093["context | local.p"]
    X001092 -->|"entity"| X001093
    X001094["context | actor"]
    X001091 -->|"b"| X001094
    X001095["eq"]
    X001089 -->|"values[1]"| X001095
    X001096["entity_location"]
    X001095 -->|"a"| X001096
    X001097["context | local.p"]
    X001096 -->|"entity"| X001097
    X001098["grid_offset"]
    X001095 -->|"b"| X001098
    X001099["context | argument.to"]
    X001098 -->|"entity"| X001099
    X001100["negate"]
    X001098 -->|"row"| X001100
    X001101["owner_orientation"]
    X001100 -->|"value"| X001101
    X001102["context | self"]
    X001101 -->|"entity"| X001102
    X001103["literal | 0"]
    X001098 -->|"column"| X001103
    E001104["effect[1]: move_entity"]
    A001055 --> E001104
    X001105["context | self"]
    E001104 -->|"entity"| X001105
    X001106["context | argument.to"]
    E001104 -->|"destination"| X001106
    E001107["effect[2]: set_field"]
    A001055 --> E001107
    X001108["context | self"]
    E001107 -->|"entity"| X001108
    X001109["literal | moved"]
    E001107 -->|"field"| X001109
    X001110["literal | True"]
    E001107 -->|"value"| X001110
    E001111["effect[3]: emit_event"]
    A001055 --> E001111
    X001112["literal | piece.captured"]
    E001111 -->|"name"| X001112
    E001113["effect[4]: advance_turn"]
    A001055 --> E001113
    A001114["chess: checkmate.evaluate | hook | phase:* | hook:game.evaluate"]
    F043 -.-> A001114
    X001115["and"]
    A001114 -->|"condition"| X001115
    X001116["attacked_node"]
    X001115 -->|"values[0]"| X001116
    X001117["entity_location"]
    X001116 -->|"node"| X001117
    X001118["first"]
    X001117 -->|"entity"| X001118
    X001119["filter"]
    X001118 -->|"items"| X001119
    X001120["entities_of_type"]
    X001119 -->|"items"| X001120
    X001121["literal | king"]
    X001120 -->|"entity_type"| X001121
    X001122["literal | e"]
    X001119 -->|"variable"| X001122
    X001123["eq"]
    X001119 -->|"predicate"| X001123
    X001124["owner"]
    X001123 -->|"a"| X001124
    X001125["context | local.e"]
    X001124 -->|"entity"| X001125
    X001126["next_participant"]
    X001123 -->|"b"| X001126
    X001127["context | active_participant"]
    X001126 -->|"participant"| X001127
    X001128["opponents"]
    X001116 -->|"by"| X001128
    X001129["next_participant"]
    X001128 -->|"participant"| X001129
    X001130["context | active_participant"]
    X001129 -->|"participant"| X001130
    X001131["eq"]
    X001115 -->|"values[1]"| X001131
    X001132["available_action_count"]
    X001131 -->|"a"| X001132
    X001133["next_participant"]
    X001132 -->|"actor"| X001133
    X001134["context | active_participant"]
    X001133 -->|"participant"| X001134
    X001135["literal | 0"]
    X001131 -->|"b"| X001135
    E001136["effect[0]: complete_objective"]
    A001114 --> E001136
    X001137["context | self"]
    E001136 -->|"entity"| X001137
    E001138["effect[1]: finish_game"]
    A001114 --> E001138
    X001139["literal | victory"]
    E001138 -->|"result"| X001139
    A001140["chess: stalemate.evaluate | hook | phase:* | hook:game.evaluate"]
    F043 -.-> A001140
    X001141["and"]
    A001140 -->|"condition"| X001141
    X001142["not"]
    X001141 -->|"values[0]"| X001142
    X001143["attacked_node"]
    X001142 -->|"value"| X001143
    X001144["entity_location"]
    X001143 -->|"node"| X001144
    X001145["first"]
    X001144 -->|"entity"| X001145
    X001146["filter"]
    X001145 -->|"items"| X001146
    X001147["entities_of_type"]
    X001146 -->|"items"| X001147
    X001148["literal | king"]
    X001147 -->|"entity_type"| X001148
    X001149["literal | e"]
    X001146 -->|"variable"| X001149
    X001150["eq"]
    X001146 -->|"predicate"| X001150
    X001151["owner"]
    X001150 -->|"a"| X001151
    X001152["context | local.e"]
    X001151 -->|"entity"| X001152
    X001153["next_participant"]
    X001150 -->|"b"| X001153
    X001154["context | active_participant"]
    X001153 -->|"participant"| X001154
    X001155["opponents"]
    X001143 -->|"by"| X001155
    X001156["next_participant"]
    X001155 -->|"participant"| X001156
    X001157["context | active_participant"]
    X001156 -->|"participant"| X001157
    X001158["eq"]
    X001141 -->|"values[1]"| X001158
    X001159["available_action_count"]
    X001158 -->|"a"| X001159
    X001160["next_participant"]
    X001159 -->|"actor"| X001160
    X001161["context | active_participant"]
    X001160 -->|"participant"| X001161
    X001162["literal | 0"]
    X001158 -->|"b"| X001162
    E001163["effect[0]: complete_objective"]
    A001140 --> E001163
    X001164["context | self"]
    E001163 -->|"entity"| X001164
    E001165["effect[1]: finish_game"]
    A001140 --> E001165
    X001166["literal | draw"]
    E001165 -->|"result"| X001166
    A001167["chess: dead_position.evaluate | hook | phase:* | hook:game.evaluate"]
    F043 -.-> A001167
    X001168["no_reachable_terminal"]
    A001167 -->|"condition"| X001168
    X001169["context | proposed_state"]
    X001168 -->|"state"| X001169
    X001170["literal | checkmate"]
    X001168 -->|"terminal"| X001170
    X001171["literal | 250000"]
    X001168 -->|"max_states"| X001171
    E001172["effect[0]: complete_objective"]
    A001167 --> E001172
    X001173["context | self"]
    E001172 -->|"entity"| X001173
    E001174["effect[1]: finish_game"]
    A001167 --> E001174
    X001175["literal | draw"]
    E001174 -->|"result"| X001175
    A001176["chess: repetition_draw.evaluate | hook | phase:* | hook:game.evaluate"]
    F043 -.-> A001176
    X001177["gte"]
    A001176 -->|"condition"| X001177
    X001178["position_occurrences"]
    X001177 -->|"a"| X001178
    X001179["context | proposed_state"]
    X001178 -->|"state"| X001179
    X001180["literal | 3"]
    X001177 -->|"b"| X001180
    E001181["effect[0]: complete_objective"]
    A001176 --> E001181
    X001182["context | self"]
    E001181 -->|"entity"| X001182
    E001183["effect[1]: finish_game"]
    A001176 --> E001183
    X001184["literal | draw"]
    E001183 -->|"result"| X001184
    A001185["chess: move_count_draw.evaluate | hook | phase:* | hook:game.evaluate"]
    F043 -.-> A001185
    X001186["gte"]
    A001185 -->|"condition"| X001186
    X001187["get_state"]
    X001186 -->|"a"| X001187
    X001188["context | proposed_state"]
    X001187 -->|"state"| X001188
    X001189["literal | halfmove_clock"]
    X001187 -->|"field"| X001189
    X001190["literal | 100"]
    X001186 -->|"b"| X001190
    E001191["effect[0]: complete_objective"]
    A001185 --> E001191
    X001192["context | self"]
    E001191 -->|"entity"| X001192
    E001193["effect[1]: finish_game"]
    A001185 --> E001193
    X001194["literal | draw"]
    E001193 -->|"result"| X001194
    A001195["chess: timeout.evaluate | hook | phase:* | hook:game.evaluate"]
    F043 -.-> A001195
    X001196["clock_expired"]
    A001195 -->|"condition"| X001196
    X001197["context | proposed_state"]
    X001196 -->|"state"| X001197
    E001198["effect[0]: complete_objective"]
    A001195 --> E001198
    X001199["context | self"]
    E001198 -->|"entity"| X001199
    E001200["effect[1]: finish_game"]
    A001195 --> E001200
    X001201["literal | computed"]
    E001200 -->|"result"| X001201
    A001202["chess: capture_quest.count | hook | phase:* | hook:objective.evaluate"]
    F043 -.-> A001202
    X001203["eq"]
    A001202 -->|"condition"| X001203
    X001204["event_attribute"]
    X001203 -->|"a"| X001204
    X001205["context | event"]
    X001204 -->|"event"| X001205
    X001206["literal | kind"]
    X001204 -->|"attribute"| X001206
    X001207["literal | piece.captured"]
    X001203 -->|"b"| X001207
    E001208["effect[0]: increment_field"]
    A001202 --> E001208
    X001209["context | self"]
    E001208 -->|"entity"| X001209
    X001210["literal | progress"]
    E001208 -->|"field"| X001210
    X001211["literal | 1"]
    E001208 -->|"amount"| X001211
    E001212["effect[1]: complete_objective"]
    A001202 --> E001212
    X001213["gte"]
    E001212 -->|"when"| X001213
    X001214["field"]
    X001213 -->|"a"| X001214
    X001215["context | self"]
    X001214 -->|"entity"| X001215
    X001216["literal | progress"]
    X001214 -->|"key"| X001216
    X001217["field"]
    X001213 -->|"b"| X001217
    X001218["context | self"]
    X001217 -->|"entity"| X001218
    X001219["literal | target"]
    X001217 -->|"key"| X001219
    X001220["context | self"]
    E001212 -->|"entity"| X001220
    A001221["chess: promotion_quest.count | hook | phase:* | hook:objective.evaluate"]
    F043 -.-> A001221
    X001222["eq"]
    A001221 -->|"condition"| X001222
    X001223["event_attribute"]
    X001222 -->|"a"| X001223
    X001224["context | event"]
    X001223 -->|"event"| X001224
    X001225["literal | kind"]
    X001223 -->|"attribute"| X001225
    X001226["literal | piece.promoted"]
    X001222 -->|"b"| X001226
    E001227["effect[0]: increment_field"]
    A001221 --> E001227
    X001228["context | self"]
    E001227 -->|"entity"| X001228
    X001229["literal | progress"]
    E001227 -->|"field"| X001229
    X001230["literal | 1"]
    E001227 -->|"amount"| X001230
    E001231["effect[1]: complete_objective"]
    A001221 --> E001231
    X001232["gte"]
    E001231 -->|"when"| X001232
    X001233["field"]
    X001232 -->|"a"| X001233
    X001234["context | self"]
    X001233 -->|"entity"| X001234
    X001235["literal | progress"]
    X001233 -->|"key"| X001235
    X001236["field"]
    X001232 -->|"b"| X001236
    X001237["context | self"]
    X001236 -->|"entity"| X001237
    X001238["literal | target"]
    X001236 -->|"key"| X001238
    X001239["context | self"]
    E001231 -->|"entity"| X001239
    A001240["chess: castling_quest.count | hook | phase:* | hook:objective.evaluate"]
    F043 -.-> A001240
    X001241["eq"]
    A001240 -->|"condition"| X001241
    X001242["event_attribute"]
    X001241 -->|"a"| X001242
    X001243["context | event"]
    X001242 -->|"event"| X001243
    X001244["literal | kind"]
    X001242 -->|"attribute"| X001244
    X001245["literal | piece.castled"]
    X001241 -->|"b"| X001245
    E001246["effect[0]: increment_field"]
    A001240 --> E001246
    X001247["context | self"]
    E001246 -->|"entity"| X001247
    X001248["literal | progress"]
    E001246 -->|"field"| X001248
    X001249["literal | 1"]
    E001246 -->|"amount"| X001249
    E001250["effect[1]: complete_objective"]
    A001240 --> E001250
    X001251["gte"]
    E001250 -->|"when"| X001251
    X001252["field"]
    X001251 -->|"a"| X001252
    X001253["context | self"]
    X001252 -->|"entity"| X001253
    X001254["literal | progress"]
    X001252 -->|"key"| X001254
    X001255["field"]
    X001251 -->|"b"| X001255
    X001256["context | self"]
    X001255 -->|"entity"| X001256
    X001257["literal | target"]
    X001255 -->|"key"| X001257
    X001258["context | self"]
    E001250 -->|"entity"| X001258
    A001259["english-draughts: man.step | command | phase:turn"]
    F044 -.-> A001259
    X001260["and"]
    A001259 -->|"condition"| X001260
    X001261["is_active"]
    X001260 -->|"values[0]"| X001261
    X001262["context | actor"]
    X001261 -->|"participant"| X001262
    X001263["contains"]
    X001260 -->|"values[1]"| X001263
    X001264["reachable_grid_nodes"]
    X001263 -->|"items"| X001264
    X001265["context | self"]
    X001264 -->|"entity"| X001265
    X001266["list"]
    X001264 -->|"directions"| X001266
    X001267["vector"]
    X001266 -->|"values[0]"| X001267
    X001268["literal | 1"]
    X001267 -->|"row"| X001268
    X001269["literal | -1"]
    X001267 -->|"column"| X001269
    X001270["vector"]
    X001266 -->|"values[1]"| X001270
    X001271["literal | 1"]
    X001270 -->|"row"| X001271
    X001272["literal | 1"]
    X001270 -->|"column"| X001272
    X001273["literal | 1"]
    X001264 -->|"max_steps"| X001273
    X001274["literal | False"]
    X001264 -->|"leap"| X001274
    X001275["owner_orientation"]
    X001264 -->|"orientation"| X001275
    X001276["context | self"]
    X001275 -->|"entity"| X001276
    X001277["literal | empty"]
    X001264 -->|"target_occupancy"| X001277
    X001278["context | observed_state"]
    X001264 -->|"state"| X001278
    X001279["context | argument.to"]
    X001263 -->|"value"| X001279
    X001280["not"]
    X001260 -->|"values[2]"| X001280
    X001281["any_match"]
    X001280 -->|"value"| X001281
    X001282["participant_entities"]
    X001281 -->|"items"| X001282
    X001283["context | actor"]
    X001282 -->|"participant"| X001283
    X001284["literal | piece"]
    X001281 -->|"variable"| X001284
    X001285["gt"]
    X001281 -->|"predicate"| X001285
    X001286["count"]
    X001285 -->|"a"| X001286
    X001287["traverse_paths"]
    X001286 -->|"items"| X001287
    X001288["context | local.piece"]
    X001287 -->|"entity"| X001288
    X001289["jump_landing_steps"]
    X001287 -->|"step_generator"| X001289
    X001290["context | local.piece"]
    X001289 -->|"entity"| X001290
    X001291["list"]
    X001289 -->|"directions"| X001291
    X001292["vector"]
    X001291 -->|"values[0]"| X001292
    X001293["literal | 1"]
    X001292 -->|"row"| X001293
    X001294["literal | -1"]
    X001292 -->|"column"| X001294
    X001295["vector"]
    X001291 -->|"values[1]"| X001295
    X001296["literal | 1"]
    X001295 -->|"row"| X001296
    X001297["literal | 1"]
    X001295 -->|"column"| X001297
    X001298["owner_orientation"]
    X001289 -->|"orientation"| X001298
    X001299["context | local.piece"]
    X001298 -->|"entity"| X001299
    X001300["literal | False"]
    X001289 -->|"flying"| X001300
    X001301["literal | 2"]
    X001289 -->|"max_flight"| X001301
    X001302["literal | empty"]
    X001289 -->|"target_occupancy"| X001302
    X001303["literal | opponent"]
    X001289 -->|"jumped_occupancy"| X001303
    X001304["literal | 40"]
    X001287 -->|"max_depth"| X001304
    X001305["literal | False"]
    X001287 -->|"captured_blockers"| X001305
    X001306["literal | True"]
    X001287 -->|"no_repeat_capture"| X001306
    X001307["literal | True"]
    X001287 -->|"stop_on_crowning"| X001307
    X001308["literal | 0"]
    X001285 -->|"b"| X001308
    E001309["effect[0]: move_entity"]
    A001259 --> E001309
    X001310["context | self"]
    E001309 -->|"entity"| X001310
    X001311["context | argument.to"]
    E001309 -->|"destination"| X001311
    E001312["effect[1]: change_entity_type"]
    A001259 --> E001312
    X001313["on_board_edge"]
    E001312 -->|"when"| X001313
    X001314["context | self"]
    X001313 -->|"entity"| X001314
    X001315["literal | promotion"]
    X001313 -->|"edge"| X001315
    X001316["context | self"]
    E001312 -->|"entity"| X001316
    X001317["literal | king"]
    E001312 -->|"to"| X001317
    E001318["effect[2]: advance_turn"]
    A001259 --> E001318
    A001319["english-draughts: man.capture | command | phase:turn"]
    F044 -.-> A001319
    X001320["and"]
    A001319 -->|"condition"| X001320
    X001321["is_active"]
    X001320 -->|"values[0]"| X001321
    X001322["context | actor"]
    X001321 -->|"participant"| X001322
    X001323["contains"]
    X001320 -->|"values[1]"| X001323
    X001324["traverse_paths"]
    X001323 -->|"items"| X001324
    X001325["context | self"]
    X001324 -->|"entity"| X001325
    X001326["jump_landing_steps"]
    X001324 -->|"step_generator"| X001326
    X001327["context | self"]
    X001326 -->|"entity"| X001327
    X001328["list"]
    X001326 -->|"directions"| X001328
    X001329["vector"]
    X001328 -->|"values[0]"| X001329
    X001330["literal | 1"]
    X001329 -->|"row"| X001330
    X001331["literal | -1"]
    X001329 -->|"column"| X001331
    X001332["vector"]
    X001328 -->|"values[1]"| X001332
    X001333["literal | 1"]
    X001332 -->|"row"| X001333
    X001334["literal | 1"]
    X001332 -->|"column"| X001334
    X001335["owner_orientation"]
    X001326 -->|"orientation"| X001335
    X001336["context | self"]
    X001335 -->|"entity"| X001336
    X001337["literal | False"]
    X001326 -->|"flying"| X001337
    X001338["literal | 2"]
    X001326 -->|"max_flight"| X001338
    X001339["literal | empty"]
    X001326 -->|"target_occupancy"| X001339
    X001340["literal | opponent"]
    X001326 -->|"jumped_occupancy"| X001340
    X001341["literal | 40"]
    X001324 -->|"max_depth"| X001341
    X001342["literal | False"]
    X001324 -->|"captured_blockers"| X001342
    X001343["literal | True"]
    X001324 -->|"no_repeat_capture"| X001343
    X001344["literal | True"]
    X001324 -->|"stop_on_crowning"| X001344
    X001345["context | argument.path"]
    X001323 -->|"value"| X001345
    X001346["literal | True"]
    X001320 -->|"values[2]"| X001346
    E001347["effect[0]: apply_path"]
    A001319 --> E001347
    X001348["context | self"]
    E001347 -->|"entity"| X001348
    X001349["context | argument.path"]
    E001347 -->|"path"| X001349
    X001350["literal | True"]
    E001347 -->|"remove_traversed_entities"| X001350
    E001351["effect[1]: change_entity_type"]
    A001319 --> E001351
    X001352["on_board_edge"]
    E001351 -->|"when"| X001352
    X001353["context | self"]
    X001352 -->|"entity"| X001353
    X001354["literal | promotion"]
    X001352 -->|"edge"| X001354
    X001355["context | self"]
    E001351 -->|"entity"| X001355
    X001356["literal | king"]
    E001351 -->|"to"| X001356
    E001357["effect[2]: emit_event"]
    A001319 --> E001357
    X001358["literal | piece.captured"]
    E001357 -->|"name"| X001358
    E001359["effect[3]: advance_turn"]
    A001319 --> E001359
    A001360["english-draughts: man.candidates | hook | phase:turn | hook:action.generate"]
    F044 -.-> A001360
    X001361["literal | True"]
    A001360 -->|"condition"| X001361
    X001362["traverse_paths"]
    A001360 -->|"iterator"| X001362
    X001363["context | self"]
    X001362 -->|"entity"| X001363
    X001364["jump_landing_steps"]
    X001362 -->|"step_generator"| X001364
    X001365["context | self"]
    X001364 -->|"entity"| X001365
    X001366["list"]
    X001364 -->|"directions"| X001366
    X001367["vector"]
    X001366 -->|"values[0]"| X001367
    X001368["literal | 1"]
    X001367 -->|"row"| X001368
    X001369["literal | -1"]
    X001367 -->|"column"| X001369
    X001370["vector"]
    X001366 -->|"values[1]"| X001370
    X001371["literal | 1"]
    X001370 -->|"row"| X001371
    X001372["literal | 1"]
    X001370 -->|"column"| X001372
    X001373["owner_orientation"]
    X001364 -->|"orientation"| X001373
    X001374["context | self"]
    X001373 -->|"entity"| X001374
    X001375["literal | False"]
    X001364 -->|"flying"| X001375
    X001376["literal | 2"]
    X001364 -->|"max_flight"| X001376
    X001377["literal | empty"]
    X001364 -->|"target_occupancy"| X001377
    X001378["literal | opponent"]
    X001364 -->|"jumped_occupancy"| X001378
    X001379["literal | 40"]
    X001362 -->|"max_depth"| X001379
    X001380["literal | False"]
    X001362 -->|"captured_blockers"| X001380
    X001381["literal | True"]
    X001362 -->|"no_repeat_capture"| X001381
    X001382["literal | True"]
    X001362 -->|"stop_on_crowning"| X001382
    E001383["effect[0]: emit_candidate"]
    A001360 --> E001383
    X001384["context | self"]
    E001383 -->|"entity"| X001384
    X001385["context | candidate"]
    E001383 -->|"path"| X001385
    A001386["english-draughts: king.step | command | phase:turn"]
    F044 -.-> A001386
    X001387["and"]
    A001386 -->|"condition"| X001387
    X001388["is_active"]
    X001387 -->|"values[0]"| X001388
    X001389["context | actor"]
    X001388 -->|"participant"| X001389
    X001390["contains"]
    X001387 -->|"values[1]"| X001390
    X001391["reachable_grid_nodes"]
    X001390 -->|"items"| X001391
    X001392["context | self"]
    X001391 -->|"entity"| X001392
    X001393["list"]
    X001391 -->|"directions"| X001393
    X001394["vector"]
    X001393 -->|"values[0]"| X001394
    X001395["literal | 1"]
    X001394 -->|"row"| X001395
    X001396["literal | -1"]
    X001394 -->|"column"| X001396
    X001397["vector"]
    X001393 -->|"values[1]"| X001397
    X001398["literal | 1"]
    X001397 -->|"row"| X001398
    X001399["literal | 1"]
    X001397 -->|"column"| X001399
    X001400["vector"]
    X001393 -->|"values[2]"| X001400
    X001401["literal | -1"]
    X001400 -->|"row"| X001401
    X001402["literal | -1"]
    X001400 -->|"column"| X001402
    X001403["vector"]
    X001393 -->|"values[3]"| X001403
    X001404["literal | -1"]
    X001403 -->|"row"| X001404
    X001405["literal | 1"]
    X001403 -->|"column"| X001405
    X001406["literal | 1"]
    X001391 -->|"max_steps"| X001406
    X001407["literal | False"]
    X001391 -->|"leap"| X001407
    X001408["owner_orientation"]
    X001391 -->|"orientation"| X001408
    X001409["context | self"]
    X001408 -->|"entity"| X001409
    X001410["literal | empty"]
    X001391 -->|"target_occupancy"| X001410
    X001411["context | observed_state"]
    X001391 -->|"state"| X001411
    X001412["context | argument.to"]
    X001390 -->|"value"| X001412
    X001413["not"]
    X001387 -->|"values[2]"| X001413
    X001414["any_match"]
    X001413 -->|"value"| X001414
    X001415["participant_entities"]
    X001414 -->|"items"| X001415
    X001416["context | actor"]
    X001415 -->|"participant"| X001416
    X001417["literal | piece"]
    X001414 -->|"variable"| X001417
    X001418["gt"]
    X001414 -->|"predicate"| X001418
    X001419["count"]
    X001418 -->|"a"| X001419
    X001420["traverse_paths"]
    X001419 -->|"items"| X001420
    X001421["context | local.piece"]
    X001420 -->|"entity"| X001421
    X001422["jump_landing_steps"]
    X001420 -->|"step_generator"| X001422
    X001423["context | local.piece"]
    X001422 -->|"entity"| X001423
    X001424["list"]
    X001422 -->|"directions"| X001424
    X001425["vector"]
    X001424 -->|"values[0]"| X001425
    X001426["literal | 1"]
    X001425 -->|"row"| X001426
    X001427["literal | -1"]
    X001425 -->|"column"| X001427
    X001428["vector"]
    X001424 -->|"values[1]"| X001428
    X001429["literal | 1"]
    X001428 -->|"row"| X001429
    X001430["literal | 1"]
    X001428 -->|"column"| X001430
    X001431["owner_orientation"]
    X001422 -->|"orientation"| X001431
    X001432["context | local.piece"]
    X001431 -->|"entity"| X001432
    X001433["literal | False"]
    X001422 -->|"flying"| X001433
    X001434["literal | 2"]
    X001422 -->|"max_flight"| X001434
    X001435["literal | empty"]
    X001422 -->|"target_occupancy"| X001435
    X001436["literal | opponent"]
    X001422 -->|"jumped_occupancy"| X001436
    X001437["literal | 40"]
    X001420 -->|"max_depth"| X001437
    X001438["literal | False"]
    X001420 -->|"captured_blockers"| X001438
    X001439["literal | True"]
    X001420 -->|"no_repeat_capture"| X001439
    X001440["literal | True"]
    X001420 -->|"stop_on_crowning"| X001440
    X001441["literal | 0"]
    X001418 -->|"b"| X001441
    E001442["effect[0]: move_entity"]
    A001386 --> E001442
    X001443["context | self"]
    E001442 -->|"entity"| X001443
    X001444["context | argument.to"]
    E001442 -->|"destination"| X001444
    E001445["effect[1]: advance_turn"]
    A001386 --> E001445
    A001446["english-draughts: king.capture | command | phase:turn"]
    F044 -.-> A001446
    X001447["and"]
    A001446 -->|"condition"| X001447
    X001448["is_active"]
    X001447 -->|"values[0]"| X001448
    X001449["context | actor"]
    X001448 -->|"participant"| X001449
    X001450["contains"]
    X001447 -->|"values[1]"| X001450
    X001451["traverse_paths"]
    X001450 -->|"items"| X001451
    X001452["context | self"]
    X001451 -->|"entity"| X001452
    X001453["jump_landing_steps"]
    X001451 -->|"step_generator"| X001453
    X001454["context | self"]
    X001453 -->|"entity"| X001454
    X001455["list"]
    X001453 -->|"directions"| X001455
    X001456["vector"]
    X001455 -->|"values[0]"| X001456
    X001457["literal | 1"]
    X001456 -->|"row"| X001457
    X001458["literal | -1"]
    X001456 -->|"column"| X001458
    X001459["vector"]
    X001455 -->|"values[1]"| X001459
    X001460["literal | 1"]
    X001459 -->|"row"| X001460
    X001461["literal | 1"]
    X001459 -->|"column"| X001461
    X001462["owner_orientation"]
    X001453 -->|"orientation"| X001462
    X001463["context | self"]
    X001462 -->|"entity"| X001463
    X001464["literal | False"]
    X001453 -->|"flying"| X001464
    X001465["literal | 2"]
    X001453 -->|"max_flight"| X001465
    X001466["literal | empty"]
    X001453 -->|"target_occupancy"| X001466
    X001467["literal | opponent"]
    X001453 -->|"jumped_occupancy"| X001467
    X001468["literal | 40"]
    X001451 -->|"max_depth"| X001468
    X001469["literal | False"]
    X001451 -->|"captured_blockers"| X001469
    X001470["literal | True"]
    X001451 -->|"no_repeat_capture"| X001470
    X001471["literal | True"]
    X001451 -->|"stop_on_crowning"| X001471
    X001472["context | argument.path"]
    X001450 -->|"value"| X001472
    X001473["literal | True"]
    X001447 -->|"values[2]"| X001473
    E001474["effect[0]: apply_path"]
    A001446 --> E001474
    X001475["context | self"]
    E001474 -->|"entity"| X001475
    X001476["context | argument.path"]
    E001474 -->|"path"| X001476
    X001477["literal | True"]
    E001474 -->|"remove_traversed_entities"| X001477
    E001478["effect[1]: emit_event"]
    A001446 --> E001478
    X001479["literal | piece.captured"]
    E001478 -->|"name"| X001479
    E001480["effect[2]: advance_turn"]
    A001446 --> E001480
    A001481["english-draughts: king.candidates | hook | phase:turn | hook:action.generate"]
    F044 -.-> A001481
    X001482["literal | True"]
    A001481 -->|"condition"| X001482
    X001483["traverse_paths"]
    A001481 -->|"iterator"| X001483
    X001484["context | self"]
    X001483 -->|"entity"| X001484
    X001485["jump_landing_steps"]
    X001483 -->|"step_generator"| X001485
    X001486["context | self"]
    X001485 -->|"entity"| X001486
    X001487["list"]
    X001485 -->|"directions"| X001487
    X001488["vector"]
    X001487 -->|"values[0]"| X001488
    X001489["literal | 1"]
    X001488 -->|"row"| X001489
    X001490["literal | -1"]
    X001488 -->|"column"| X001490
    X001491["vector"]
    X001487 -->|"values[1]"| X001491
    X001492["literal | 1"]
    X001491 -->|"row"| X001492
    X001493["literal | 1"]
    X001491 -->|"column"| X001493
    X001494["owner_orientation"]
    X001485 -->|"orientation"| X001494
    X001495["context | self"]
    X001494 -->|"entity"| X001495
    X001496["literal | False"]
    X001485 -->|"flying"| X001496
    X001497["literal | 2"]
    X001485 -->|"max_flight"| X001497
    X001498["literal | empty"]
    X001485 -->|"target_occupancy"| X001498
    X001499["literal | opponent"]
    X001485 -->|"jumped_occupancy"| X001499
    X001500["literal | 40"]
    X001483 -->|"max_depth"| X001500
    X001501["literal | False"]
    X001483 -->|"captured_blockers"| X001501
    X001502["literal | True"]
    X001483 -->|"no_repeat_capture"| X001502
    X001503["literal | True"]
    X001483 -->|"stop_on_crowning"| X001503
    E001504["effect[0]: emit_candidate"]
    A001481 --> E001504
    X001505["context | self"]
    E001504 -->|"entity"| X001505
    X001506["context | candidate"]
    E001504 -->|"path"| X001506
    A001507["english-draughts: victory.evaluate | hook | phase:* | hook:game.evaluate"]
    F044 -.-> A001507
    X001508["eq"]
    A001507 -->|"condition"| X001508
    X001509["available_action_count"]
    X001508 -->|"a"| X001509
    X001510["next_participant"]
    X001509 -->|"actor"| X001510
    X001511["context | active_participant"]
    X001510 -->|"participant"| X001511
    X001512["literal | 0"]
    X001508 -->|"b"| X001512
    E001513["effect[0]: complete_objective"]
    A001507 --> E001513
    X001514["context | self"]
    E001513 -->|"entity"| X001514
    E001515["effect[1]: finish_game"]
    A001507 --> E001515
    X001516["literal | victory"]
    E001515 -->|"result"| X001516
    A001517["english-draughts: draw.evaluate | hook | phase:* | hook:game.evaluate"]
    F044 -.-> A001517
    X001518["gte"]
    A001517 -->|"condition"| X001518
    X001519["field"]
    X001518 -->|"a"| X001519
    X001520["context | game"]
    X001519 -->|"entity"| X001520
    X001521["literal | draw_counter"]
    X001519 -->|"key"| X001521
    X001522["literal | 40"]
    X001518 -->|"b"| X001522
    E001523["effect[0]: complete_objective"]
    A001517 --> E001523
    X001524["context | self"]
    E001523 -->|"entity"| X001524
    E001525["effect[1]: finish_game"]
    A001517 --> E001525
    X001526["literal | draw"]
    E001525 -->|"result"| X001526
    A001527["english-draughts: capture_quest.count | hook | phase:* | hook:objective.evaluate"]
    F044 -.-> A001527
    X001528["eq"]
    A001527 -->|"condition"| X001528
    X001529["event_attribute"]
    X001528 -->|"a"| X001529
    X001530["context | event"]
    X001529 -->|"event"| X001530
    X001531["literal | kind"]
    X001529 -->|"attribute"| X001531
    X001532["literal | piece.captured"]
    X001528 -->|"b"| X001532
    E001533["effect[0]: increment_field"]
    A001527 --> E001533
    X001534["context | self"]
    E001533 -->|"entity"| X001534
    X001535["literal | progress"]
    E001533 -->|"field"| X001535
    X001536["literal | 1"]
    E001533 -->|"amount"| X001536
    A001537["international-draughts: man.step | command | phase:turn"]
    F045 -.-> A001537
    X001538["and"]
    A001537 -->|"condition"| X001538
    X001539["is_active"]
    X001538 -->|"values[0]"| X001539
    X001540["context | actor"]
    X001539 -->|"participant"| X001540
    X001541["contains"]
    X001538 -->|"values[1]"| X001541
    X001542["reachable_grid_nodes"]
    X001541 -->|"items"| X001542
    X001543["context | self"]
    X001542 -->|"entity"| X001543
    X001544["list"]
    X001542 -->|"directions"| X001544
    X001545["vector"]
    X001544 -->|"values[0]"| X001545
    X001546["literal | 1"]
    X001545 -->|"row"| X001546
    X001547["literal | -1"]
    X001545 -->|"column"| X001547
    X001548["vector"]
    X001544 -->|"values[1]"| X001548
    X001549["literal | 1"]
    X001548 -->|"row"| X001549
    X001550["literal | 1"]
    X001548 -->|"column"| X001550
    X001551["literal | 1"]
    X001542 -->|"max_steps"| X001551
    X001552["literal | False"]
    X001542 -->|"leap"| X001552
    X001553["owner_orientation"]
    X001542 -->|"orientation"| X001553
    X001554["context | self"]
    X001553 -->|"entity"| X001554
    X001555["literal | empty"]
    X001542 -->|"target_occupancy"| X001555
    X001556["context | observed_state"]
    X001542 -->|"state"| X001556
    X001557["context | argument.to"]
    X001541 -->|"value"| X001557
    X001558["not"]
    X001538 -->|"values[2]"| X001558
    X001559["any_match"]
    X001558 -->|"value"| X001559
    X001560["participant_entities"]
    X001559 -->|"items"| X001560
    X001561["context | actor"]
    X001560 -->|"participant"| X001561
    X001562["literal | piece"]
    X001559 -->|"variable"| X001562
    X001563["gt"]
    X001559 -->|"predicate"| X001563
    X001564["count"]
    X001563 -->|"a"| X001564
    X001565["traverse_paths"]
    X001564 -->|"items"| X001565
    X001566["context | local.piece"]
    X001565 -->|"entity"| X001566
    X001567["jump_landing_steps"]
    X001565 -->|"step_generator"| X001567
    X001568["context | local.piece"]
    X001567 -->|"entity"| X001568
    X001569["list"]
    X001567 -->|"directions"| X001569
    X001570["vector"]
    X001569 -->|"values[0]"| X001570
    X001571["literal | 1"]
    X001570 -->|"row"| X001571
    X001572["literal | -1"]
    X001570 -->|"column"| X001572
    X001573["vector"]
    X001569 -->|"values[1]"| X001573
    X001574["literal | 1"]
    X001573 -->|"row"| X001574
    X001575["literal | 1"]
    X001573 -->|"column"| X001575
    X001576["vector"]
    X001569 -->|"values[2]"| X001576
    X001577["literal | -1"]
    X001576 -->|"row"| X001577
    X001578["literal | -1"]
    X001576 -->|"column"| X001578
    X001579["vector"]
    X001569 -->|"values[3]"| X001579
    X001580["literal | -1"]
    X001579 -->|"row"| X001580
    X001581["literal | 1"]
    X001579 -->|"column"| X001581
    X001582["owner_orientation"]
    X001567 -->|"orientation"| X001582
    X001583["context | local.piece"]
    X001582 -->|"entity"| X001583
    X001584["literal | True"]
    X001567 -->|"flying"| X001584
    X001585["literal | 9"]
    X001567 -->|"max_flight"| X001585
    X001586["literal | empty"]
    X001567 -->|"target_occupancy"| X001586
    X001587["literal | opponent"]
    X001567 -->|"jumped_occupancy"| X001587
    X001588["literal | 40"]
    X001565 -->|"max_depth"| X001588
    X001589["literal | True"]
    X001565 -->|"captured_blockers"| X001589
    X001590["literal | True"]
    X001565 -->|"no_repeat_capture"| X001590
    X001591["literal | False"]
    X001565 -->|"stop_on_crowning"| X001591
    X001592["literal | 0"]
    X001563 -->|"b"| X001592
    E001593["effect[0]: move_entity"]
    A001537 --> E001593
    X001594["context | self"]
    E001593 -->|"entity"| X001594
    X001595["context | argument.to"]
    E001593 -->|"destination"| X001595
    E001596["effect[1]: change_entity_type"]
    A001537 --> E001596
    X001597["on_board_edge"]
    E001596 -->|"when"| X001597
    X001598["context | self"]
    X001597 -->|"entity"| X001598
    X001599["literal | promotion"]
    X001597 -->|"edge"| X001599
    X001600["context | self"]
    E001596 -->|"entity"| X001600
    X001601["literal | king"]
    E001596 -->|"to"| X001601
    E001602["effect[2]: advance_turn"]
    A001537 --> E001602
    A001603["international-draughts: man.capture | command | phase:turn"]
    F045 -.-> A001603
    X001604["and"]
    A001603 -->|"condition"| X001604
    X001605["is_active"]
    X001604 -->|"values[0]"| X001605
    X001606["context | actor"]
    X001605 -->|"participant"| X001606
    X001607["contains"]
    X001604 -->|"values[1]"| X001607
    X001608["traverse_paths"]
    X001607 -->|"items"| X001608
    X001609["context | self"]
    X001608 -->|"entity"| X001609
    X001610["jump_landing_steps"]
    X001608 -->|"step_generator"| X001610
    X001611["context | self"]
    X001610 -->|"entity"| X001611
    X001612["list"]
    X001610 -->|"directions"| X001612
    X001613["vector"]
    X001612 -->|"values[0]"| X001613
    X001614["literal | 1"]
    X001613 -->|"row"| X001614
    X001615["literal | -1"]
    X001613 -->|"column"| X001615
    X001616["vector"]
    X001612 -->|"values[1]"| X001616
    X001617["literal | 1"]
    X001616 -->|"row"| X001617
    X001618["literal | 1"]
    X001616 -->|"column"| X001618
    X001619["vector"]
    X001612 -->|"values[2]"| X001619
    X001620["literal | -1"]
    X001619 -->|"row"| X001620
    X001621["literal | -1"]
    X001619 -->|"column"| X001621
    X001622["vector"]
    X001612 -->|"values[3]"| X001622
    X001623["literal | -1"]
    X001622 -->|"row"| X001623
    X001624["literal | 1"]
    X001622 -->|"column"| X001624
    X001625["owner_orientation"]
    X001610 -->|"orientation"| X001625
    X001626["context | self"]
    X001625 -->|"entity"| X001626
    X001627["literal | True"]
    X001610 -->|"flying"| X001627
    X001628["literal | 9"]
    X001610 -->|"max_flight"| X001628
    X001629["literal | empty"]
    X001610 -->|"target_occupancy"| X001629
    X001630["literal | opponent"]
    X001610 -->|"jumped_occupancy"| X001630
    X001631["literal | 40"]
    X001608 -->|"max_depth"| X001631
    X001632["literal | True"]
    X001608 -->|"captured_blockers"| X001632
    X001633["literal | True"]
    X001608 -->|"no_repeat_capture"| X001633
    X001634["literal | False"]
    X001608 -->|"stop_on_crowning"| X001634
    X001635["context | argument.path"]
    X001607 -->|"value"| X001635
    X001636["eq"]
    X001604 -->|"values[2]"| X001636
    X001637["count"]
    X001636 -->|"a"| X001637
    X001638["path_captured_entities"]
    X001637 -->|"items"| X001638
    X001639["context | argument.path"]
    X001638 -->|"path"| X001639
    X001640["maximum"]
    X001636 -->|"b"| X001640
    X001641["map"]
    X001640 -->|"values"| X001641
    X001642["traverse_paths"]
    X001641 -->|"items"| X001642
    X001643["context | self"]
    X001642 -->|"entity"| X001643
    X001644["jump_landing_steps"]
    X001642 -->|"step_generator"| X001644
    X001645["context | self"]
    X001644 -->|"entity"| X001645
    X001646["list"]
    X001644 -->|"directions"| X001646
    X001647["vector"]
    X001646 -->|"values[0]"| X001647
    X001648["literal | 1"]
    X001647 -->|"row"| X001648
    X001649["literal | -1"]
    X001647 -->|"column"| X001649
    X001650["vector"]
    X001646 -->|"values[1]"| X001650
    X001651["literal | 1"]
    X001650 -->|"row"| X001651
    X001652["literal | 1"]
    X001650 -->|"column"| X001652
    X001653["vector"]
    X001646 -->|"values[2]"| X001653
    X001654["literal | -1"]
    X001653 -->|"row"| X001654
    X001655["literal | -1"]
    X001653 -->|"column"| X001655
    X001656["vector"]
    X001646 -->|"values[3]"| X001656
    X001657["literal | -1"]
    X001656 -->|"row"| X001657
    X001658["literal | 1"]
    X001656 -->|"column"| X001658
    X001659["owner_orientation"]
    X001644 -->|"orientation"| X001659
    X001660["context | self"]
    X001659 -->|"entity"| X001660
    X001661["literal | True"]
    X001644 -->|"flying"| X001661
    X001662["literal | 9"]
    X001644 -->|"max_flight"| X001662
    X001663["literal | empty"]
    X001644 -->|"target_occupancy"| X001663
    X001664["literal | opponent"]
    X001644 -->|"jumped_occupancy"| X001664
    X001665["literal | 40"]
    X001642 -->|"max_depth"| X001665
    X001666["literal | True"]
    X001642 -->|"captured_blockers"| X001666
    X001667["literal | True"]
    X001642 -->|"no_repeat_capture"| X001667
    X001668["literal | False"]
    X001642 -->|"stop_on_crowning"| X001668
    X001669["literal | p"]
    X001641 -->|"variable"| X001669
    X001670["count"]
    X001641 -->|"expression"| X001670
    X001671["path_captured_entities"]
    X001670 -->|"items"| X001671
    X001672["context | local.p"]
    X001671 -->|"path"| X001672
    E001673["effect[0]: apply_path"]
    A001603 --> E001673
    X001674["context | self"]
    E001673 -->|"entity"| X001674
    X001675["context | argument.path"]
    E001673 -->|"path"| X001675
    X001676["literal | True"]
    E001673 -->|"remove_traversed_entities"| X001676
    E001677["effect[1]: change_entity_type"]
    A001603 --> E001677
    X001678["on_board_edge"]
    E001677 -->|"when"| X001678
    X001679["context | self"]
    X001678 -->|"entity"| X001679
    X001680["literal | promotion"]
    X001678 -->|"edge"| X001680
    X001681["context | self"]
    E001677 -->|"entity"| X001681
    X001682["literal | king"]
    E001677 -->|"to"| X001682
    E001683["effect[2]: emit_event"]
    A001603 --> E001683
    X001684["literal | piece.captured"]
    E001683 -->|"name"| X001684
    E001685["effect[3]: advance_turn"]
    A001603 --> E001685
    A001686["international-draughts: man.candidates | hook | phase:turn | hook:action.generate"]
    F045 -.-> A001686
    X001687["literal | True"]
    A001686 -->|"condition"| X001687
    X001688["traverse_paths"]
    A001686 -->|"iterator"| X001688
    X001689["context | self"]
    X001688 -->|"entity"| X001689
    X001690["jump_landing_steps"]
    X001688 -->|"step_generator"| X001690
    X001691["context | self"]
    X001690 -->|"entity"| X001691
    X001692["list"]
    X001690 -->|"directions"| X001692
    X001693["vector"]
    X001692 -->|"values[0]"| X001693
    X001694["literal | 1"]
    X001693 -->|"row"| X001694
    X001695["literal | -1"]
    X001693 -->|"column"| X001695
    X001696["vector"]
    X001692 -->|"values[1]"| X001696
    X001697["literal | 1"]
    X001696 -->|"row"| X001697
    X001698["literal | 1"]
    X001696 -->|"column"| X001698
    X001699["vector"]
    X001692 -->|"values[2]"| X001699
    X001700["literal | -1"]
    X001699 -->|"row"| X001700
    X001701["literal | -1"]
    X001699 -->|"column"| X001701
    X001702["vector"]
    X001692 -->|"values[3]"| X001702
    X001703["literal | -1"]
    X001702 -->|"row"| X001703
    X001704["literal | 1"]
    X001702 -->|"column"| X001704
    X001705["owner_orientation"]
    X001690 -->|"orientation"| X001705
    X001706["context | self"]
    X001705 -->|"entity"| X001706
    X001707["literal | True"]
    X001690 -->|"flying"| X001707
    X001708["literal | 9"]
    X001690 -->|"max_flight"| X001708
    X001709["literal | empty"]
    X001690 -->|"target_occupancy"| X001709
    X001710["literal | opponent"]
    X001690 -->|"jumped_occupancy"| X001710
    X001711["literal | 40"]
    X001688 -->|"max_depth"| X001711
    X001712["literal | True"]
    X001688 -->|"captured_blockers"| X001712
    X001713["literal | True"]
    X001688 -->|"no_repeat_capture"| X001713
    X001714["literal | False"]
    X001688 -->|"stop_on_crowning"| X001714
    E001715["effect[0]: emit_candidate"]
    A001686 --> E001715
    X001716["context | self"]
    E001715 -->|"entity"| X001716
    X001717["context | candidate"]
    E001715 -->|"path"| X001717
    A001718["international-draughts: king.step | command | phase:turn"]
    F045 -.-> A001718
    X001719["and"]
    A001718 -->|"condition"| X001719
    X001720["is_active"]
    X001719 -->|"values[0]"| X001720
    X001721["context | actor"]
    X001720 -->|"participant"| X001721
    X001722["contains"]
    X001719 -->|"values[1]"| X001722
    X001723["reachable_grid_nodes"]
    X001722 -->|"items"| X001723
    X001724["context | self"]
    X001723 -->|"entity"| X001724
    X001725["list"]
    X001723 -->|"directions"| X001725
    X001726["vector"]
    X001725 -->|"values[0]"| X001726
    X001727["literal | 1"]
    X001726 -->|"row"| X001727
    X001728["literal | -1"]
    X001726 -->|"column"| X001728
    X001729["vector"]
    X001725 -->|"values[1]"| X001729
    X001730["literal | 1"]
    X001729 -->|"row"| X001730
    X001731["literal | 1"]
    X001729 -->|"column"| X001731
    X001732["vector"]
    X001725 -->|"values[2]"| X001732
    X001733["literal | -1"]
    X001732 -->|"row"| X001733
    X001734["literal | -1"]
    X001732 -->|"column"| X001734
    X001735["vector"]
    X001725 -->|"values[3]"| X001735
    X001736["literal | -1"]
    X001735 -->|"row"| X001736
    X001737["literal | 1"]
    X001735 -->|"column"| X001737
    X001738["literal | 9"]
    X001723 -->|"max_steps"| X001738
    X001739["literal | False"]
    X001723 -->|"leap"| X001739
    X001740["owner_orientation"]
    X001723 -->|"orientation"| X001740
    X001741["context | self"]
    X001740 -->|"entity"| X001741
    X001742["literal | empty"]
    X001723 -->|"target_occupancy"| X001742
    X001743["context | observed_state"]
    X001723 -->|"state"| X001743
    X001744["context | argument.to"]
    X001722 -->|"value"| X001744
    X001745["not"]
    X001719 -->|"values[2]"| X001745
    X001746["any_match"]
    X001745 -->|"value"| X001746
    X001747["participant_entities"]
    X001746 -->|"items"| X001747
    X001748["context | actor"]
    X001747 -->|"participant"| X001748
    X001749["literal | piece"]
    X001746 -->|"variable"| X001749
    X001750["gt"]
    X001746 -->|"predicate"| X001750
    X001751["count"]
    X001750 -->|"a"| X001751
    X001752["traverse_paths"]
    X001751 -->|"items"| X001752
    X001753["context | local.piece"]
    X001752 -->|"entity"| X001753
    X001754["jump_landing_steps"]
    X001752 -->|"step_generator"| X001754
    X001755["context | local.piece"]
    X001754 -->|"entity"| X001755
    X001756["list"]
    X001754 -->|"directions"| X001756
    X001757["vector"]
    X001756 -->|"values[0]"| X001757
    X001758["literal | 1"]
    X001757 -->|"row"| X001758
    X001759["literal | -1"]
    X001757 -->|"column"| X001759
    X001760["vector"]
    X001756 -->|"values[1]"| X001760
    X001761["literal | 1"]
    X001760 -->|"row"| X001761
    X001762["literal | 1"]
    X001760 -->|"column"| X001762
    X001763["vector"]
    X001756 -->|"values[2]"| X001763
    X001764["literal | -1"]
    X001763 -->|"row"| X001764
    X001765["literal | -1"]
    X001763 -->|"column"| X001765
    X001766["vector"]
    X001756 -->|"values[3]"| X001766
    X001767["literal | -1"]
    X001766 -->|"row"| X001767
    X001768["literal | 1"]
    X001766 -->|"column"| X001768
    X001769["owner_orientation"]
    X001754 -->|"orientation"| X001769
    X001770["context | local.piece"]
    X001769 -->|"entity"| X001770
    X001771["literal | True"]
    X001754 -->|"flying"| X001771
    X001772["literal | 9"]
    X001754 -->|"max_flight"| X001772
    X001773["literal | empty"]
    X001754 -->|"target_occupancy"| X001773
    X001774["literal | opponent"]
    X001754 -->|"jumped_occupancy"| X001774
    X001775["literal | 40"]
    X001752 -->|"max_depth"| X001775
    X001776["literal | True"]
    X001752 -->|"captured_blockers"| X001776
    X001777["literal | True"]
    X001752 -->|"no_repeat_capture"| X001777
    X001778["literal | False"]
    X001752 -->|"stop_on_crowning"| X001778
    X001779["literal | 0"]
    X001750 -->|"b"| X001779
    E001780["effect[0]: move_entity"]
    A001718 --> E001780
    X001781["context | self"]
    E001780 -->|"entity"| X001781
    X001782["context | argument.to"]
    E001780 -->|"destination"| X001782
    E001783["effect[1]: advance_turn"]
    A001718 --> E001783
    A001784["international-draughts: king.capture | command | phase:turn"]
    F045 -.-> A001784
    X001785["and"]
    A001784 -->|"condition"| X001785
    X001786["is_active"]
    X001785 -->|"values[0]"| X001786
    X001787["context | actor"]
    X001786 -->|"participant"| X001787
    X001788["contains"]
    X001785 -->|"values[1]"| X001788
    X001789["traverse_paths"]
    X001788 -->|"items"| X001789
    X001790["context | self"]
    X001789 -->|"entity"| X001790
    X001791["jump_landing_steps"]
    X001789 -->|"step_generator"| X001791
    X001792["context | self"]
    X001791 -->|"entity"| X001792
    X001793["list"]
    X001791 -->|"directions"| X001793
    X001794["vector"]
    X001793 -->|"values[0]"| X001794
    X001795["literal | 1"]
    X001794 -->|"row"| X001795
    X001796["literal | -1"]
    X001794 -->|"column"| X001796
    X001797["vector"]
    X001793 -->|"values[1]"| X001797
    X001798["literal | 1"]
    X001797 -->|"row"| X001798
    X001799["literal | 1"]
    X001797 -->|"column"| X001799
    X001800["vector"]
    X001793 -->|"values[2]"| X001800
    X001801["literal | -1"]
    X001800 -->|"row"| X001801
    X001802["literal | -1"]
    X001800 -->|"column"| X001802
    X001803["vector"]
    X001793 -->|"values[3]"| X001803
    X001804["literal | -1"]
    X001803 -->|"row"| X001804
    X001805["literal | 1"]
    X001803 -->|"column"| X001805
    X001806["owner_orientation"]
    X001791 -->|"orientation"| X001806
    X001807["context | self"]
    X001806 -->|"entity"| X001807
    X001808["literal | True"]
    X001791 -->|"flying"| X001808
    X001809["literal | 9"]
    X001791 -->|"max_flight"| X001809
    X001810["literal | empty"]
    X001791 -->|"target_occupancy"| X001810
    X001811["literal | opponent"]
    X001791 -->|"jumped_occupancy"| X001811
    X001812["literal | 40"]
    X001789 -->|"max_depth"| X001812
    X001813["literal | True"]
    X001789 -->|"captured_blockers"| X001813
    X001814["literal | True"]
    X001789 -->|"no_repeat_capture"| X001814
    X001815["literal | False"]
    X001789 -->|"stop_on_crowning"| X001815
    X001816["context | argument.path"]
    X001788 -->|"value"| X001816
    X001817["eq"]
    X001785 -->|"values[2]"| X001817
    X001818["count"]
    X001817 -->|"a"| X001818
    X001819["path_captured_entities"]
    X001818 -->|"items"| X001819
    X001820["context | argument.path"]
    X001819 -->|"path"| X001820
    X001821["maximum"]
    X001817 -->|"b"| X001821
    X001822["map"]
    X001821 -->|"values"| X001822
    X001823["traverse_paths"]
    X001822 -->|"items"| X001823
    X001824["context | self"]
    X001823 -->|"entity"| X001824
    X001825["jump_landing_steps"]
    X001823 -->|"step_generator"| X001825
    X001826["context | self"]
    X001825 -->|"entity"| X001826
    X001827["list"]
    X001825 -->|"directions"| X001827
    X001828["vector"]
    X001827 -->|"values[0]"| X001828
    X001829["literal | 1"]
    X001828 -->|"row"| X001829
    X001830["literal | -1"]
    X001828 -->|"column"| X001830
    X001831["vector"]
    X001827 -->|"values[1]"| X001831
    X001832["literal | 1"]
    X001831 -->|"row"| X001832
    X001833["literal | 1"]
    X001831 -->|"column"| X001833
    X001834["vector"]
    X001827 -->|"values[2]"| X001834
    X001835["literal | -1"]
    X001834 -->|"row"| X001835
    X001836["literal | -1"]
    X001834 -->|"column"| X001836
    X001837["vector"]
    X001827 -->|"values[3]"| X001837
    X001838["literal | -1"]
    X001837 -->|"row"| X001838
    X001839["literal | 1"]
    X001837 -->|"column"| X001839
    X001840["owner_orientation"]
    X001825 -->|"orientation"| X001840
    X001841["context | self"]
    X001840 -->|"entity"| X001841
    X001842["literal | True"]
    X001825 -->|"flying"| X001842
    X001843["literal | 9"]
    X001825 -->|"max_flight"| X001843
    X001844["literal | empty"]
    X001825 -->|"target_occupancy"| X001844
    X001845["literal | opponent"]
    X001825 -->|"jumped_occupancy"| X001845
    X001846["literal | 40"]
    X001823 -->|"max_depth"| X001846
    X001847["literal | True"]
    X001823 -->|"captured_blockers"| X001847
    X001848["literal | True"]
    X001823 -->|"no_repeat_capture"| X001848
    X001849["literal | False"]
    X001823 -->|"stop_on_crowning"| X001849
    X001850["literal | p"]
    X001822 -->|"variable"| X001850
    X001851["count"]
    X001822 -->|"expression"| X001851
    X001852["path_captured_entities"]
    X001851 -->|"items"| X001852
    X001853["context | local.p"]
    X001852 -->|"path"| X001853
    E001854["effect[0]: apply_path"]
    A001784 --> E001854
    X001855["context | self"]
    E001854 -->|"entity"| X001855
    X001856["context | argument.path"]
    E001854 -->|"path"| X001856
    X001857["literal | True"]
    E001854 -->|"remove_traversed_entities"| X001857
    E001858["effect[1]: emit_event"]
    A001784 --> E001858
    X001859["literal | piece.captured"]
    E001858 -->|"name"| X001859
    E001860["effect[2]: advance_turn"]
    A001784 --> E001860
    A001861["international-draughts: king.candidates | hook | phase:turn | hook:action.generate"]
    F045 -.-> A001861
    X001862["literal | True"]
    A001861 -->|"condition"| X001862
    X001863["traverse_paths"]
    A001861 -->|"iterator"| X001863
    X001864["context | self"]
    X001863 -->|"entity"| X001864
    X001865["jump_landing_steps"]
    X001863 -->|"step_generator"| X001865
    X001866["context | self"]
    X001865 -->|"entity"| X001866
    X001867["list"]
    X001865 -->|"directions"| X001867
    X001868["vector"]
    X001867 -->|"values[0]"| X001868
    X001869["literal | 1"]
    X001868 -->|"row"| X001869
    X001870["literal | -1"]
    X001868 -->|"column"| X001870
    X001871["vector"]
    X001867 -->|"values[1]"| X001871
    X001872["literal | 1"]
    X001871 -->|"row"| X001872
    X001873["literal | 1"]
    X001871 -->|"column"| X001873
    X001874["vector"]
    X001867 -->|"values[2]"| X001874
    X001875["literal | -1"]
    X001874 -->|"row"| X001875
    X001876["literal | -1"]
    X001874 -->|"column"| X001876
    X001877["vector"]
    X001867 -->|"values[3]"| X001877
    X001878["literal | -1"]
    X001877 -->|"row"| X001878
    X001879["literal | 1"]
    X001877 -->|"column"| X001879
    X001880["owner_orientation"]
    X001865 -->|"orientation"| X001880
    X001881["context | self"]
    X001880 -->|"entity"| X001881
    X001882["literal | True"]
    X001865 -->|"flying"| X001882
    X001883["literal | 9"]
    X001865 -->|"max_flight"| X001883
    X001884["literal | empty"]
    X001865 -->|"target_occupancy"| X001884
    X001885["literal | opponent"]
    X001865 -->|"jumped_occupancy"| X001885
    X001886["literal | 40"]
    X001863 -->|"max_depth"| X001886
    X001887["literal | True"]
    X001863 -->|"captured_blockers"| X001887
    X001888["literal | True"]
    X001863 -->|"no_repeat_capture"| X001888
    X001889["literal | False"]
    X001863 -->|"stop_on_crowning"| X001889
    E001890["effect[0]: emit_candidate"]
    A001861 --> E001890
    X001891["context | self"]
    E001890 -->|"entity"| X001891
    X001892["context | candidate"]
    E001890 -->|"path"| X001892
    A001893["international-draughts: victory.evaluate | hook | phase:* | hook:game.evaluate"]
    F045 -.-> A001893
    X001894["eq"]
    A001893 -->|"condition"| X001894
    X001895["available_action_count"]
    X001894 -->|"a"| X001895
    X001896["next_participant"]
    X001895 -->|"actor"| X001896
    X001897["context | active_participant"]
    X001896 -->|"participant"| X001897
    X001898["literal | 0"]
    X001894 -->|"b"| X001898
    E001899["effect[0]: complete_objective"]
    A001893 --> E001899
    X001900["context | self"]
    E001899 -->|"entity"| X001900
    E001901["effect[1]: finish_game"]
    A001893 --> E001901
    X001902["literal | victory"]
    E001901 -->|"result"| X001902
    A001903["international-draughts: draw.evaluate | hook | phase:* | hook:game.evaluate"]
    F045 -.-> A001903
    X001904["gte"]
    A001903 -->|"condition"| X001904
    X001905["field"]
    X001904 -->|"a"| X001905
    X001906["context | game"]
    X001905 -->|"entity"| X001906
    X001907["literal | draw_counter"]
    X001905 -->|"key"| X001907
    X001908["literal | 80"]
    X001904 -->|"b"| X001908
    E001909["effect[0]: complete_objective"]
    A001903 --> E001909
    X001910["context | self"]
    E001909 -->|"entity"| X001910
    E001911["effect[1]: finish_game"]
    A001903 --> E001911
    X001912["literal | draw"]
    E001911 -->|"result"| X001912
    A001913["international-draughts: capture_quest.count | hook | phase:* | hook:objective.evaluate"]
    F045 -.-> A001913
    X001914["eq"]
    A001913 -->|"condition"| X001914
    X001915["event_attribute"]
    X001914 -->|"a"| X001915
    X001916["context | event"]
    X001915 -->|"event"| X001916
    X001917["literal | kind"]
    X001915 -->|"attribute"| X001917
    X001918["literal | piece.captured"]
    X001914 -->|"b"| X001918
    E001919["effect[0]: increment_field"]
    A001913 --> E001919
    X001920["context | self"]
    E001919 -->|"entity"| X001920
    X001921["literal | progress"]
    E001919 -->|"field"| X001921
    X001922["literal | 1"]
    E001919 -->|"amount"| X001922
    A001923["moneyproperty: game.begin_turn | hook | phase:turn_start | hook:phase.enter"]
    F046 -.-> A001923
    X001924["literal | True"]
    A001923 -->|"condition"| X001924
    E001925["effect[0]: set_phase"]
    A001923 --> E001925
    X001926["literal | roll"]
    E001925 -->|"phase"| X001926
    A001927["moneyproperty: game.roll | command | phase:roll"]
    F046 -.-> A001927
    X001928["and"]
    A001927 -->|"condition"| X001928
    X001929["and"]
    X001928 -->|"values[0]"| X001929
    X001930["is_active"]
    X001929 -->|"values[0]"| X001930
    X001931["context | actor"]
    X001930 -->|"participant"| X001931
    X001932["phase_is"]
    X001929 -->|"values[1]"| X001932
    X001933["literal | roll"]
    X001932 -->|"phase"| X001933
    X001934["not"]
    X001928 -->|"values[1]"| X001934
    X001935["field"]
    X001934 -->|"value"| X001935
    X001936["entity_owned_by"]
    X001935 -->|"entity"| X001936
    X001937["context | actor"]
    X001936 -->|"participant"| X001937
    X001938["literal | token"]
    X001936 -->|"entity_type"| X001938
    X001939["literal | detained"]
    X001935 -->|"key"| X001939
    E001940["effect[0]: trusted_random_int"]
    A001927 --> E001940
    X001941["literal | die1"]
    E001940 -->|"name"| X001941
    X001942["literal | 1"]
    E001940 -->|"lower"| X001942
    X001943["literal | 6"]
    E001940 -->|"upper"| X001943
    E001944["effect[1]: trusted_random_int"]
    A001927 --> E001944
    X001945["literal | die2"]
    E001944 -->|"name"| X001945
    X001946["literal | 1"]
    E001944 -->|"lower"| X001946
    X001947["literal | 6"]
    E001944 -->|"upper"| X001947
    E001948["effect[2]: set_field"]
    A001927 --> E001948
    X001949["context | self"]
    E001948 -->|"entity"| X001949
    X001950["literal | current_roll"]
    E001948 -->|"field"| X001950
    X001951["add"]
    E001948 -->|"value"| X001951
    X001952["context | random.die1"]
    X001951 -->|"a"| X001952
    X001953["context | random.die2"]
    X001951 -->|"b"| X001953
    E001954["effect[3]: set_field"]
    A001927 --> E001954
    X001955["entity_owned_by"]
    E001954 -->|"entity"| X001955
    X001956["context | actor"]
    X001955 -->|"participant"| X001956
    X001957["literal | token"]
    X001955 -->|"entity_type"| X001957
    X001958["literal | doubles"]
    E001954 -->|"field"| X001958
    X001959["if"]
    E001954 -->|"value"| X001959
    X001960["eq"]
    X001959 -->|"condition"| X001960
    X001961["context | random.die1"]
    X001960 -->|"a"| X001961
    X001962["context | random.die2"]
    X001960 -->|"b"| X001962
    X001963["add"]
    X001959 -->|"then"| X001963
    X001964["field"]
    X001963 -->|"a"| X001964
    X001965["entity_owned_by"]
    X001964 -->|"entity"| X001965
    X001966["context | actor"]
    X001965 -->|"participant"| X001966
    X001967["literal | token"]
    X001965 -->|"entity_type"| X001967
    X001968["literal | doubles"]
    X001964 -->|"key"| X001968
    X001969["literal | 1"]
    X001963 -->|"b"| X001969
    X001970["literal | 0"]
    X001959 -->|"otherwise"| X001970
    E001971["effect[4]: set_phase"]
    A001927 --> E001971
    X001972["if"]
    E001971 -->|"phase"| X001972
    X001973["gte"]
    X001972 -->|"condition"| X001973
    X001974["field"]
    X001973 -->|"a"| X001974
    X001975["entity_owned_by"]
    X001974 -->|"entity"| X001975
    X001976["context | actor"]
    X001975 -->|"participant"| X001976
    X001977["literal | token"]
    X001975 -->|"entity_type"| X001977
    X001978["literal | doubles"]
    X001974 -->|"key"| X001978
    X001979["literal | 3"]
    X001973 -->|"b"| X001979
    X001980["literal | management"]
    X001972 -->|"then"| X001980
    X001981["literal | move"]
    X001972 -->|"otherwise"| X001981
    E001982["effect[5]: move_entity"]
    A001927 --> E001982
    X001983["gte"]
    E001982 -->|"when"| X001983
    X001984["field"]
    X001983 -->|"a"| X001984
    X001985["entity_owned_by"]
    X001984 -->|"entity"| X001985
    X001986["context | actor"]
    X001985 -->|"participant"| X001986
    X001987["literal | token"]
    X001985 -->|"entity_type"| X001987
    X001988["literal | doubles"]
    X001984 -->|"key"| X001988
    X001989["literal | 3"]
    X001983 -->|"b"| X001989
    X001990["entity_owned_by"]
    E001982 -->|"entity"| X001990
    X001991["context | actor"]
    X001990 -->|"participant"| X001991
    X001992["literal | token"]
    X001990 -->|"entity_type"| X001992
    X001993["entity_by_seed"]
    E001982 -->|"destination"| X001993
    X001994["literal | rest1"]
    X001993 -->|"key"| X001994
    E001995["effect[6]: set_field"]
    A001927 --> E001995
    X001996["gte"]
    E001995 -->|"when"| X001996
    X001997["field"]
    X001996 -->|"a"| X001997
    X001998["entity_owned_by"]
    X001997 -->|"entity"| X001998
    X001999["context | actor"]
    X001998 -->|"participant"| X001999
    X002000["literal | token"]
    X001998 -->|"entity_type"| X002000
    X002001["literal | doubles"]
    X001997 -->|"key"| X002001
    X002002["literal | 3"]
    X001996 -->|"b"| X002002
    X002003["entity_owned_by"]
    E001995 -->|"entity"| X002003
    X002004["context | actor"]
    X002003 -->|"participant"| X002004
    X002005["literal | token"]
    X002003 -->|"entity_type"| X002005
    X002006["literal | detained"]
    E001995 -->|"field"| X002006
    X002007["literal | True"]
    E001995 -->|"value"| X002007
    E002008["effect[7]: set_field"]
    A001927 --> E002008
    X002009["gte"]
    E002008 -->|"when"| X002009
    X002010["field"]
    X002009 -->|"a"| X002010
    X002011["entity_owned_by"]
    X002010 -->|"entity"| X002011
    X002012["context | actor"]
    X002011 -->|"participant"| X002012
    X002013["literal | token"]
    X002011 -->|"entity_type"| X002013
    X002014["literal | doubles"]
    X002010 -->|"key"| X002014
    X002015["literal | 3"]
    X002009 -->|"b"| X002015
    X002016["entity_owned_by"]
    E002008 -->|"entity"| X002016
    X002017["context | actor"]
    X002016 -->|"participant"| X002017
    X002018["literal | token"]
    X002016 -->|"entity_type"| X002018
    X002019["literal | detention_attempts"]
    E002008 -->|"field"| X002019
    X002020["literal | 0"]
    E002008 -->|"value"| X002020
    E002021["effect[8]: set_field"]
    A001927 --> E002021
    X002022["gte"]
    E002021 -->|"when"| X002022
    X002023["field"]
    X002022 -->|"a"| X002023
    X002024["entity_owned_by"]
    X002023 -->|"entity"| X002024
    X002025["context | actor"]
    X002024 -->|"participant"| X002025
    X002026["literal | token"]
    X002024 -->|"entity_type"| X002026
    X002027["literal | doubles"]
    X002023 -->|"key"| X002027
    X002028["literal | 3"]
    X002022 -->|"b"| X002028
    X002029["entity_owned_by"]
    E002021 -->|"entity"| X002029
    X002030["context | actor"]
    X002029 -->|"participant"| X002030
    X002031["literal | token"]
    X002029 -->|"entity_type"| X002031
    X002032["literal | doubles"]
    E002021 -->|"field"| X002032
    X002033["literal | 0"]
    E002021 -->|"value"| X002033
    A002034["moneyproperty: token.move | hook | phase:move | hook:phase.enter"]
    F046 -.-> A002034
    X002035["and"]
    A002034 -->|"condition"| X002035
    X002036["phase_is"]
    X002035 -->|"values[0]"| X002036
    X002037["literal | move"]
    X002036 -->|"phase"| X002037
    X002038["eq"]
    X002035 -->|"values[1]"| X002038
    X002039["owner"]
    X002038 -->|"a"| X002039
    X002040["context | self"]
    X002039 -->|"entity"| X002040
    X002041["context | active_participant"]
    X002038 -->|"b"| X002041
    E002042["effect[0]: move_entity"]
    A002034 --> E002042
    X002043["context | self"]
    E002042 -->|"entity"| X002043
    X002044["path_last"]
    E002042 -->|"destination"| X002044
    X002045["track_advance"]
    X002044 -->|"path"| X002045
    X002046["context | self"]
    X002045 -->|"entity"| X002046
    X002047["field"]
    X002045 -->|"steps"| X002047
    X002048["context | game"]
    X002047 -->|"entity"| X002048
    X002049["literal | current_roll"]
    X002047 -->|"key"| X002049
    E002050["effect[1]: emit_traversal_events"]
    A002034 --> E002050
    X002051["context | self"]
    E002050 -->|"entity"| X002051
    X002052["field"]
    E002050 -->|"steps"| X002052
    X002053["context | game"]
    X002052 -->|"entity"| X002053
    X002054["literal | current_roll"]
    X002052 -->|"key"| X002054
    X002055["literal | space.passed"]
    E002050 -->|"hook"| X002055
    E002056["effect[2]: set_phase"]
    A002034 --> E002056
    X002057["literal | resolve"]
    E002056 -->|"phase"| X002057
    A002058["moneyproperty: lot.resolve_location | hook | phase:resolve | hook:phase.enter"]
    F046 -.-> A002058
    X002059["entity_at"]
    A002058 -->|"condition"| X002059
    X002060["context | self"]
    X002059 -->|"entity"| X002060
    X002061["context | active_participant"]
    X002059 -->|"participant"| X002061
    E002062["effect[0]: emit_event"]
    A002058 --> E002062
    X002063["literal | space.landed"]
    E002062 -->|"name"| X002063
    E002064["effect[1]: set_phase"]
    A002058 --> E002064
    X002065["literal | decision"]
    E002064 -->|"phase"| X002065
    A002066["moneyproperty: property.buy | command | phase:decision"]
    F046 -.-> A002066
    X002067["and"]
    A002066 -->|"condition"| X002067
    X002068["and"]
    X002067 -->|"values[0]"| X002068
    X002069["and"]
    X002068 -->|"values[0]"| X002069
    X002070["eq"]
    X002069 -->|"values[0]"| X002070
    X002071["owner"]
    X002070 -->|"a"| X002071
    X002072["context | self"]
    X002071 -->|"entity"| X002072
    X002073["literal | null"]
    X002070 -->|"b"| X002073
    X002074["gte"]
    X002069 -->|"values[1]"| X002074
    X002075["field"]
    X002074 -->|"a"| X002075
    X002076["entity_owned_by"]
    X002075 -->|"entity"| X002076
    X002077["context | actor"]
    X002076 -->|"participant"| X002077
    X002078["literal | inventory"]
    X002076 -->|"entity_type"| X002078
    X002079["literal | balance"]
    X002075 -->|"key"| X002079
    X002080["field"]
    X002074 -->|"b"| X002080
    X002081["context | self"]
    X002080 -->|"entity"| X002081
    X002082["literal | price"]
    X002080 -->|"key"| X002082
    X002083["eq"]
    X002068 -->|"values[1]"| X002083
    X002084["entity_location"]
    X002083 -->|"a"| X002084
    X002085["context | self"]
    X002084 -->|"entity"| X002085
    X002086["entity_location"]
    X002083 -->|"b"| X002086
    X002087["entity_owned_by"]
    X002086 -->|"entity"| X002087
    X002088["context | actor"]
    X002087 -->|"participant"| X002088
    X002089["literal | token"]
    X002087 -->|"entity_type"| X002089
    X002090["phase_is"]
    X002067 -->|"values[1]"| X002090
    X002091["literal | decision"]
    X002090 -->|"phase"| X002091
    E002092["effect[0]: transfer_resource"]
    A002066 --> E002092
    X002093["context | actor"]
    E002092 -->|"source"| X002093
    X002094["context | bank"]
    E002092 -->|"target"| X002094
    X002095["field"]
    E002092 -->|"amount"| X002095
    X002096["context | self"]
    X002095 -->|"entity"| X002096
    X002097["literal | price"]
    X002095 -->|"key"| X002097
    E002098["effect[1]: set_owner"]
    A002066 --> E002098
    X002099["context | self"]
    E002098 -->|"entity"| X002099
    X002100["context | actor"]
    E002098 -->|"owner"| X002100
    E002101["effect[2]: set_phase"]
    A002066 --> E002101
    X002102["literal | management"]
    E002101 -->|"phase"| X002102
    A002103["moneyproperty: property.decline_purchase | command | phase:decision"]
    F046 -.-> A002103
    X002104["and"]
    A002103 -->|"condition"| X002104
    X002105["eq"]
    X002104 -->|"values[0]"| X002105
    X002106["owner"]
    X002105 -->|"a"| X002106
    X002107["context | self"]
    X002106 -->|"entity"| X002107
    X002108["literal | null"]
    X002105 -->|"b"| X002108
    X002109["eq"]
    X002104 -->|"values[1]"| X002109
    X002110["entity_location"]
    X002109 -->|"a"| X002110
    X002111["context | self"]
    X002110 -->|"entity"| X002111
    X002112["entity_location"]
    X002109 -->|"b"| X002112
    X002113["entity_owned_by"]
    X002112 -->|"entity"| X002113
    X002114["context | actor"]
    X002113 -->|"participant"| X002114
    X002115["literal | token"]
    X002113 -->|"entity_type"| X002115
    E002116["effect[0]: open_decision"]
    A002103 --> E002116
    X002117["literal | auction"]
    E002116 -->|"decision"| X002117
    X002118["context | self"]
    E002116 -->|"entity"| X002118
    E002119["effect[1]: set_phase"]
    A002103 --> E002119
    X002120["literal | decision"]
    E002119 -->|"phase"| X002120
    A002121["moneyproperty: auction.bid | command | phase:decision"]
    F046 -.-> A002121
    X002122["and"]
    A002121 -->|"condition"| X002122
    X002123["decision_is_open"]
    X002122 -->|"values[0]"| X002123
    X002124["context | self"]
    X002123 -->|"decision"| X002124
    X002125["contains"]
    X002122 -->|"values[1]"| X002125
    X002126["decision_eligible"]
    X002125 -->|"items"| X002126
    X002127["context | self"]
    X002126 -->|"decision"| X002127
    X002128["context | actor"]
    X002125 -->|"value"| X002128
    X002129["gte"]
    X002122 -->|"values[2]"| X002129
    X002130["field"]
    X002129 -->|"a"| X002130
    X002131["entity_owned_by"]
    X002130 -->|"entity"| X002131
    X002132["context | actor"]
    X002131 -->|"participant"| X002132
    X002133["literal | inventory"]
    X002131 -->|"entity_type"| X002133
    X002134["literal | balance"]
    X002130 -->|"key"| X002134
    X002135["context | argument.amount"]
    X002129 -->|"b"| X002135
    X002136["gt"]
    X002122 -->|"values[3]"| X002136
    X002137["context | argument.amount"]
    X002136 -->|"a"| X002137
    X002138["maximum_or"]
    X002136 -->|"b"| X002138
    X002139["map"]
    X002138 -->|"items"| X002139
    X002140["decision_responses"]
    X002139 -->|"items"| X002140
    X002141["context | self"]
    X002140 -->|"decision"| X002141
    X002142["literal | response"]
    X002139 -->|"variable"| X002142
    X002143["record_field"]
    X002139 -->|"expression"| X002143
    X002144["context | local.response"]
    X002143 -->|"record"| X002144
    X002145["literal | amount"]
    X002143 -->|"key"| X002145
    X002146["literal | 0"]
    X002138 -->|"default"| X002146
    E002147["effect[0]: record_decision"]
    A002121 --> E002147
    X002148["context | self"]
    E002147 -->|"entity"| X002148
    X002149["context | actor"]
    E002147 -->|"actor"| X002149
    X002150["context | argument.amount"]
    E002147 -->|"amount"| X002150
    A002151["moneyproperty: auction.resolve_auction | hook | phase:decision | hook:decision.resolved"]
    F046 -.-> A002151
    X002152["and"]
    A002151 -->|"condition"| X002152
    X002153["decision_is_open"]
    X002152 -->|"values[0]"| X002153
    X002154["context | self"]
    X002153 -->|"decision"| X002154
    X002155["eq"]
    X002152 -->|"values[1]"| X002155
    X002156["count"]
    X002155 -->|"a"| X002156
    X002157["decision_responses"]
    X002156 -->|"items"| X002157
    X002158["context | self"]
    X002157 -->|"decision"| X002158
    X002159["count"]
    X002155 -->|"b"| X002159
    X002160["decision_eligible"]
    X002159 -->|"items"| X002160
    X002161["context | self"]
    X002160 -->|"decision"| X002161
    E002162["effect[0]: resolve_decision"]
    A002151 --> E002162
    X002163["context | self"]
    E002162 -->|"entity"| X002163
    E002164["effect[1]: transfer_resource"]
    A002151 --> E002164
    X002165["is_present"]
    E002164 -->|"when"| X002165
    X002166["best_by"]
    X002165 -->|"value"| X002166
    X002167["decision_responses"]
    X002166 -->|"items"| X002167
    X002168["context | self"]
    X002167 -->|"decision"| X002168
    X002169["literal | amount"]
    X002166 -->|"field"| X002169
    X002170["literal | descending"]
    X002166 -->|"order"| X002170
    X002171["record_field"]
    E002164 -->|"source"| X002171
    X002172["best_by"]
    X002171 -->|"record"| X002172
    X002173["decision_responses"]
    X002172 -->|"items"| X002173
    X002174["context | self"]
    X002173 -->|"decision"| X002174
    X002175["literal | amount"]
    X002172 -->|"field"| X002175
    X002176["literal | descending"]
    X002172 -->|"order"| X002176
    X002177["literal | participant"]
    X002171 -->|"key"| X002177
    X002178["context | bank"]
    E002164 -->|"target"| X002178
    X002179["record_field"]
    E002164 -->|"amount"| X002179
    X002180["best_by"]
    X002179 -->|"record"| X002180
    X002181["decision_responses"]
    X002180 -->|"items"| X002181
    X002182["context | self"]
    X002181 -->|"decision"| X002182
    X002183["literal | amount"]
    X002180 -->|"field"| X002183
    X002184["literal | descending"]
    X002180 -->|"order"| X002184
    X002185["literal | amount"]
    X002179 -->|"key"| X002185
    E002186["effect[2]: set_owner"]
    A002151 --> E002186
    X002187["is_present"]
    E002186 -->|"when"| X002187
    X002188["best_by"]
    X002187 -->|"value"| X002188
    X002189["decision_responses"]
    X002188 -->|"items"| X002189
    X002190["context | self"]
    X002189 -->|"decision"| X002190
    X002191["literal | amount"]
    X002188 -->|"field"| X002191
    X002192["literal | descending"]
    X002188 -->|"order"| X002192
    X002193["decision_subject"]
    E002186 -->|"entity"| X002193
    X002194["context | self"]
    X002193 -->|"decision"| X002194
    X002195["record_field"]
    E002186 -->|"owner"| X002195
    X002196["best_by"]
    X002195 -->|"record"| X002196
    X002197["decision_responses"]
    X002196 -->|"items"| X002197
    X002198["context | self"]
    X002197 -->|"decision"| X002198
    X002199["literal | amount"]
    X002196 -->|"field"| X002199
    X002200["literal | descending"]
    X002196 -->|"order"| X002200
    X002201["literal | participant"]
    X002195 -->|"key"| X002201
    E002202["effect[3]: set_phase"]
    A002151 --> E002202
    X002203["literal | management"]
    E002202 -->|"phase"| X002203
    A002204["moneyproperty: property.charge_rent | hook | phase:resolve | hook:space.landed"]
    F046 -.-> A002204
    X002205["and"]
    A002204 -->|"condition"| X002205
    X002206["and"]
    X002205 -->|"values[0]"| X002206
    X002207["not"]
    X002206 -->|"values[0]"| X002207
    X002208["eq"]
    X002207 -->|"value"| X002208
    X002209["owner"]
    X002208 -->|"a"| X002209
    X002210["context | self"]
    X002209 -->|"entity"| X002210
    X002211["literal | null"]
    X002208 -->|"b"| X002211
    X002212["not"]
    X002206 -->|"values[1]"| X002212
    X002213["eq"]
    X002212 -->|"value"| X002213
    X002214["owner"]
    X002213 -->|"a"| X002214
    X002215["context | self"]
    X002214 -->|"entity"| X002215
    X002216["context | active_participant"]
    X002213 -->|"b"| X002216
    X002217["eq"]
    X002205 -->|"values[1]"| X002217
    X002218["entity_location"]
    X002217 -->|"a"| X002218
    X002219["context | self"]
    X002218 -->|"entity"| X002219
    X002220["entity_location"]
    X002217 -->|"b"| X002220
    X002221["entity_owned_by"]
    X002220 -->|"entity"| X002221
    X002222["context | active_participant"]
    X002221 -->|"participant"| X002222
    X002223["literal | token"]
    X002221 -->|"entity_type"| X002223
    E002224["effect[0]: transfer_resource"]
    A002204 --> E002224
    X002225["context | active_participant"]
    E002224 -->|"source"| X002225
    X002226["owner"]
    E002224 -->|"target"| X002226
    X002227["context | self"]
    X002226 -->|"entity"| X002227
    X002228["multiply"]
    E002224 -->|"amount"| X002228
    X002229["field"]
    X002228 -->|"a"| X002229
    X002230["context | self"]
    X002229 -->|"entity"| X002230
    X002231["literal | base_rent"]
    X002229 -->|"key"| X002231
    X002232["add"]
    X002228 -->|"b"| X002232
    X002233["literal | 1"]
    X002232 -->|"a"| X002233
    X002234["field"]
    X002232 -->|"b"| X002234
    X002235["context | self"]
    X002234 -->|"entity"| X002235
    X002236["literal | houses"]
    X002234 -->|"key"| X002236
    A002237["moneyproperty: property.mortgage | command | phase:management"]
    F046 -.-> A002237
    X002238["and"]
    A002237 -->|"condition"| X002238
    X002239["eq"]
    X002238 -->|"values[0]"| X002239
    X002240["owner"]
    X002239 -->|"a"| X002240
    X002241["context | self"]
    X002240 -->|"entity"| X002241
    X002242["context | actor"]
    X002239 -->|"b"| X002242
    X002243["not"]
    X002238 -->|"values[1]"| X002243
    X002244["field"]
    X002243 -->|"value"| X002244
    X002245["context | self"]
    X002244 -->|"entity"| X002245
    X002246["literal | mortgaged"]
    X002244 -->|"key"| X002246
    X002247["eq"]
    X002238 -->|"values[2]"| X002247
    X002248["field"]
    X002247 -->|"a"| X002248
    X002249["context | self"]
    X002248 -->|"entity"| X002249
    X002250["literal | houses"]
    X002248 -->|"key"| X002250
    X002251["literal | 0"]
    X002247 -->|"b"| X002251
    E002252["effect[0]: set_field"]
    A002237 --> E002252
    X002253["context | self"]
    E002252 -->|"entity"| X002253
    X002254["literal | mortgaged"]
    E002252 -->|"field"| X002254
    X002255["literal | True"]
    E002252 -->|"value"| X002255
    E002256["effect[1]: credit_resource"]
    A002237 --> E002256
    X002257["context | actor"]
    E002256 -->|"participant"| X002257
    X002258["field"]
    E002256 -->|"amount"| X002258
    X002259["context | self"]
    X002258 -->|"entity"| X002259
    X002260["literal | mortgage_value"]
    X002258 -->|"key"| X002260
    A002261["moneyproperty: property.unmortgage | command | phase:management"]
    F046 -.-> A002261
    X002262["and"]
    A002261 -->|"condition"| X002262
    X002263["eq"]
    X002262 -->|"values[0]"| X002263
    X002264["owner"]
    X002263 -->|"a"| X002264
    X002265["context | self"]
    X002264 -->|"entity"| X002265
    X002266["context | actor"]
    X002263 -->|"b"| X002266
    X002267["field"]
    X002262 -->|"values[1]"| X002267
    X002268["context | self"]
    X002267 -->|"entity"| X002268
    X002269["literal | mortgaged"]
    X002267 -->|"key"| X002269
    X002270["gte"]
    X002262 -->|"values[2]"| X002270
    X002271["field"]
    X002270 -->|"a"| X002271
    X002272["entity_owned_by"]
    X002271 -->|"entity"| X002272
    X002273["context | actor"]
    X002272 -->|"participant"| X002273
    X002274["literal | inventory"]
    X002272 -->|"entity_type"| X002274
    X002275["literal | balance"]
    X002271 -->|"key"| X002275
    X002276["floor_divide"]
    X002270 -->|"b"| X002276
    X002277["add"]
    X002276 -->|"a"| X002277
    X002278["multiply"]
    X002277 -->|"a"| X002278
    X002279["field"]
    X002278 -->|"a"| X002279
    X002280["context | self"]
    X002279 -->|"entity"| X002280
    X002281["literal | mortgage_value"]
    X002279 -->|"key"| X002281
    X002282["literal | 110"]
    X002278 -->|"b"| X002282
    X002283["literal | 99"]
    X002277 -->|"b"| X002283
    X002284["literal | 100"]
    X002276 -->|"b"| X002284
    E002285["effect[0]: debit_resource"]
    A002261 --> E002285
    X002286["context | actor"]
    E002285 -->|"participant"| X002286
    X002287["floor_divide"]
    E002285 -->|"amount"| X002287
    X002288["add"]
    X002287 -->|"a"| X002288
    X002289["multiply"]
    X002288 -->|"a"| X002289
    X002290["field"]
    X002289 -->|"a"| X002290
    X002291["context | self"]
    X002290 -->|"entity"| X002291
    X002292["literal | mortgage_value"]
    X002290 -->|"key"| X002292
    X002293["literal | 110"]
    X002289 -->|"b"| X002293
    X002294["literal | 99"]
    X002288 -->|"b"| X002294
    X002295["literal | 100"]
    X002287 -->|"b"| X002295
    E002296["effect[1]: set_field"]
    A002261 --> E002296
    X002297["context | self"]
    E002296 -->|"entity"| X002297
    X002298["literal | mortgaged"]
    E002296 -->|"field"| X002298
    X002299["literal | False"]
    E002296 -->|"value"| X002299
    A002300["moneyproperty: property.build | command | phase:management"]
    F046 -.-> A002300
    X002301["and"]
    A002300 -->|"condition"| X002301
    X002302["eq"]
    X002301 -->|"values[0]"| X002302
    X002303["owner"]
    X002302 -->|"a"| X002303
    X002304["context | self"]
    X002303 -->|"entity"| X002304
    X002305["context | actor"]
    X002302 -->|"b"| X002305
    X002306["not"]
    X002301 -->|"values[1]"| X002306
    X002307["field"]
    X002306 -->|"value"| X002307
    X002308["context | self"]
    X002307 -->|"entity"| X002308
    X002309["literal | mortgaged"]
    X002307 -->|"key"| X002309
    X002310["lt"]
    X002301 -->|"values[2]"| X002310
    X002311["field"]
    X002310 -->|"a"| X002311
    X002312["context | self"]
    X002311 -->|"entity"| X002312
    X002313["literal | houses"]
    X002311 -->|"key"| X002313
    X002314["literal | 5"]
    X002310 -->|"b"| X002314
    X002315["gte"]
    X002301 -->|"values[3]"| X002315
    X002316["field"]
    X002315 -->|"a"| X002316
    X002317["entity_owned_by"]
    X002316 -->|"entity"| X002317
    X002318["context | actor"]
    X002317 -->|"participant"| X002318
    X002319["literal | inventory"]
    X002317 -->|"entity_type"| X002319
    X002320["literal | balance"]
    X002316 -->|"key"| X002320
    X002321["field"]
    X002315 -->|"b"| X002321
    X002322["context | self"]
    X002321 -->|"entity"| X002322
    X002323["literal | build_cost"]
    X002321 -->|"key"| X002323
    E002324["effect[0]: debit_resource"]
    A002300 --> E002324
    X002325["context | actor"]
    E002324 -->|"participant"| X002325
    X002326["field"]
    E002324 -->|"amount"| X002326
    X002327["context | self"]
    X002326 -->|"entity"| X002327
    X002328["literal | build_cost"]
    X002326 -->|"key"| X002328
    E002329["effect[1]: increment_field"]
    A002300 --> E002329
    X002330["context | self"]
    E002329 -->|"entity"| X002330
    X002331["literal | houses"]
    E002329 -->|"field"| X002331
    X002332["literal | 1"]
    E002329 -->|"amount"| X002332
    A002333["moneyproperty: property.sell_building | command | phase:management"]
    F046 -.-> A002333
    X002334["and"]
    A002333 -->|"condition"| X002334
    X002335["eq"]
    X002334 -->|"values[0]"| X002335
    X002336["owner"]
    X002335 -->|"a"| X002336
    X002337["context | self"]
    X002336 -->|"entity"| X002337
    X002338["context | actor"]
    X002335 -->|"b"| X002338
    X002339["gt"]
    X002334 -->|"values[1]"| X002339
    X002340["field"]
    X002339 -->|"a"| X002340
    X002341["context | self"]
    X002340 -->|"entity"| X002341
    X002342["literal | houses"]
    X002340 -->|"key"| X002342
    X002343["literal | 0"]
    X002339 -->|"b"| X002343
    E002344["effect[0]: increment_field"]
    A002333 --> E002344
    X002345["context | self"]
    E002344 -->|"entity"| X002345
    X002346["literal | houses"]
    E002344 -->|"field"| X002346
    X002347["literal | -1"]
    E002344 -->|"amount"| X002347
    E002348["effect[1]: credit_resource"]
    A002333 --> E002348
    X002349["context | actor"]
    E002348 -->|"participant"| X002349
    X002350["floor_divide"]
    E002348 -->|"amount"| X002350
    X002351["field"]
    X002350 -->|"a"| X002351
    X002352["context | self"]
    X002351 -->|"entity"| X002352
    X002353["literal | build_cost"]
    X002351 -->|"key"| X002353
    X002354["literal | 2"]
    X002350 -->|"b"| X002354
    A002355["moneyproperty: deck.draw | hook | phase:resolve | hook:space.landed"]
    F046 -.-> A002355
    X002356["has_relation"]
    A002355 -->|"condition"| X002356
    X002357["context | location"]
    X002356 -->|"source"| X002357
    X002358["context | self"]
    X002356 -->|"target"| X002358
    X002359["literal | draws_from"]
    X002356 -->|"relation"| X002359
    E002360["effect[0]: draw_collection_item"]
    A002355 --> E002360
    X002361["context | self"]
    E002360 -->|"deck"| X002361
    E002362["effect[1]: emit_event"]
    A002355 --> E002362
    X002363["literal | card.drawn"]
    E002362 -->|"name"| X002363
    X002364["context | drawn_card"]
    E002362 -->|"entity"| X002364
    A002365["moneyproperty: trade_offer.propose_trade | command | phase:management"]
    F046 -.-> A002365
    X002366["transfer_plan_valid"]
    A002365 -->|"condition"| X002366
    X002367["context | argument.offer"]
    X002366 -->|"plan"| X002367
    X002368["context | observed_state"]
    X002366 -->|"state"| X002368
    E002369["effect[0]: create_entity"]
    A002365 --> E002369
    X002370["literal | trade_offer"]
    E002369 -->|"type"| X002370
    X002371["context | argument.offer"]
    E002369 -->|"fields"| X002371
    E002372["effect[1]: open_decision"]
    A002365 --> E002372
    X002373["literal | trade"]
    E002372 -->|"decision"| X002373
    X002374["context | created_entity"]
    E002372 -->|"entity"| X002374
    A002375["moneyproperty: trade_offer.accept_trade | command | phase:decision"]
    F046 -.-> A002375
    X002376["and"]
    A002375 -->|"condition"| X002376
    X002377["and"]
    X002376 -->|"values[0]"| X002377
    X002378["decision_is_open"]
    X002377 -->|"values[0]"| X002378
    X002379["context | self"]
    X002378 -->|"decision"| X002379
    X002380["contains"]
    X002377 -->|"values[1]"| X002380
    X002381["decision_eligible"]
    X002380 -->|"items"| X002381
    X002382["context | self"]
    X002381 -->|"decision"| X002382
    X002383["context | actor"]
    X002380 -->|"value"| X002383
    X002384["transfer_plan_valid"]
    X002376 -->|"values[1]"| X002384
    X002385["decision_payload"]
    X002384 -->|"plan"| X002385
    X002386["context | self"]
    X002385 -->|"decision"| X002386
    X002387["context | observed_state"]
    X002384 -->|"state"| X002387
    E002388["effect[0]: execute_transfer_plan"]
    A002375 --> E002388
    X002389["decision_payload"]
    E002388 -->|"plan"| X002389
    X002390["context | self"]
    X002389 -->|"decision"| X002390
    E002391["effect[1]: resolve_decision"]
    A002375 --> E002391
    X002392["context | self"]
    E002391 -->|"entity"| X002392
    A002393["moneyproperty: trade_offer.reject_trade | command | phase:decision"]
    F046 -.-> A002393
    X002394["and"]
    A002393 -->|"condition"| X002394
    X002395["decision_is_open"]
    X002394 -->|"values[0]"| X002395
    X002396["context | self"]
    X002395 -->|"decision"| X002396
    X002397["contains"]
    X002394 -->|"values[1]"| X002397
    X002398["decision_eligible"]
    X002397 -->|"items"| X002398
    X002399["context | self"]
    X002398 -->|"decision"| X002399
    X002400["context | actor"]
    X002397 -->|"value"| X002400
    E002401["effect[0]: resolve_decision"]
    A002393 --> E002401
    X002402["context | self"]
    E002401 -->|"entity"| X002402
    A002403["moneyproperty: game.end_turn | command | phase:management"]
    F046 -.-> A002403
    X002404["eq"]
    A002403 -->|"condition"| X002404
    X002405["count"]
    X002404 -->|"a"| X002405
    X002406["entities_matching"]
    X002405 -->|"items"| X002406
    X002407["literal | decision"]
    X002406 -->|"entity_type"| X002407
    X002408["field"]
    X002406 -->|"where"| X002408
    X002409["context | candidate"]
    X002408 -->|"entity"| X002409
    X002410["literal | open"]
    X002408 -->|"key"| X002410
    X002411["literal | 0"]
    X002404 -->|"b"| X002411
    E002412["effect[0]: advance_turn"]
    A002403 --> E002412
    X002413["eq"]
    E002412 -->|"when"| X002413
    X002414["field"]
    X002413 -->|"a"| X002414
    X002415["entity_owned_by"]
    X002414 -->|"entity"| X002415
    X002416["context | actor"]
    X002415 -->|"participant"| X002416
    X002417["literal | token"]
    X002415 -->|"entity_type"| X002417
    X002418["literal | doubles"]
    X002414 -->|"key"| X002418
    X002419["literal | 0"]
    X002413 -->|"b"| X002419
    E002420["effect[1]: set_phase"]
    A002403 --> E002420
    X002421["literal | roll"]
    E002420 -->|"phase"| X002421
    A002422["moneyproperty: bankruptcy.bankruptcy | hook | phase:* | hook:game.evaluate"]
    F046 -.-> A002422
    X002423["lt"]
    A002422 -->|"condition"| X002423
    X002424["field"]
    X002423 -->|"a"| X002424
    X002425["entity_owned_by"]
    X002424 -->|"entity"| X002425
    X002426["context | active_participant"]
    X002425 -->|"participant"| X002426
    X002427["literal | inventory"]
    X002425 -->|"entity_type"| X002427
    X002428["literal | balance"]
    X002424 -->|"key"| X002428
    X002429["literal | 0"]
    X002423 -->|"b"| X002429
    E002430["effect[0]: execute_transfer_plan"]
    A002422 --> E002430
    X002431["liquidation_transfer_plan"]
    E002430 -->|"plan"| X002431
    X002432["context | active_participant"]
    X002431 -->|"debtor"| X002432
    X002433["get_state"]
    X002431 -->|"creditor"| X002433
    X002434["literal | creditor"]
    X002433 -->|"field"| X002434
    X002435["participant_entities"]
    X002431 -->|"assets"| X002435
    X002436["context | active_participant"]
    X002435 -->|"participant"| X002436
    X002437["literal | 0"]
    X002431 -->|"reserve"| X002437
    E002438["effect[1]: eliminate_participant"]
    A002422 --> E002438
    X002439["context | active_participant"]
    E002438 -->|"participant"| X002439
    A002440["moneyproperty: last_solvent.win | hook | phase:* | hook:game.evaluate"]
    F046 -.-> A002440
    X002441["eq"]
    A002440 -->|"condition"| X002441
    X002442["count"]
    X002441 -->|"a"| X002442
    X002443["filter"]
    X002442 -->|"items"| X002443
    X002444["participants"]
    X002443 -->|"items"| X002444
    X002445["literal | person"]
    X002443 -->|"variable"| X002445
    X002446["gte"]
    X002443 -->|"condition"| X002446
    X002447["field"]
    X002446 -->|"a"| X002447
    X002448["entity_owned_by"]
    X002447 -->|"entity"| X002448
    X002449["context | local.person"]
    X002448 -->|"participant"| X002449
    X002450["literal | inventory"]
    X002448 -->|"entity_type"| X002450
    X002451["literal | balance"]
    X002447 -->|"key"| X002451
    X002452["literal | 0"]
    X002446 -->|"b"| X002452
    X002453["literal | 1"]
    X002441 -->|"b"| X002453
    E002454["effect[0]: complete_objective"]
    A002440 --> E002454
    X002455["context | self"]
    E002454 -->|"entity"| X002455
    E002456["effect[1]: finish_game"]
    A002440 --> E002456
    X002457["literal | last_solvent"]
    E002456 -->|"result"| X002457
    A002458["moneyproperty: wealth_quest.wealth | hook | phase:* | hook:objective.evaluate"]
    F046 -.-> A002458
    X002459["gte"]
    A002458 -->|"condition"| X002459
    X002460["field"]
    X002459 -->|"a"| X002460
    X002461["entity_owned_by"]
    X002460 -->|"entity"| X002461
    X002462["context | active_participant"]
    X002461 -->|"participant"| X002462
    X002463["literal | inventory"]
    X002461 -->|"entity_type"| X002463
    X002464["literal | balance"]
    X002460 -->|"key"| X002464
    X002465["literal | 3000"]
    X002459 -->|"b"| X002465
    E002466["effect[0]: complete_objective"]
    A002458 --> E002466
    X002467["context | self"]
    E002466 -->|"entity"| X002467
    A002468["moneyproperty: lot.fee_on_landing | hook | phase:resolve | hook:space.landed"]
    F046 -.-> A002468
    X002469["and"]
    A002468 -->|"condition"| X002469
    X002470["eq"]
    X002469 -->|"values[0]"| X002470
    X002471["field"]
    X002470 -->|"a"| X002471
    X002472["context | self"]
    X002471 -->|"entity"| X002472
    X002473["literal | location_kind"]
    X002471 -->|"key"| X002473
    X002474["literal | tax"]
    X002470 -->|"b"| X002474
    X002475["entity_at"]
    X002469 -->|"values[1]"| X002475
    X002476["context | self"]
    X002475 -->|"entity"| X002476
    X002477["context | active_participant"]
    X002475 -->|"participant"| X002477
    E002478["effect[0]: debit_resource"]
    A002468 --> E002478
    X002479["context | active_participant"]
    E002478 -->|"participant"| X002479
    X002480["field"]
    E002478 -->|"amount"| X002480
    X002481["context | self"]
    X002480 -->|"entity"| X002481
    X002482["literal | fee"]
    X002480 -->|"key"| X002482
    A002483["moneyproperty: lot.send_to_detention | hook | phase:resolve | hook:space.landed"]
    F046 -.-> A002483
    X002484["and"]
    A002483 -->|"condition"| X002484
    X002485["eq"]
    X002484 -->|"values[0]"| X002485
    X002486["field"]
    X002485 -->|"a"| X002486
    X002487["context | self"]
    X002486 -->|"entity"| X002487
    X002488["literal | location_kind"]
    X002486 -->|"key"| X002488
    X002489["literal | goto"]
    X002485 -->|"b"| X002489
    X002490["entity_at"]
    X002484 -->|"values[1]"| X002490
    X002491["context | self"]
    X002490 -->|"entity"| X002491
    X002492["context | active_participant"]
    X002490 -->|"participant"| X002492
    E002493["effect[0]: move_entity"]
    A002483 --> E002493
    X002494["entity_owned_by"]
    E002493 -->|"entity"| X002494
    X002495["context | active_participant"]
    X002494 -->|"participant"| X002495
    X002496["literal | token"]
    X002494 -->|"entity_type"| X002496
    X002497["entity_by_seed"]
    E002493 -->|"destination"| X002497
    X002498["literal | rest1"]
    X002497 -->|"key"| X002498
    E002499["effect[1]: set_field"]
    A002483 --> E002499
    X002500["entity_owned_by"]
    E002499 -->|"entity"| X002500
    X002501["context | active_participant"]
    X002500 -->|"participant"| X002501
    X002502["literal | token"]
    X002500 -->|"entity_type"| X002502
    X002503["literal | detained"]
    E002499 -->|"field"| X002503
    X002504["literal | True"]
    E002499 -->|"value"| X002504
    E002505["effect[2]: set_field"]
    A002483 --> E002505
    X002506["entity_owned_by"]
    E002505 -->|"entity"| X002506
    X002507["context | actor"]
    X002506 -->|"participant"| X002507
    X002508["literal | token"]
    X002506 -->|"entity_type"| X002508
    X002509["literal | detention_attempts"]
    E002505 -->|"field"| X002509
    X002510["literal | 0"]
    E002505 -->|"value"| X002510
    E002511["effect[3]: set_field"]
    A002483 --> E002511
    X002512["entity_owned_by"]
    E002511 -->|"entity"| X002512
    X002513["context | actor"]
    X002512 -->|"participant"| X002513
    X002514["literal | token"]
    X002512 -->|"entity_type"| X002514
    X002515["literal | doubles"]
    E002511 -->|"field"| X002515
    X002516["literal | 0"]
    E002511 -->|"value"| X002516
    A002517["moneyproperty: lot.start_reward | hook | phase:* | hook:space.passed"]
    F046 -.-> A002517
    X002518["eq"]
    A002517 -->|"condition"| X002518
    X002519["context | self"]
    X002518 -->|"a"| X002519
    X002520["entity_by_seed"]
    X002518 -->|"b"| X002520
    X002521["literal | start"]
    X002520 -->|"key"| X002521
    E002522["effect[0]: credit_resource"]
    A002517 --> E002522
    X002523["context | active_participant"]
    E002522 -->|"participant"| X002523
    X002524["literal | 200"]
    E002522 -->|"amount"| X002524
    A002525["moneyproperty: card.card_credit | hook | phase:* | hook:card.drawn"]
    F046 -.-> A002525
    X002526["and"]
    A002525 -->|"condition"| X002526
    X002527["eq"]
    X002526 -->|"values[0]"| X002527
    X002528["context | self"]
    X002527 -->|"a"| X002528
    X002529["context | drawn_card"]
    X002527 -->|"b"| X002529
    X002530["eq"]
    X002526 -->|"values[1]"| X002530
    X002531["field"]
    X002530 -->|"a"| X002531
    X002532["context | self"]
    X002531 -->|"entity"| X002532
    X002533["literal | operation"]
    X002531 -->|"key"| X002533
    X002534["literal | credit"]
    X002530 -->|"b"| X002534
    E002535["effect[0]: credit_resource"]
    A002525 --> E002535
    X002536["context | active_participant"]
    E002535 -->|"participant"| X002536
    X002537["field"]
    E002535 -->|"amount"| X002537
    X002538["context | self"]
    X002537 -->|"entity"| X002538
    X002539["literal | amount"]
    X002537 -->|"key"| X002539
    A002540["moneyproperty: card.card_debit | hook | phase:* | hook:card.drawn"]
    F046 -.-> A002540
    X002541["and"]
    A002540 -->|"condition"| X002541
    X002542["eq"]
    X002541 -->|"values[0]"| X002542
    X002543["context | self"]
    X002542 -->|"a"| X002543
    X002544["context | drawn_card"]
    X002542 -->|"b"| X002544
    X002545["eq"]
    X002541 -->|"values[1]"| X002545
    X002546["field"]
    X002545 -->|"a"| X002546
    X002547["context | self"]
    X002546 -->|"entity"| X002547
    X002548["literal | operation"]
    X002546 -->|"key"| X002548
    X002549["literal | debit"]
    X002545 -->|"b"| X002549
    E002550["effect[0]: debit_resource"]
    A002540 --> E002550
    X002551["context | active_participant"]
    E002550 -->|"participant"| X002551
    X002552["field"]
    E002550 -->|"amount"| X002552
    X002553["context | self"]
    X002552 -->|"entity"| X002553
    X002554["literal | amount"]
    X002552 -->|"key"| X002554
    A002555["moneyproperty: card.card_advance | hook | phase:* | hook:card.drawn"]
    F046 -.-> A002555
    X002556["and"]
    A002555 -->|"condition"| X002556
    X002557["eq"]
    X002556 -->|"values[0]"| X002557
    X002558["context | self"]
    X002557 -->|"a"| X002558
    X002559["context | drawn_card"]
    X002557 -->|"b"| X002559
    X002560["eq"]
    X002556 -->|"values[1]"| X002560
    X002561["field"]
    X002560 -->|"a"| X002561
    X002562["context | self"]
    X002561 -->|"entity"| X002562
    X002563["literal | operation"]
    X002561 -->|"key"| X002563
    X002564["literal | advance"]
    X002560 -->|"b"| X002564
    E002565["effect[0]: move_entity"]
    A002555 --> E002565
    X002566["entity_owned_by"]
    E002565 -->|"entity"| X002566
    X002567["context | active_participant"]
    X002566 -->|"participant"| X002567
    X002568["literal | token"]
    X002566 -->|"entity_type"| X002568
    X002569["entity_by_seed"]
    E002565 -->|"destination"| X002569
    X002570["literal | start"]
    X002569 -->|"key"| X002570
    A002571["moneyproperty: card.card_relative | hook | phase:* | hook:card.drawn"]
    F046 -.-> A002571
    X002572["and"]
    A002571 -->|"condition"| X002572
    X002573["eq"]
    X002572 -->|"values[0]"| X002573
    X002574["context | self"]
    X002573 -->|"a"| X002574
    X002575["context | drawn_card"]
    X002573 -->|"b"| X002575
    X002576["eq"]
    X002572 -->|"values[1]"| X002576
    X002577["field"]
    X002576 -->|"a"| X002577
    X002578["context | self"]
    X002577 -->|"entity"| X002578
    X002579["literal | operation"]
    X002577 -->|"key"| X002579
    X002580["literal | relative"]
    X002576 -->|"b"| X002580
    E002581["effect[0]: move_entity"]
    A002571 --> E002581
    X002582["entity_owned_by"]
    E002581 -->|"entity"| X002582
    X002583["context | active_participant"]
    X002582 -->|"participant"| X002583
    X002584["literal | token"]
    X002582 -->|"entity_type"| X002584
    X002585["path_last"]
    E002581 -->|"destination"| X002585
    X002586["track_advance"]
    X002585 -->|"path"| X002586
    X002587["entity_owned_by"]
    X002586 -->|"entity"| X002587
    X002588["context | active_participant"]
    X002587 -->|"participant"| X002588
    X002589["literal | token"]
    X002587 -->|"entity_type"| X002589
    X002590["field"]
    X002586 -->|"steps"| X002590
    X002591["context | self"]
    X002590 -->|"entity"| X002591
    X002592["literal | amount"]
    X002590 -->|"key"| X002592
    A002593["moneyproperty: game.roll_detained | command | phase:roll"]
    F046 -.-> A002593
    X002594["and"]
    A002593 -->|"condition"| X002594
    X002595["and"]
    X002594 -->|"values[0]"| X002595
    X002596["is_active"]
    X002595 -->|"values[0]"| X002596
    X002597["context | actor"]
    X002596 -->|"participant"| X002597
    X002598["phase_is"]
    X002595 -->|"values[1]"| X002598
    X002599["literal | roll"]
    X002598 -->|"phase"| X002599
    X002600["field"]
    X002594 -->|"values[1]"| X002600
    X002601["entity_owned_by"]
    X002600 -->|"entity"| X002601
    X002602["context | actor"]
    X002601 -->|"participant"| X002602
    X002603["literal | token"]
    X002601 -->|"entity_type"| X002603
    X002604["literal | detained"]
    X002600 -->|"key"| X002604
    E002605["effect[0]: trusted_random_int"]
    A002593 --> E002605
    X002606["literal | die1"]
    E002605 -->|"name"| X002606
    X002607["literal | 1"]
    E002605 -->|"lower"| X002607
    X002608["literal | 6"]
    E002605 -->|"upper"| X002608
    E002609["effect[1]: trusted_random_int"]
    A002593 --> E002609
    X002610["literal | die2"]
    E002609 -->|"name"| X002610
    X002611["literal | 1"]
    E002609 -->|"lower"| X002611
    X002612["literal | 6"]
    E002609 -->|"upper"| X002612
    E002613["effect[2]: set_field"]
    A002593 --> E002613
    X002614["context | self"]
    E002613 -->|"entity"| X002614
    X002615["literal | current_roll"]
    E002613 -->|"field"| X002615
    X002616["add"]
    E002613 -->|"value"| X002616
    X002617["context | random.die1"]
    X002616 -->|"a"| X002617
    X002618["context | random.die2"]
    X002616 -->|"b"| X002618
    E002619["effect[3]: set_field"]
    A002593 --> E002619
    X002620["entity_owned_by"]
    E002619 -->|"entity"| X002620
    X002621["context | actor"]
    X002620 -->|"participant"| X002621
    X002622["literal | token"]
    X002620 -->|"entity_type"| X002622
    X002623["literal | detention_attempts"]
    E002619 -->|"field"| X002623
    X002624["if"]
    E002619 -->|"value"| X002624
    X002625["eq"]
    X002624 -->|"condition"| X002625
    X002626["context | random.die1"]
    X002625 -->|"a"| X002626
    X002627["context | random.die2"]
    X002625 -->|"b"| X002627
    X002628["literal | 0"]
    X002624 -->|"then"| X002628
    X002629["add"]
    X002624 -->|"otherwise"| X002629
    X002630["field"]
    X002629 -->|"a"| X002630
    X002631["entity_owned_by"]
    X002630 -->|"entity"| X002631
    X002632["context | actor"]
    X002631 -->|"participant"| X002632
    X002633["literal | token"]
    X002631 -->|"entity_type"| X002633
    X002634["literal | detention_attempts"]
    X002630 -->|"key"| X002634
    X002635["literal | 1"]
    X002629 -->|"b"| X002635
    E002636["effect[4]: debit_resource"]
    A002593 --> E002636
    X002637["and"]
    E002636 -->|"when"| X002637
    X002638["not"]
    X002637 -->|"values[0]"| X002638
    X002639["eq"]
    X002638 -->|"value"| X002639
    X002640["context | random.die1"]
    X002639 -->|"a"| X002640
    X002641["context | random.die2"]
    X002639 -->|"b"| X002641
    X002642["gte"]
    X002637 -->|"values[1]"| X002642
    X002643["field"]
    X002642 -->|"a"| X002643
    X002644["entity_owned_by"]
    X002643 -->|"entity"| X002644
    X002645["context | actor"]
    X002644 -->|"participant"| X002645
    X002646["literal | token"]
    X002644 -->|"entity_type"| X002646
    X002647["literal | detention_attempts"]
    X002643 -->|"key"| X002647
    X002648["literal | 3"]
    X002642 -->|"b"| X002648
    X002649["context | actor"]
    E002636 -->|"participant"| X002649
    X002650["literal | 50"]
    E002636 -->|"amount"| X002650
    E002651["effect[5]: set_field"]
    A002593 --> E002651
    X002652["entity_owned_by"]
    E002651 -->|"entity"| X002652
    X002653["context | actor"]
    X002652 -->|"participant"| X002653
    X002654["literal | token"]
    X002652 -->|"entity_type"| X002654
    X002655["literal | detained"]
    E002651 -->|"field"| X002655
    X002656["not"]
    E002651 -->|"value"| X002656
    X002657["or"]
    X002656 -->|"value"| X002657
    X002658["eq"]
    X002657 -->|"values[0]"| X002658
    X002659["context | random.die1"]
    X002658 -->|"a"| X002659
    X002660["context | random.die2"]
    X002658 -->|"b"| X002660
    X002661["gte"]
    X002657 -->|"values[1]"| X002661
    X002662["field"]
    X002661 -->|"a"| X002662
    X002663["entity_owned_by"]
    X002662 -->|"entity"| X002663
    X002664["context | actor"]
    X002663 -->|"participant"| X002664
    X002665["literal | token"]
    X002663 -->|"entity_type"| X002665
    X002666["literal | detention_attempts"]
    X002662 -->|"key"| X002666
    X002667["literal | 3"]
    X002661 -->|"b"| X002667
    E002668["effect[6]: set_field"]
    A002593 --> E002668
    X002669["entity_owned_by"]
    E002668 -->|"entity"| X002669
    X002670["context | actor"]
    X002669 -->|"participant"| X002670
    X002671["literal | token"]
    X002669 -->|"entity_type"| X002671
    X002672["literal | doubles"]
    E002668 -->|"field"| X002672
    X002673["literal | 0"]
    E002668 -->|"value"| X002673
    E002674["effect[7]: set_phase"]
    A002593 --> E002674
    X002675["if"]
    E002674 -->|"phase"| X002675
    X002676["or"]
    X002675 -->|"condition"| X002676
    X002677["eq"]
    X002676 -->|"values[0]"| X002677
    X002678["context | random.die1"]
    X002677 -->|"a"| X002678
    X002679["context | random.die2"]
    X002677 -->|"b"| X002679
    X002680["gte"]
    X002676 -->|"values[1]"| X002680
    X002681["field"]
    X002680 -->|"a"| X002681
    X002682["entity_owned_by"]
    X002681 -->|"entity"| X002682
    X002683["context | actor"]
    X002682 -->|"participant"| X002683
    X002684["literal | token"]
    X002682 -->|"entity_type"| X002684
    X002685["literal | detention_attempts"]
    X002681 -->|"key"| X002685
    X002686["literal | 3"]
    X002680 -->|"b"| X002686
    X002687["literal | move"]
    X002675 -->|"then"| X002687
    X002688["literal | management"]
    X002675 -->|"otherwise"| X002688
    A002689["moneyproperty: game.pay_release | command | phase:roll"]
    F046 -.-> A002689
    X002690["and"]
    A002689 -->|"condition"| X002690
    X002691["and"]
    X002690 -->|"values[0]"| X002691
    X002692["is_active"]
    X002691 -->|"values[0]"| X002692
    X002693["context | actor"]
    X002692 -->|"participant"| X002693
    X002694["phase_is"]
    X002691 -->|"values[1]"| X002694
    X002695["literal | roll"]
    X002694 -->|"phase"| X002695
    X002696["field"]
    X002690 -->|"values[1]"| X002696
    X002697["entity_owned_by"]
    X002696 -->|"entity"| X002697
    X002698["context | actor"]
    X002697 -->|"participant"| X002698
    X002699["literal | token"]
    X002697 -->|"entity_type"| X002699
    X002700["literal | detained"]
    X002696 -->|"key"| X002700
    X002701["gte"]
    X002690 -->|"values[2]"| X002701
    X002702["field"]
    X002701 -->|"a"| X002702
    X002703["entity_owned_by"]
    X002702 -->|"entity"| X002703
    X002704["context | actor"]
    X002703 -->|"participant"| X002704
    X002705["literal | inventory"]
    X002703 -->|"entity_type"| X002705
    X002706["literal | balance"]
    X002702 -->|"key"| X002706
    X002707["literal | 50"]
    X002701 -->|"b"| X002707
    E002708["effect[0]: debit_resource"]
    A002689 --> E002708
    X002709["context | actor"]
    E002708 -->|"participant"| X002709
    X002710["literal | 50"]
    E002708 -->|"amount"| X002710
    E002711["effect[1]: set_field"]
    A002689 --> E002711
    X002712["entity_owned_by"]
    E002711 -->|"entity"| X002712
    X002713["context | actor"]
    X002712 -->|"participant"| X002713
    X002714["literal | token"]
    X002712 -->|"entity_type"| X002714
    X002715["literal | detained"]
    E002711 -->|"field"| X002715
    X002716["literal | False"]
    E002711 -->|"value"| X002716
    E002717["effect[2]: set_field"]
    A002689 --> E002717
    X002718["entity_owned_by"]
    E002717 -->|"entity"| X002718
    X002719["context | actor"]
    X002718 -->|"participant"| X002719
    X002720["literal | token"]
    X002718 -->|"entity_type"| X002720
    X002721["literal | detention_attempts"]
    E002717 -->|"field"| X002721
    X002722["literal | 0"]
    E002717 -->|"value"| X002722
  end
  %% ACTION_AST_COUNTS files=148 actions=72 expression_nodes=2722
```

