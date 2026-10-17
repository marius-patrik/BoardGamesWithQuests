# BoardGamesWithQuests

BoardGamesWithQuests is a configuration-driven multiplayer board-game platform. One React application runs on Vercel and in Tauri WebViews; a separate Vercel-hosted Python/FastAPI application executes a generic deterministic engine. Supabase PostgreSQL owns all authoritative state and declarative configurations; Supabase Storage holds raster presentation assets. Configuration JSON is portable interchange and is not authoritative database state.

This specification is organized into six sections. The normative relational schema and Mermaid AST are maintained separately in [SCHEMA](SCHEMA.md) and [AST](AST.md); the API and configuration data remain embedded below. Inline source comments are part of the documentation contract. The final repository must not acquire a second implementation of the UI or engine.

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

A game is `pending`, `active`, `finished`, or `expired`. The configured minimum participant count activates pending games once seats/roles are valid. Pending invitations expire after 24 hours. Games always pin one published version; published versions are immutable. A terminal game does not accept gameplay actions other than exact retries.

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

# 2. COMPONENTS

## 2.1 Technology and schema choice

| Responsibility | Authoritative implementation |
|---|---|
| Routing/UI | Wouter, React, TypeScript, Bun, Rsbuild, Tailwind CSS, shadcn/ui, Motion |
| Rendering | Generic SVG scene, typed visual templates and asset grants |
| Native | Tauri 2 WebView loading production HTTPS frontend, platform signing |
| API | Python FastAPI/Pydantic (separate Vercel project), cookie session, Origin/CSRF |
| Engine | Pure Python functional interpreter, no database/network dependencies |
| Database schema | **Drizzle PostgreSQL schema in TypeScript**, tooling-only package |
| Runtime DB client | Python psycopg, not Drizzle |
| Database and identity | Supabase PostgreSQL, Auth, private Broadcast, Storage |
| Migrations | Reviewed SQL generated from Drizzle; SQL-only security functions and triggers |
| API contract | OpenAPI 3.1 YAML and FastAPI conforming Pydantic models |
| Tests | pytest (engine/API/DB), Playwright (browser), native smoke checks |
| Documentation | Python docstrings, **TSDoc**, Rustdoc and OpenAPI summaries |

Supabase provides a native declarative schema workflow, but its source format is SQL. Drizzle works against Supabase PostgreSQL and provides a typed, more readable single-source **table schema**. Because the engine is Python, Drizzle is only build-time schema tooling: Python reads the provisioned database through psycopg. Postgres-specific triggers, secret-field authorization, published immutability, and private Broadcast still require reviewed SQL routines. There is deliberately no competing ORM runtime model in TypeScript.

The API and web deployments are separate Vercel projects; the web origin forwards `/api/*` to FastAPI. Native applications load that same HTTPS origin. Supabase owns Auth, relational state and Storage. Configurations are portable JSON, never the database's authoritative document format.

## 2.2 Exact intended tracked source tree

Every source path listed here has exactly one file node in the **single AST diagram** in [AST](AST.md). Generated build output, package caches, timestamped migration artifacts and generated native platform projects are not authored files.

```text
.
.agents/
  AST.md
  PRD.md
  SCHEMA.md
.github/
  workflows/
    deploy-api.yml
    deploy-web.yml
    release-native.yml
    verify.yml
packages/
  database/
    src/
      schema.ts
    drizzle.config.ts
    package.json
  native/
    src-tauri/
      capabilities/
        default.json
      icons/
        icon.icns
        icon.ico
        icon.png
      src/
        main.rs
      Cargo.lock
      Cargo.toml
      build.rs
      tauri.conf.json
    package.json
  server/
    api/
      __init__.py
      app.py
      assets.py
      contracts.py
      index.py
      openapi.yaml
      realtime.py
      repository.py
      routes.py
      security.py
      services.py
    configuration/
      __init__.py
      bootstrap.py
      configuration.schema.json
      models.py
      operator_contract.json
      transfer.py
      validation.py
    data/
      chess.json
      english-draughts.json
      international-draughts.json
      moneyproperty.json
    engine/
      __init__.py
      effects.py
      events.py
      expressions.py
      hooks.py
      model.py
      operators.py
      randomness.py
      reachability.py
      runtime.py
      topology.py
      types.py
    supabase/
      config.toml
      security.sql
      seed.sql
    pyproject.toml
    vercel.json
  web/
    src/
      api/
        assets.ts
        client.ts
        realtime.ts
        types.ts
      app/
        pages.tsx
        query.ts
        router.tsx
        session.tsx
      editor/
        ActionEditor.tsx
        AssetEditor.tsx
        DefinitionEditor.tsx
        EntityEditor.tsx
        ExpressionEditor.tsx
        RolePhaseEditor.tsx
        SpaceEditor.tsx
        TransferEditor.tsx
        VisualEditor.tsx
        useDraft.ts
      games/
        ActionPanel.tsx
        Clocks.tsx
        Decisions.tsx
        GameView.tsx
        History.tsx
        Invite.tsx
        ObjectivePanel.tsx
        Participants.tsx
        useGame.ts
      rendering/
        Accessibility.ts
        Animation.tsx
        Interactions.tsx
        Layout.ts
        Primitive.tsx
        Scene.tsx
      ui/
        button.tsx
        card.tsx
        dialog.tsx
        input.tsx
        select.tsx
        tabs.tsx
        toast.tsx
        tooltip.tsx
      App.tsx
      main.tsx
      styles.css
    components.json
    index.html
    package.json
    rsbuild.config.ts
    tsconfig.json
    vercel.json
tests/
  api/
    test_contract.py
    test_realtime.py
  browser/
    editor.spec.ts
    games.spec.ts
    package.json
    playwright.config.ts
    rendering.spec.ts
  configuration/
    test_assets.py
    test_roundtrip.py
  database/
    test_integrity.py
    test_schema.py
    test_transactions.py
  engine/
    test_chess.py
    test_draughts.py
    test_execution.py
    test_game_contracts.py
    test_moneyproperty.py
    test_reachability.py
  native/
    smoke.spec.ts
tools/
  build_docs.py
  build_operator_contract.py
  build_prd.py
  check_prd.py
  check_semantics.py
  check_spec.py
  generate_ast.py
  migrate_schema.py
  register_manifest.py
  sync_api_schema.py
.editorconfig
.env.example
.gitignore
LICENSE
README.md
bun.lock
package.json
tsconfig.json
tsdoc.json
typedoc.json
```

## 2.3 Package boundaries

`packages/database` declares all table/enum/index/FK/check structure. `packages/server/api` authenticates, authorizes, projects and transactionally persists; `engine` evaluates actions in pure immutable contexts; `configuration` imports/exports/validates JSON; `server/supabase` declares exceptional SQL routines, Auth/RealtIme policies, and data seed declarations. `packages/web` contains the only React UI and Wouter routes, including all concrete pages, the generic renderer and editor. `packages/native` is an HTTPS WebView wrapper only.

`packages/server/supabase/security.sql` intentionally contains the only authored SQL DDL not expressible as ordinary Drizzle tables: security grants/policies, publication immutability triggers and private revision broadcasts. Drizzle-generated versioned SQL migrations remain reviewed deployment artifacts. `seed.sql` contains registry/reference DML and Storage bucket initialization, never authoritative game definitions.

# 3. API

The OpenAPI 3.1 schema is the authoritative HTTP contract. Every schema reference resolves locally, and the embedded `ConfigDocument` is byte-equivalent after normalization to the portable JSON Schema in DATA.

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
      summary: Read session
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
      properties:
        definition_id: *id001
        version: *id003
        idempotency_key: *id002
    GameSummary:
      type: object
      additionalProperties: false
      required:
      - id
      - status
      - revision
      - definition
      properties:
        id: *id001
        status:
          enum:
          - pending
          - active
          - finished
          - expired
        revision: *id003
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
      - participants
      - entities
      - available_actions
      - server_time
      properties:
        id: *id001
        status:
          enum:
          - pending
          - active
          - finished
          - expired
        revision: *id003
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
    Invitation:
      type: object
      additionalProperties: false
      required:
      - game_id
      - status
      - expires_at
      - definition
      properties:
        game_id: *id001
        status:
          enum:
          - pending
          - active
          - expired
        expires_at: *id004
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
      description: Versioned, portable authoring format; database stores its normalized relational projection.
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
```

# 4. SCHEMA

The canonical, inline-documented Drizzle PostgreSQL schema and database security/Realtime routines are in **[SCHEMA.md](SCHEMA.md)**. This file is the sole normative schema declaration; implementation must conform to it.

# 5. AST

The canonical source-file, declaration, dependency, and game-configuration Mermaid AST is in **[AST.md](AST.md)**. Each declared source path corresponds to one node in that diagram, including the two architecture documents.

# 6. DATA

## 6.1 Portable JSON schema

The following JSON Schema is the exact portable interchange contract. Its `ConfigDocument` representation inside OpenAPI is mechanically checked for equivalence.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:bgwq:configuration:v1",
  "title": "BoardGamesWithQuests portable configuration v1",
  "description": "Versioned, portable authoring format; database stores its normalized relational projection.",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "format",
    "format_version",
    "definition",
    "roles",
    "phases",
    "entities",
    "seeds",
    "links",
    "fields",
    "actions",
    "visuals",
    "assets"
  ],
  "properties": {
    "format": {
      "const": "bgwq.configuration"
    },
    "format_version": {
      "const": 1
    },
    "definition": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "key",
        "name",
        "min_participants",
        "max_participants"
      ],
      "properties": {
        "key": {
          "$ref": "#/$defs/key"
        },
        "name": {
          "type": "string",
          "minLength": 1
        },
        "description": {
          "type": "string"
        },
        "min_participants": {
          "type": "integer",
          "minimum": 1,
          "maximum": 64
        },
        "max_participants": {
          "type": "integer",
          "minimum": 1,
          "maximum": 64
        },
        "semantics_version": {
          "const": 1
        }
      }
    },
    "roles": {
      "type": "array",
      "items": {
        "$ref": "#/$defs/role"
      }
    },
    "phases": {
      "type": "array",
      "minItems": 1,
      "items": {
        "$ref": "#/$defs/phase"
      }
    },
    "entities": {
      "type": "array",
      "minItems": 1,
      "items": {
        "$ref": "#/$defs/entity"
      }
    },
    "seeds": {
      "type": "array",
      "minItems": 1,
      "items": {
        "$ref": "#/$defs/seed"
      }
    },
    "links": {
      "type": "array",
      "items": {
        "$ref": "#/$defs/link"
      }
    },
    "fields": {
      "type": "array",
      "items": {
        "$ref": "#/$defs/field"
      }
    },
    "actions": {
      "type": "array",
      "minItems": 1,
      "items": {
        "$ref": "#/$defs/action"
      }
    },
    "visuals": {
      "type": "array",
      "items": {
        "$ref": "#/$defs/visual"
      }
    },
    "assets": {
      "type": "array",
      "items": {
        "$ref": "#/$defs/asset"
      }
    }
  },
  "$defs": {
    "key": {
      "type": "string",
      "pattern": "^[a-z][a-z0-9_.-]*$"
    },
    "role": {
      "type": "object",
      "required": [
        "key",
        "name",
        "min",
        "max"
      ],
      "additionalProperties": false,
      "properties": {
        "key": {
          "$ref": "#/$defs/key"
        },
        "name": {
          "type": "string"
        },
        "min": {
          "type": "integer",
          "minimum": 0
        },
        "max": {
          "type": "integer",
          "minimum": 0
        },
        "forward_row": {
          "type": [
            "integer",
            "null"
          ],
          "enum": [
            -1,
            1,
            null
          ],
          "description": "Optional forward row orientation used by generic relative-vector operations."
        }
      }
    },
    "phase": {
      "type": "object",
      "required": [
        "key",
        "name",
        "initial",
        "order"
      ],
      "additionalProperties": false,
      "properties": {
        "key": {
          "$ref": "#/$defs/key"
        },
        "name": {
          "type": "string"
        },
        "initial": {
          "type": "boolean"
        },
        "order": {
          "type": "integer"
        }
      }
    },
    "entity": {
      "type": "object",
      "required": [
        "key",
        "kind",
        "name"
      ],
      "additionalProperties": false,
      "properties": {
        "key": {
          "$ref": "#/$defs/key"
        },
        "kind": {
          "enum": [
            "game",
            "space",
            "item",
            "objective"
          ]
        },
        "name": {
          "type": "string"
        }
      }
    },
    "seed": {
      "type": "object",
      "required": [
        "key",
        "type"
      ],
      "additionalProperties": false,
      "properties": {
        "key": {
          "$ref": "#/$defs/key"
        },
        "type": {
          "$ref": "#/$defs/key"
        },
        "owner": {
          "type": "integer",
          "minimum": 0
        },
        "parent": {
          "$ref": "#/$defs/key"
        },
        "location": {
          "$ref": "#/$defs/key"
        },
        "order": {
          "type": "integer"
        },
        "row": {
          "type": "integer"
        },
        "column": {
          "type": "integer"
        },
        "x": {
          "type": "number"
        },
        "y": {
          "type": "number"
        },
        "values": {
          "type": "object",
          "additionalProperties": {
            "$ref": "#/$defs/value"
          }
        }
      }
    },
    "link": {
      "type": "object",
      "required": [
        "source",
        "target",
        "relation"
      ],
      "additionalProperties": false,
      "properties": {
        "source": {
          "$ref": "#/$defs/key"
        },
        "target": {
          "$ref": "#/$defs/key"
        },
        "relation": {
          "$ref": "#/$defs/key"
        },
        "order": {
          "type": "integer"
        }
      }
    },
    "field": {
      "type": "object",
      "required": [
        "entity",
        "key",
        "type"
      ],
      "additionalProperties": false,
      "properties": {
        "entity": {
          "$ref": "#/$defs/key"
        },
        "key": {
          "$ref": "#/$defs/key"
        },
        "type": {
          "enum": [
            "bool",
            "int",
            "decimal",
            "text",
            "instant",
            "entity",
            "participant"
          ]
        },
        "nullable": {
          "type": "boolean"
        },
        "default": {
          "$ref": "#/$defs/value"
        }
      }
    },
    "value": {
      "type": [
        "boolean",
        "integer",
        "number",
        "string",
        "null"
      ]
    },
    "expression": {
      "type": "object",
      "required": [
        "op"
      ],
      "additionalProperties": false,
      "properties": {
        "op": {
          "$ref": "#/$defs/key"
        },
        "args": {
          "type": "object",
          "additionalProperties": {
            "anyOf": [
              {
                "$ref": "#/$defs/expression"
              },
              {
                "type": "array",
                "items": {
                  "$ref": "#/$defs/expression"
                }
              }
            ]
          }
        },
        "value": {
          "$ref": "#/$defs/value"
        },
        "ref": {
          "type": "string"
        },
        "type": {
          "type": "string"
        }
      }
    },
    "effect": {
      "type": "object",
      "required": [
        "op"
      ],
      "additionalProperties": false,
      "properties": {
        "op": {
          "$ref": "#/$defs/key"
        },
        "when": {
          "$ref": "#/$defs/expression"
        },
        "args": {
          "type": "object",
          "additionalProperties": {
            "anyOf": [
              {
                "$ref": "#/$defs/expression"
              },
              {
                "type": "array",
                "items": {
                  "$ref": "#/$defs/expression"
                }
              }
            ]
          }
        }
      }
    },
    "action": {
      "type": "object",
      "required": [
        "key",
        "entity",
        "trigger",
        "phase",
        "condition",
        "effects"
      ],
      "additionalProperties": false,
      "properties": {
        "key": {
          "$ref": "#/$defs/key"
        },
        "entity": {
          "$ref": "#/$defs/key"
        },
        "name": {
          "type": "string"
        },
        "trigger": {
          "enum": [
            "command",
            "hook"
          ]
        },
        "hook": {
          "type": "string"
        },
        "phase": {
          "type": "string"
        },
        "parameters": {
          "type": "array",
          "items": {
            "type": "object",
            "required": [
              "key",
              "type"
            ],
            "additionalProperties": false,
            "properties": {
              "key": {
                "$ref": "#/$defs/key"
              },
              "type": {
                "type": "string"
              },
              "required": {
                "type": "boolean"
              },
              "choices": {
                "type": "array",
                "minItems": 1,
                "uniqueItems": true,
                "items": {
                  "type": "string"
                }
              }
            }
          }
        },
        "iterator": {
          "$ref": "#/$defs/expression"
        },
        "variable": {
          "type": "string"
        },
        "condition": {
          "$ref": "#/$defs/expression"
        },
        "effects": {
          "type": "array",
          "items": {
            "$ref": "#/$defs/effect"
          }
        },
        "priority": {
          "type": "integer"
        }
      }
    },
    "visual": {
      "type": "object",
      "required": [
        "entity",
        "primitives"
      ],
      "additionalProperties": false,
      "properties": {
        "entity": {
          "$ref": "#/$defs/key"
        },
        "primitives": {
          "type": "array",
          "items": {
            "type": "object",
            "required": [
              "kind"
            ],
            "additionalProperties": false,
            "properties": {
              "kind": {
                "enum": [
                  "rectangle",
                  "ellipse",
                  "line",
                  "path",
                  "text",
                  "image"
                ]
              },
              "x": {
                "type": "number"
              },
              "y": {
                "type": "number"
              },
              "width": {
                "type": "number"
              },
              "height": {
                "type": "number"
              },
              "fill": {
                "type": "string"
              },
              "stroke": {
                "type": "string"
              },
              "d": {
                "type": "string"
              },
              "text": {
                "type": "string"
              },
              "asset": {
                "type": "string"
              },
              "layer": {
                "type": "integer"
              }
            }
          }
        }
      }
    },
    "asset": {
      "type": "object",
      "required": [
        "key",
        "mime",
        "sha256",
        "base64"
      ],
      "additionalProperties": false,
      "properties": {
        "key": {
          "$ref": "#/$defs/key"
        },
        "mime": {
          "enum": [
            "image/png",
            "image/webp"
          ]
        },
        "sha256": {
          "type": "string",
          "pattern": "^[0-9a-f]{64}$"
        },
        "base64": {
          "type": "string"
        }
      }
    }
  }
}
```

## 6.2 Built-in definition data

All four documents are complete structural instances of the interchange schema. Every operator used in their conditions and effects must have an exact generic signature and implementation before the game can be considered executable.

### chess.json

```json
{
  "format": "bgwq.configuration",
  "format_version": 1,
  "definition": {
    "key": "chess",
    "name": "Orthodox Chess",
    "min_participants": 2,
    "max_participants": 2,
    "semantics_version": 1
  },
  "roles": [
    {
      "key": "seat_0",
      "name": "Player 1",
      "min": 1,
      "max": 1,
      "forward_row": 1
    },
    {
      "key": "seat_1",
      "name": "Player 2",
      "min": 1,
      "max": 1,
      "forward_row": -1
    }
  ],
  "phases": [
    {
      "key": "turn",
      "name": "Turn",
      "initial": true,
      "order": 0
    }
  ],
  "entities": [
    {
      "key": "chess_game",
      "kind": "game",
      "name": "Chess Game"
    },
    {
      "key": "chess_board",
      "kind": "space",
      "name": "Chess Board"
    },
    {
      "key": "square",
      "kind": "space",
      "name": "Square"
    },
    {
      "key": "king",
      "kind": "item",
      "name": "King"
    },
    {
      "key": "queen",
      "kind": "item",
      "name": "Queen"
    },
    {
      "key": "rook",
      "kind": "item",
      "name": "Rook"
    },
    {
      "key": "bishop",
      "kind": "item",
      "name": "Bishop"
    },
    {
      "key": "knight",
      "kind": "item",
      "name": "Knight"
    },
    {
      "key": "pawn",
      "kind": "item",
      "name": "Pawn"
    },
    {
      "key": "checkmate",
      "kind": "objective",
      "name": "Checkmate"
    },
    {
      "key": "stalemate",
      "kind": "objective",
      "name": "Stalemate"
    },
    {
      "key": "dead_position",
      "kind": "objective",
      "name": "Dead Position"
    },
    {
      "key": "repetition_draw",
      "kind": "objective",
      "name": "Repetition Draw"
    },
    {
      "key": "move_count_draw",
      "kind": "objective",
      "name": "Move Count Draw"
    },
    {
      "key": "timeout",
      "kind": "objective",
      "name": "Timeout"
    },
    {
      "key": "capture_quest",
      "kind": "objective",
      "name": "Capture Quest"
    },
    {
      "key": "promotion_quest",
      "kind": "objective",
      "name": "Promotion Quest"
    },
    {
      "key": "castling_quest",
      "kind": "objective",
      "name": "Castling Quest"
    }
  ],
  "seeds": [
    {
      "key": "root",
      "type": "chess_game"
    },
    {
      "key": "board",
      "type": "chess_board",
      "parent": "root"
    },
    {
      "key": "a1",
      "type": "square",
      "parent": "board",
      "row": 0,
      "column": 0,
      "x": 0,
      "y": 700,
      "values": {
        "light": false
      }
    },
    {
      "key": "b1",
      "type": "square",
      "parent": "board",
      "row": 0,
      "column": 1,
      "x": 100,
      "y": 700,
      "values": {
        "light": true
      }
    },
    {
      "key": "c1",
      "type": "square",
      "parent": "board",
      "row": 0,
      "column": 2,
      "x": 200,
      "y": 700,
      "values": {
        "light": false
      }
    },
    {
      "key": "d1",
      "type": "square",
      "parent": "board",
      "row": 0,
      "column": 3,
      "x": 300,
      "y": 700,
      "values": {
        "light": true
      }
    },
    {
      "key": "e1",
      "type": "square",
      "parent": "board",
      "row": 0,
      "column": 4,
      "x": 400,
      "y": 700,
      "values": {
        "light": false
      }
    },
    {
      "key": "f1",
      "type": "square",
      "parent": "board",
      "row": 0,
      "column": 5,
      "x": 500,
      "y": 700,
      "values": {
        "light": true
      }
    },
    {
      "key": "g1",
      "type": "square",
      "parent": "board",
      "row": 0,
      "column": 6,
      "x": 600,
      "y": 700,
      "values": {
        "light": false
      }
    },
    {
      "key": "h1",
      "type": "square",
      "parent": "board",
      "row": 0,
      "column": 7,
      "x": 700,
      "y": 700,
      "values": {
        "light": true
      }
    },
    {
      "key": "a2",
      "type": "square",
      "parent": "board",
      "row": 1,
      "column": 0,
      "x": 0,
      "y": 600,
      "values": {
        "light": true
      }
    },
    {
      "key": "b2",
      "type": "square",
      "parent": "board",
      "row": 1,
      "column": 1,
      "x": 100,
      "y": 600,
      "values": {
        "light": false
      }
    },
    {
      "key": "c2",
      "type": "square",
      "parent": "board",
      "row": 1,
      "column": 2,
      "x": 200,
      "y": 600,
      "values": {
        "light": true
      }
    },
    {
      "key": "d2",
      "type": "square",
      "parent": "board",
      "row": 1,
      "column": 3,
      "x": 300,
      "y": 600,
      "values": {
        "light": false
      }
    },
    {
      "key": "e2",
      "type": "square",
      "parent": "board",
      "row": 1,
      "column": 4,
      "x": 400,
      "y": 600,
      "values": {
        "light": true
      }
    },
    {
      "key": "f2",
      "type": "square",
      "parent": "board",
      "row": 1,
      "column": 5,
      "x": 500,
      "y": 600,
      "values": {
        "light": false
      }
    },
    {
      "key": "g2",
      "type": "square",
      "parent": "board",
      "row": 1,
      "column": 6,
      "x": 600,
      "y": 600,
      "values": {
        "light": true
      }
    },
    {
      "key": "h2",
      "type": "square",
      "parent": "board",
      "row": 1,
      "column": 7,
      "x": 700,
      "y": 600,
      "values": {
        "light": false
      }
    },
    {
      "key": "a3",
      "type": "square",
      "parent": "board",
      "row": 2,
      "column": 0,
      "x": 0,
      "y": 500,
      "values": {
        "light": false
      }
    },
    {
      "key": "b3",
      "type": "square",
      "parent": "board",
      "row": 2,
      "column": 1,
      "x": 100,
      "y": 500,
      "values": {
        "light": true
      }
    },
    {
      "key": "c3",
      "type": "square",
      "parent": "board",
      "row": 2,
      "column": 2,
      "x": 200,
      "y": 500,
      "values": {
        "light": false
      }
    },
    {
      "key": "d3",
      "type": "square",
      "parent": "board",
      "row": 2,
      "column": 3,
      "x": 300,
      "y": 500,
      "values": {
        "light": true
      }
    },
    {
      "key": "e3",
      "type": "square",
      "parent": "board",
      "row": 2,
      "column": 4,
      "x": 400,
      "y": 500,
      "values": {
        "light": false
      }
    },
    {
      "key": "f3",
      "type": "square",
      "parent": "board",
      "row": 2,
      "column": 5,
      "x": 500,
      "y": 500,
      "values": {
        "light": true
      }
    },
    {
      "key": "g3",
      "type": "square",
      "parent": "board",
      "row": 2,
      "column": 6,
      "x": 600,
      "y": 500,
      "values": {
        "light": false
      }
    },
    {
      "key": "h3",
      "type": "square",
      "parent": "board",
      "row": 2,
      "column": 7,
      "x": 700,
      "y": 500,
      "values": {
        "light": true
      }
    },
    {
      "key": "a4",
      "type": "square",
      "parent": "board",
      "row": 3,
      "column": 0,
      "x": 0,
      "y": 400,
      "values": {
        "light": true
      }
    },
    {
      "key": "b4",
      "type": "square",
      "parent": "board",
      "row": 3,
      "column": 1,
      "x": 100,
      "y": 400,
      "values": {
        "light": false
      }
    },
    {
      "key": "c4",
      "type": "square",
      "parent": "board",
      "row": 3,
      "column": 2,
      "x": 200,
      "y": 400,
      "values": {
        "light": true
      }
    },
    {
      "key": "d4",
      "type": "square",
      "parent": "board",
      "row": 3,
      "column": 3,
      "x": 300,
      "y": 400,
      "values": {
        "light": false
      }
    },
    {
      "key": "e4",
      "type": "square",
      "parent": "board",
      "row": 3,
      "column": 4,
      "x": 400,
      "y": 400,
      "values": {
        "light": true
      }
    },
    {
      "key": "f4",
      "type": "square",
      "parent": "board",
      "row": 3,
      "column": 5,
      "x": 500,
      "y": 400,
      "values": {
        "light": false
      }
    },
    {
      "key": "g4",
      "type": "square",
      "parent": "board",
      "row": 3,
      "column": 6,
      "x": 600,
      "y": 400,
      "values": {
        "light": true
      }
    },
    {
      "key": "h4",
      "type": "square",
      "parent": "board",
      "row": 3,
      "column": 7,
      "x": 700,
      "y": 400,
      "values": {
        "light": false
      }
    },
    {
      "key": "a5",
      "type": "square",
      "parent": "board",
      "row": 4,
      "column": 0,
      "x": 0,
      "y": 300,
      "values": {
        "light": false
      }
    },
    {
      "key": "b5",
      "type": "square",
      "parent": "board",
      "row": 4,
      "column": 1,
      "x": 100,
      "y": 300,
      "values": {
        "light": true
      }
    },
    {
      "key": "c5",
      "type": "square",
      "parent": "board",
      "row": 4,
      "column": 2,
      "x": 200,
      "y": 300,
      "values": {
        "light": false
      }
    },
    {
      "key": "d5",
      "type": "square",
      "parent": "board",
      "row": 4,
      "column": 3,
      "x": 300,
      "y": 300,
      "values": {
        "light": true
      }
    },
    {
      "key": "e5",
      "type": "square",
      "parent": "board",
      "row": 4,
      "column": 4,
      "x": 400,
      "y": 300,
      "values": {
        "light": false
      }
    },
    {
      "key": "f5",
      "type": "square",
      "parent": "board",
      "row": 4,
      "column": 5,
      "x": 500,
      "y": 300,
      "values": {
        "light": true
      }
    },
    {
      "key": "g5",
      "type": "square",
      "parent": "board",
      "row": 4,
      "column": 6,
      "x": 600,
      "y": 300,
      "values": {
        "light": false
      }
    },
    {
      "key": "h5",
      "type": "square",
      "parent": "board",
      "row": 4,
      "column": 7,
      "x": 700,
      "y": 300,
      "values": {
        "light": true
      }
    },
    {
      "key": "a6",
      "type": "square",
      "parent": "board",
      "row": 5,
      "column": 0,
      "x": 0,
      "y": 200,
      "values": {
        "light": true
      }
    },
    {
      "key": "b6",
      "type": "square",
      "parent": "board",
      "row": 5,
      "column": 1,
      "x": 100,
      "y": 200,
      "values": {
        "light": false
      }
    },
    {
      "key": "c6",
      "type": "square",
      "parent": "board",
      "row": 5,
      "column": 2,
      "x": 200,
      "y": 200,
      "values": {
        "light": true
      }
    },
    {
      "key": "d6",
      "type": "square",
      "parent": "board",
      "row": 5,
      "column": 3,
      "x": 300,
      "y": 200,
      "values": {
        "light": false
      }
    },
    {
      "key": "e6",
      "type": "square",
      "parent": "board",
      "row": 5,
      "column": 4,
      "x": 400,
      "y": 200,
      "values": {
        "light": true
      }
    },
    {
      "key": "f6",
      "type": "square",
      "parent": "board",
      "row": 5,
      "column": 5,
      "x": 500,
      "y": 200,
      "values": {
        "light": false
      }
    },
    {
      "key": "g6",
      "type": "square",
      "parent": "board",
      "row": 5,
      "column": 6,
      "x": 600,
      "y": 200,
      "values": {
        "light": true
      }
    },
    {
      "key": "h6",
      "type": "square",
      "parent": "board",
      "row": 5,
      "column": 7,
      "x": 700,
      "y": 200,
      "values": {
        "light": false
      }
    },
    {
      "key": "a7",
      "type": "square",
      "parent": "board",
      "row": 6,
      "column": 0,
      "x": 0,
      "y": 100,
      "values": {
        "light": false
      }
    },
    {
      "key": "b7",
      "type": "square",
      "parent": "board",
      "row": 6,
      "column": 1,
      "x": 100,
      "y": 100,
      "values": {
        "light": true
      }
    },
    {
      "key": "c7",
      "type": "square",
      "parent": "board",
      "row": 6,
      "column": 2,
      "x": 200,
      "y": 100,
      "values": {
        "light": false
      }
    },
    {
      "key": "d7",
      "type": "square",
      "parent": "board",
      "row": 6,
      "column": 3,
      "x": 300,
      "y": 100,
      "values": {
        "light": true
      }
    },
    {
      "key": "e7",
      "type": "square",
      "parent": "board",
      "row": 6,
      "column": 4,
      "x": 400,
      "y": 100,
      "values": {
        "light": false
      }
    },
    {
      "key": "f7",
      "type": "square",
      "parent": "board",
      "row": 6,
      "column": 5,
      "x": 500,
      "y": 100,
      "values": {
        "light": true
      }
    },
    {
      "key": "g7",
      "type": "square",
      "parent": "board",
      "row": 6,
      "column": 6,
      "x": 600,
      "y": 100,
      "values": {
        "light": false
      }
    },
    {
      "key": "h7",
      "type": "square",
      "parent": "board",
      "row": 6,
      "column": 7,
      "x": 700,
      "y": 100,
      "values": {
        "light": true
      }
    },
    {
      "key": "a8",
      "type": "square",
      "parent": "board",
      "row": 7,
      "column": 0,
      "x": 0,
      "y": 0,
      "values": {
        "light": true
      }
    },
    {
      "key": "b8",
      "type": "square",
      "parent": "board",
      "row": 7,
      "column": 1,
      "x": 100,
      "y": 0,
      "values": {
        "light": false
      }
    },
    {
      "key": "c8",
      "type": "square",
      "parent": "board",
      "row": 7,
      "column": 2,
      "x": 200,
      "y": 0,
      "values": {
        "light": true
      }
    },
    {
      "key": "d8",
      "type": "square",
      "parent": "board",
      "row": 7,
      "column": 3,
      "x": 300,
      "y": 0,
      "values": {
        "light": false
      }
    },
    {
      "key": "e8",
      "type": "square",
      "parent": "board",
      "row": 7,
      "column": 4,
      "x": 400,
      "y": 0,
      "values": {
        "light": true
      }
    },
    {
      "key": "f8",
      "type": "square",
      "parent": "board",
      "row": 7,
      "column": 5,
      "x": 500,
      "y": 0,
      "values": {
        "light": false
      }
    },
    {
      "key": "g8",
      "type": "square",
      "parent": "board",
      "row": 7,
      "column": 6,
      "x": 600,
      "y": 0,
      "values": {
        "light": true
      }
    },
    {
      "key": "h8",
      "type": "square",
      "parent": "board",
      "row": 7,
      "column": 7,
      "x": 700,
      "y": 0,
      "values": {
        "light": false
      }
    },
    {
      "key": "king_0_4",
      "type": "king",
      "owner": 0,
      "location": "e1",
      "values": {
        "moved": false
      }
    },
    {
      "key": "king_1_4",
      "type": "king",
      "owner": 1,
      "location": "e8",
      "values": {
        "moved": false
      }
    },
    {
      "key": "queen_0_3",
      "type": "queen",
      "owner": 0,
      "location": "d1",
      "values": {
        "moved": false
      }
    },
    {
      "key": "queen_1_3",
      "type": "queen",
      "owner": 1,
      "location": "d8",
      "values": {
        "moved": false
      }
    },
    {
      "key": "rook_0_0",
      "type": "rook",
      "owner": 0,
      "location": "a1",
      "values": {
        "moved": false
      }
    },
    {
      "key": "rook_0_7",
      "type": "rook",
      "owner": 0,
      "location": "h1",
      "values": {
        "moved": false
      }
    },
    {
      "key": "rook_1_0",
      "type": "rook",
      "owner": 1,
      "location": "a8",
      "values": {
        "moved": false
      }
    },
    {
      "key": "rook_1_7",
      "type": "rook",
      "owner": 1,
      "location": "h8",
      "values": {
        "moved": false
      }
    },
    {
      "key": "bishop_0_2",
      "type": "bishop",
      "owner": 0,
      "location": "c1",
      "values": {
        "moved": false
      }
    },
    {
      "key": "bishop_0_5",
      "type": "bishop",
      "owner": 0,
      "location": "f1",
      "values": {
        "moved": false
      }
    },
    {
      "key": "bishop_1_2",
      "type": "bishop",
      "owner": 1,
      "location": "c8",
      "values": {
        "moved": false
      }
    },
    {
      "key": "bishop_1_5",
      "type": "bishop",
      "owner": 1,
      "location": "f8",
      "values": {
        "moved": false
      }
    },
    {
      "key": "knight_0_1",
      "type": "knight",
      "owner": 0,
      "location": "b1",
      "values": {
        "moved": false
      }
    },
    {
      "key": "knight_0_6",
      "type": "knight",
      "owner": 0,
      "location": "g1",
      "values": {
        "moved": false
      }
    },
    {
      "key": "knight_1_1",
      "type": "knight",
      "owner": 1,
      "location": "b8",
      "values": {
        "moved": false
      }
    },
    {
      "key": "knight_1_6",
      "type": "knight",
      "owner": 1,
      "location": "g8",
      "values": {
        "moved": false
      }
    },
    {
      "key": "pawn_0_0",
      "type": "pawn",
      "owner": 0,
      "location": "a2",
      "values": {
        "moved": false
      }
    },
    {
      "key": "pawn_0_1",
      "type": "pawn",
      "owner": 0,
      "location": "b2",
      "values": {
        "moved": false
      }
    },
    {
      "key": "pawn_0_2",
      "type": "pawn",
      "owner": 0,
      "location": "c2",
      "values": {
        "moved": false
      }
    },
    {
      "key": "pawn_0_3",
      "type": "pawn",
      "owner": 0,
      "location": "d2",
      "values": {
        "moved": false
      }
    },
    {
      "key": "pawn_0_4",
      "type": "pawn",
      "owner": 0,
      "location": "e2",
      "values": {
        "moved": false
      }
    },
    {
      "key": "pawn_0_5",
      "type": "pawn",
      "owner": 0,
      "location": "f2",
      "values": {
        "moved": false
      }
    },
    {
      "key": "pawn_0_6",
      "type": "pawn",
      "owner": 0,
      "location": "g2",
      "values": {
        "moved": false
      }
    },
    {
      "key": "pawn_0_7",
      "type": "pawn",
      "owner": 0,
      "location": "h2",
      "values": {
        "moved": false
      }
    },
    {
      "key": "pawn_1_0",
      "type": "pawn",
      "owner": 1,
      "location": "a7",
      "values": {
        "moved": false
      }
    },
    {
      "key": "pawn_1_1",
      "type": "pawn",
      "owner": 1,
      "location": "b7",
      "values": {
        "moved": false
      }
    },
    {
      "key": "pawn_1_2",
      "type": "pawn",
      "owner": 1,
      "location": "c7",
      "values": {
        "moved": false
      }
    },
    {
      "key": "pawn_1_3",
      "type": "pawn",
      "owner": 1,
      "location": "d7",
      "values": {
        "moved": false
      }
    },
    {
      "key": "pawn_1_4",
      "type": "pawn",
      "owner": 1,
      "location": "e7",
      "values": {
        "moved": false
      }
    },
    {
      "key": "pawn_1_5",
      "type": "pawn",
      "owner": 1,
      "location": "f7",
      "values": {
        "moved": false
      }
    },
    {
      "key": "pawn_1_6",
      "type": "pawn",
      "owner": 1,
      "location": "g7",
      "values": {
        "moved": false
      }
    },
    {
      "key": "pawn_1_7",
      "type": "pawn",
      "owner": 1,
      "location": "h7",
      "values": {
        "moved": false
      }
    },
    {
      "key": "objective_checkmate",
      "type": "checkmate",
      "parent": "root",
      "values": {
        "progress": 0,
        "completed": false
      }
    },
    {
      "key": "objective_stalemate",
      "type": "stalemate",
      "parent": "root",
      "values": {
        "progress": 0,
        "completed": false
      }
    },
    {
      "key": "objective_dead_position",
      "type": "dead_position",
      "parent": "root",
      "values": {
        "progress": 0,
        "completed": false
      }
    },
    {
      "key": "objective_repetition_draw",
      "type": "repetition_draw",
      "parent": "root",
      "values": {
        "progress": 0,
        "completed": false
      }
    },
    {
      "key": "objective_move_count_draw",
      "type": "move_count_draw",
      "parent": "root",
      "values": {
        "progress": 0,
        "completed": false
      }
    },
    {
      "key": "objective_timeout",
      "type": "timeout",
      "parent": "root",
      "values": {
        "progress": 0,
        "completed": false
      }
    },
    {
      "key": "objective_capture_quest",
      "type": "capture_quest",
      "parent": "root",
      "values": {
        "progress": 0,
        "completed": false,
        "target": 3
      }
    },
    {
      "key": "objective_promotion_quest",
      "type": "promotion_quest",
      "parent": "root",
      "values": {
        "progress": 0,
        "completed": false,
        "target": 1
      }
    },
    {
      "key": "objective_castling_quest",
      "type": "castling_quest",
      "parent": "root",
      "values": {
        "progress": 0,
        "completed": false,
        "target": 1
      }
    }
  ],
  "links": [],
  "fields": [
    {
      "entity": "chess_game",
      "key": "active_seat",
      "type": "int"
    },
    {
      "entity": "chess_game",
      "key": "halfmove",
      "type": "int"
    },
    {
      "entity": "chess_game",
      "key": "fullmove",
      "type": "int"
    },
    {
      "entity": "chess_game",
      "key": "en_passant",
      "type": "entity"
    },
    {
      "entity": "chess_game",
      "key": "castle_white_k",
      "type": "bool"
    },
    {
      "entity": "chess_game",
      "key": "castle_white_q",
      "type": "bool"
    },
    {
      "entity": "chess_game",
      "key": "castle_black_k",
      "type": "bool"
    },
    {
      "entity": "chess_game",
      "key": "castle_black_q",
      "type": "bool"
    },
    {
      "entity": "pawn",
      "key": "moved",
      "type": "bool",
      "default": false
    },
    {
      "entity": "rook",
      "key": "moved",
      "type": "bool",
      "default": false
    },
    {
      "entity": "king",
      "key": "moved",
      "type": "bool",
      "default": false
    },
    {
      "entity": "checkmate",
      "key": "progress",
      "type": "int",
      "default": 0
    },
    {
      "entity": "checkmate",
      "key": "completed",
      "type": "bool",
      "default": false
    },
    {
      "entity": "stalemate",
      "key": "progress",
      "type": "int",
      "default": 0
    },
    {
      "entity": "stalemate",
      "key": "completed",
      "type": "bool",
      "default": false
    },
    {
      "entity": "dead_position",
      "key": "progress",
      "type": "int",
      "default": 0
    },
    {
      "entity": "dead_position",
      "key": "completed",
      "type": "bool",
      "default": false
    },
    {
      "entity": "repetition_draw",
      "key": "progress",
      "type": "int",
      "default": 0
    },
    {
      "entity": "repetition_draw",
      "key": "completed",
      "type": "bool",
      "default": false
    },
    {
      "entity": "move_count_draw",
      "key": "progress",
      "type": "int",
      "default": 0
    },
    {
      "entity": "move_count_draw",
      "key": "completed",
      "type": "bool",
      "default": false
    },
    {
      "entity": "timeout",
      "key": "progress",
      "type": "int",
      "default": 0
    },
    {
      "entity": "timeout",
      "key": "completed",
      "type": "bool",
      "default": false
    },
    {
      "entity": "capture_quest",
      "key": "progress",
      "type": "int",
      "default": 0
    },
    {
      "entity": "capture_quest",
      "key": "completed",
      "type": "bool",
      "default": false
    },
    {
      "entity": "promotion_quest",
      "key": "progress",
      "type": "int",
      "default": 0
    },
    {
      "entity": "promotion_quest",
      "key": "completed",
      "type": "bool",
      "default": false
    },
    {
      "entity": "castling_quest",
      "key": "progress",
      "type": "int",
      "default": 0
    },
    {
      "entity": "castling_quest",
      "key": "completed",
      "type": "bool",
      "default": false
    },
    {
      "entity": "square",
      "key": "light",
      "type": "bool",
      "default": false
    },
    {
      "entity": "queen",
      "key": "moved",
      "type": "bool",
      "default": false
    },
    {
      "entity": "bishop",
      "key": "moved",
      "type": "bool",
      "default": false
    },
    {
      "entity": "knight",
      "key": "moved",
      "type": "bool",
      "default": false
    },
    {
      "entity": "capture_quest",
      "key": "target",
      "type": "int",
      "default": 1
    },
    {
      "entity": "promotion_quest",
      "key": "target",
      "type": "int",
      "default": 1
    },
    {
      "entity": "castling_quest",
      "key": "target",
      "type": "int",
      "default": 1
    }
  ],
  "actions": [
    {
      "key": "move",
      "entity": "rook",
      "trigger": "command",
      "phase": "turn",
      "condition": {
        "op": "and",
        "args": {
          "values": [
            {
              "op": "eq",
              "args": {
                "a": {
                  "op": "owner",
                  "args": {
                    "entity": {
                      "op": "context",
                      "ref": "self"
                    }
                  }
                },
                "b": {
                  "op": "context",
                  "ref": "actor"
                }
              }
            },
            {
              "op": "phase_is",
              "args": {
                "phase": {
                  "op": "literal",
                  "value": "turn"
                }
              }
            },
            {
              "op": "is_active",
              "args": {
                "participant": {
                  "op": "context",
                  "ref": "actor"
                }
              }
            },
            {
              "op": "contains",
              "args": {
                "items": {
                  "op": "reachable_grid_nodes",
                  "args": {
                    "entity": {
                      "op": "context",
                      "ref": "self"
                    },
                    "directions": {
                      "op": "list",
                      "args": {
                        "values": [
                          {
                            "op": "vector",
                            "args": {
                              "row": {
                                "op": "literal",
                                "value": 1
                              },
                              "column": {
                                "op": "literal",
                                "value": 0
                              }
                            }
                          },
                          {
                            "op": "vector",
                            "args": {
                              "row": {
                                "op": "literal",
                                "value": -1
                              },
                              "column": {
                                "op": "literal",
                                "value": 0
                              }
                            }
                          },
                          {
                            "op": "vector",
                            "args": {
                              "row": {
                                "op": "literal",
                                "value": 0
                              },
                              "column": {
                                "op": "literal",
                                "value": 1
                              }
                            }
                          },
                          {
                            "op": "vector",
                            "args": {
                              "row": {
                                "op": "literal",
                                "value": 0
                              },
                              "column": {
                                "op": "literal",
                                "value": -1
                              }
                            }
                          }
                        ]
                      }
                    },
                    "max_steps": {
                      "op": "literal",
                      "value": 7
                    },
                    "leap": {
                      "op": "literal",
                      "value": false
                    },
                    "orientation": {
                      "op": "literal",
                      "value": 1
                    },
                    "target_occupancy": {
                      "op": "literal",
                      "value": "empty_or_opponent"
                    },
                    "state": {
                      "op": "context",
                      "ref": "observed_state"
                    }
                  }
                },
                "value": {
                  "op": "context",
                  "ref": "argument.to"
                }
              }
            },
            {
              "op": "none_match",
              "args": {
                "items": {
                  "op": "entities_at",
                  "args": {
                    "node": {
                      "op": "context",
                      "ref": "argument.to"
                    }
                  }
                },
                "variable": {
                  "op": "literal",
                  "value": "other"
                },
                "predicate": {
                  "op": "eq",
                  "args": {
                    "a": {
                      "op": "owner",
                      "args": {
                        "entity": {
                          "op": "context",
                          "ref": "local.other"
                        }
                      }
                    },
                    "b": {
                      "op": "owner",
                      "args": {
                        "entity": {
                          "op": "context",
                          "ref": "self"
                        }
                      }
                    }
                  }
                }
              }
            },
            {
              "op": "none_match",
              "args": {
                "items": {
                  "op": "entities_matching",
                  "args": {
                    "entity_type": {
                      "op": "literal",
                      "value": "king"
                    },
                    "owner": {
                      "op": "context",
                      "ref": "actor"
                    },
                    "state": {
                      "op": "preview",
                      "args": {
                        "state": {
                          "op": "context",
                          "ref": "observed_state"
                        },
                        "effects": {
                          "op": "list",
                          "args": {
                            "values": [
                              {
                                "op": "effect_value",
                                "args": {
                                  "name": {
                                    "op": "literal",
                                    "value": "move_entity"
                                  },
                                  "entity": {
                                    "op": "context",
                                    "ref": "self"
                                  },
                                  "destination": {
                                    "op": "context",
                                    "ref": "argument.to"
                                  }
                                }
                              }
                            ]
                          }
                        }
                      }
                    }
                  }
                },
                "variable": {
                  "op": "literal",
                  "value": "protected"
                },
                "predicate": {
                  "op": "threatened",
                  "args": {
                    "entity": {
                      "op": "context",
                      "ref": "local.protected"
                    },
                    "state": {
                      "op": "preview",
                      "args": {
                        "state": {
                          "op": "context",
                          "ref": "observed_state"
                        },
                        "effects": {
                          "op": "list",
                          "args": {
                            "values": [
                              {
                                "op": "effect_value",
                                "args": {
                                  "name": {
                                    "op": "literal",
                                    "value": "move_entity"
                                  },
                                  "entity": {
                                    "op": "context",
                                    "ref": "self"
                                  },
                                  "destination": {
                                    "op": "context",
                                    "ref": "argument.to"
                                  }
                                }
                              }
                            ]
                          }
                        }
                      }
                    }
                  }
                }
              }
            },
            {
              "op": "none_match",
              "args": {
                "items": {
                  "op": "entities_at",
                  "args": {
                    "node": {
                      "op": "context",
                      "ref": "argument.to"
                    }
                  }
                },
                "variable": {
                  "op": "literal",
                  "value": "occupant"
                },
                "predicate": {
                  "op": "contains",
                  "args": {
                    "items": {
                      "op": "entities_of_type",
                      "args": {
                        "entity_type": {
                          "op": "literal",
                          "value": "king"
                        }
                      }
                    },
                    "value": {
                      "op": "context",
                      "ref": "local.occupant"
                    }
                  }
                }
              }
            }
          ]
        }
      },
      "effects": [
        {
          "op": "remove_matching_entities",
          "args": {
            "node": {
              "op": "context",
              "ref": "argument.to"
            },
            "exclude_owner": {
              "op": "context",
              "ref": "actor"
            }
          }
        },
        {
          "op": "move_entity",
          "args": {
            "entity": {
              "op": "context",
              "ref": "self"
            },
            "destination": {
              "op": "context",
              "ref": "argument.to"
            }
          }
        },
        {
          "op": "emit_event",
          "args": {
            "name": {
              "op": "literal",
              "value": "piece.moved"
            }
          }
        },
        {
          "op": "set_field",
          "args": {
            "entity": {
              "op": "context",
              "ref": "self"
            },
            "field": {
              "op": "literal",
              "value": "moved"
            },
            "value": {
              "op": "literal",
              "value": true
            }
          }
        },
        {
          "op": "advance_turn",
          "args": {}
        }
      ],
      "priority": 0,
      "parameters": [
        {
          "key": "to",
          "type": "entity"
        }
      ]
    },
    {
      "key": "generate",
      "entity": "rook",
      "trigger": "hook",
      "phase": "turn",
      "condition": {
        "op": "eq",
        "args": {
          "a": {
            "op": "owner",
            "args": {
              "entity": {
                "op": "context",
                "ref": "self"
              }
            }
          },
          "b": {
            "op": "context",
            "ref": "actor"
          }
        }
      },
      "effects": [
        {
          "op": "emit_candidate",
          "args": {
            "source": {
              "op": "context",
              "ref": "self"
            },
            "destination": {
              "op": "context",
              "ref": "candidate"
            }
          }
        }
      ],
      "priority": 0,
      "hook": "action.generate",
      "iterator": {
        "op": "reachable_grid_nodes",
        "args": {
          "entity": {
            "op": "context",
            "ref": "self"
          },
          "directions": {
            "op": "list",
            "args": {
              "values": [
                {
                  "op": "vector",
                  "args": {
                    "row": {
                      "op": "literal",
                      "value": 1
                    },
                    "column": {
                      "op": "literal",
                      "value": 0
                    }
                  }
                },
                {
                  "op": "vector",
                  "args": {
                    "row": {
                      "op": "literal",
                      "value": -1
                    },
                    "column": {
                      "op": "literal",
                      "value": 0
                    }
                  }
                },
                {
                  "op": "vector",
                  "args": {
                    "row": {
                      "op": "literal",
                      "value": 0
                    },
                    "column": {
                      "op": "literal",
                      "value": 1
                    }
                  }
                },
                {
                  "op": "vector",
                  "args": {
                    "row": {
                      "op": "literal",
                      "value": 0
                    },
                    "column": {
                      "op": "literal",
                      "value": -1
                    }
                  }
                }
              ]
            }
          },
          "max_steps": {
            "op": "literal",
            "value": 7
          },
          "leap": {
            "op": "literal",
            "value": false
          },
          "orientation": {
            "op": "literal",
            "value": 1
          },
          "target_occupancy": {
            "op": "literal",
            "value": "empty_or_opponent"
          },
          "state": {
            "op": "context",
            "ref": "observed_state"
          }
        }
      },
      "variable": "candidate"
    },
    {
      "key": "move",
      "entity": "bishop",
      "trigger": "command",
      "phase": "turn",
      "condition": {
        "op": "and",
        "args": {
          "values": [
            {
              "op": "eq",
              "args": {
                "a": {
                  "op": "owner",
                  "args": {
                    "entity": {
                      "op": "context",
                      "ref": "self"
                    }
                  }
                },
                "b": {
                  "op": "context",
                  "ref": "actor"
                }
              }
            },
            {
              "op": "phase_is",
              "args": {
                "phase": {
                  "op": "literal",
                  "value": "turn"
                }
              }
            },
            {
              "op": "is_active",
              "args": {
                "participant": {
                  "op": "context",
                  "ref": "actor"
                }
              }
            },
            {
              "op": "contains",
              "args": {
                "items": {
                  "op": "reachable_grid_nodes",
                  "args": {
                    "entity": {
                      "op": "context",
                      "ref": "self"
                    },
                    "directions": {
                      "op": "list",
                      "args": {
                        "values": [
                          {
                            "op": "vector",
                            "args": {
                              "row": {
                                "op": "literal",
                                "value": 1
                              },
                              "column": {
                                "op": "literal",
                                "value": 1
                              }
                            }
                          },
                          {
                            "op": "vector",
                            "args": {
                              "row": {
                                "op": "literal",
                                "value": 1
                              },
                              "column": {
                                "op": "literal",
                                "value": -1
                              }
                            }
                          },
                          {
                            "op": "vector",
                            "args": {
                              "row": {
                                "op": "literal",
                                "value": -1
                              },
                              "column": {
                                "op": "literal",
                                "value": 1
                              }
                            }
                          },
                          {
                            "op": "vector",
                            "args": {
                              "row": {
                                "op": "literal",
                                "value": -1
                              },
                              "column": {
                                "op": "literal",
                                "value": -1
                              }
                            }
                          }
                        ]
                      }
                    },
                    "max_steps": {
                      "op": "literal",
                      "value": 7
                    },
                    "leap": {
                      "op": "literal",
                      "value": false
                    },
                    "orientation": {
                      "op": "literal",
                      "value": 1
                    },
                    "target_occupancy": {
                      "op": "literal",
                      "value": "empty_or_opponent"
                    },
                    "state": {
                      "op": "context",
                      "ref": "observed_state"
                    }
                  }
                },
                "value": {
                  "op": "context",
                  "ref": "argument.to"
                }
              }
            },
            {
              "op": "none_match",
              "args": {
                "items": {
                  "op": "entities_at",
                  "args": {
                    "node": {
                      "op": "context",
                      "ref": "argument.to"
                    }
                  }
                },
                "variable": {
                  "op": "literal",
                  "value": "other"
                },
                "predicate": {
                  "op": "eq",
                  "args": {
                    "a": {
                      "op": "owner",
                      "args": {
                        "entity": {
                          "op": "context",
                          "ref": "local.other"
                        }
                      }
                    },
                    "b": {
                      "op": "owner",
                      "args": {
                        "entity": {
                          "op": "context",
                          "ref": "self"
                        }
                      }
                    }
                  }
                }
              }
            },
            {
              "op": "none_match",
              "args": {
                "items": {
                  "op": "entities_matching",
                  "args": {
                    "entity_type": {
                      "op": "literal",
                      "value": "king"
                    },
                    "owner": {
                      "op": "context",
                      "ref": "actor"
                    },
                    "state": {
                      "op": "preview",
                      "args": {
                        "state": {
                          "op": "context",
                          "ref": "observed_state"
                        },
                        "effects": {
                          "op": "list",
                          "args": {
                            "values": [
                              {
                                "op": "effect_value",
                                "args": {
                                  "name": {
                                    "op": "literal",
                                    "value": "move_entity"
                                  },
                                  "entity": {
                                    "op": "context",
                                    "ref": "self"
                                  },
                                  "destination": {
                                    "op": "context",
                                    "ref": "argument.to"
                                  }
                                }
                              }
                            ]
                          }
                        }
                      }
                    }
                  }
                },
                "variable": {
                  "op": "literal",
                  "value": "protected"
                },
                "predicate": {
                  "op": "threatened",
                  "args": {
                    "entity": {
                      "op": "context",
                      "ref": "local.protected"
                    },
                    "state": {
                      "op": "preview",
                      "args": {
                        "state": {
                          "op": "context",
                          "ref": "observed_state"
                        },
                        "effects": {
                          "op": "list",
                          "args": {
                            "values": [
                              {
                                "op": "effect_value",
                                "args": {
                                  "name": {
                                    "op": "literal",
                                    "value": "move_entity"
                                  },
                                  "entity": {
                                    "op": "context",
                                    "ref": "self"
                                  },
                                  "destination": {
                                    "op": "context",
                                    "ref": "argument.to"
                                  }
                                }
                              }
                            ]
                          }
                        }
                      }
                    }
                  }
                }
              }
            },
            {
              "op": "none_match",
              "args": {
                "items": {
                  "op": "entities_at",
                  "args": {
                    "node": {
                      "op": "context",
                      "ref": "argument.to"
                    }
                  }
                },
                "variable": {
                  "op": "literal",
                  "value": "occupant"
                },
                "predicate": {
                  "op": "contains",
                  "args": {
                    "items": {
                      "op": "entities_of_type",
                      "args": {
                        "entity_type": {
                          "op": "literal",
                          "value": "king"
                        }
                      }
                    },
                    "value": {
                      "op": "context",
                      "ref": "local.occupant"
                    }
                  }
                }
              }
            }
          ]
        }
      },
      "effects": [
        {
          "op": "remove_matching_entities",
          "args": {
            "node": {
              "op": "context",
              "ref": "argument.to"
            },
            "exclude_owner": {
              "op": "context",
              "ref": "actor"
            }
          }
        },
        {
          "op": "move_entity",
          "args": {
            "entity": {
              "op": "context",
              "ref": "self"
            },
            "destination": {
              "op": "context",
              "ref": "argument.to"
            }
          }
        },
        {
          "op": "emit_event",
          "args": {
            "name": {
              "op": "literal",
              "value": "piece.moved"
            }
          }
        },
        {
          "op": "advance_turn",
          "args": {}
        }
      ],
      "priority": 0,
      "parameters": [
        {
          "key": "to",
          "type": "entity"
        }
      ]
    },
    {
      "key": "generate",
      "entity": "bishop",
      "trigger": "hook",
      "phase": "turn",
      "condition": {
        "op": "eq",
        "args": {
          "a": {
            "op": "owner",
            "args": {
              "entity": {
                "op": "context",
                "ref": "self"
              }
            }
          },
          "b": {
            "op": "context",
            "ref": "actor"
          }
        }
      },
      "effects": [
        {
          "op": "emit_candidate",
          "args": {
            "source": {
              "op": "context",
              "ref": "self"
            },
            "destination": {
              "op": "context",
              "ref": "candidate"
            }
          }
        }
      ],
      "priority": 0,
      "hook": "action.generate",
      "iterator": {
        "op": "reachable_grid_nodes",
        "args": {
          "entity": {
            "op": "context",
            "ref": "self"
          },
          "directions": {
            "op": "list",
            "args": {
              "values": [
                {
                  "op": "vector",
                  "args": {
                    "row": {
                      "op": "literal",
                      "value": 1
                    },
                    "column": {
                      "op": "literal",
                      "value": 1
                    }
                  }
                },
                {
                  "op": "vector",
                  "args": {
                    "row": {
                      "op": "literal",
                      "value": 1
                    },
                    "column": {
                      "op": "literal",
                      "value": -1
                    }
                  }
                },
                {
                  "op": "vector",
                  "args": {
                    "row": {
                      "op": "literal",
                      "value": -1
                    },
                    "column": {
                      "op": "literal",
                      "value": 1
                    }
                  }
                },
                {
                  "op": "vector",
                  "args": {
                    "row": {
                      "op": "literal",
                      "value": -1
                    },
                    "column": {
                      "op": "literal",
                      "value": -1
                    }
                  }
                }
              ]
            }
          },
          "max_steps": {
            "op": "literal",
            "value": 7
          },
          "leap": {
            "op": "literal",
            "value": false
          },
          "orientation": {
            "op": "literal",
            "value": 1
          },
          "target_occupancy": {
            "op": "literal",
            "value": "empty_or_opponent"
          },
          "state": {
            "op": "context",
            "ref": "observed_state"
          }
        }
      },
      "variable": "candidate"
    },
    {
      "key": "move",
      "entity": "queen",
      "trigger": "command",
      "phase": "turn",
      "condition": {
        "op": "and",
        "args": {
          "values": [
            {
              "op": "eq",
              "args": {
                "a": {
                  "op": "owner",
                  "args": {
                    "entity": {
                      "op": "context",
                      "ref": "self"
                    }
                  }
                },
                "b": {
                  "op": "context",
                  "ref": "actor"
                }
              }
            },
            {
              "op": "phase_is",
              "args": {
                "phase": {
                  "op": "literal",
                  "value": "turn"
                }
              }
            },
            {
              "op": "is_active",
              "args": {
                "participant": {
                  "op": "context",
                  "ref": "actor"
                }
              }
            },
            {
              "op": "contains",
              "args": {
                "items": {
                  "op": "reachable_grid_nodes",
                  "args": {
                    "entity": {
                      "op": "context",
                      "ref": "self"
                    },
                    "directions": {
                      "op": "list",
                      "args": {
                        "values": [
                          {
                            "op": "vector",
                            "args": {
                              "row": {
                                "op": "literal",
                                "value": 1
                              },
                              "column": {
                                "op": "literal",
                                "value": 0
                              }
                            }
                          },
                          {
                            "op": "vector",
                            "args": {
                              "row": {
                                "op": "literal",
                                "value": -1
                              },
                              "column": {
                                "op": "literal",
                                "value": 0
                              }
                            }
                          },
                          {
                            "op": "vector",
                            "args": {
                              "row": {
                                "op": "literal",
                                "value": 0
                              },
                              "column": {
                                "op": "literal",
                                "value": 1
                              }
                            }
                          },
                          {
                            "op": "vector",
                            "args": {
                              "row": {
                                "op": "literal",
                                "value": 0
                              },
                              "column": {
                                "op": "literal",
                                "value": -1
                              }
                            }
                          },
                          {
                            "op": "vector",
                            "args": {
                              "row": {
                                "op": "literal",
                                "value": 1
                              },
                              "column": {
                                "op": "literal",
                                "value": 1
                              }
                            }
                          },
                          {
                            "op": "vector",
                            "args": {
                              "row": {
                                "op": "literal",
                                "value": 1
                              },
                              "column": {
                                "op": "literal",
                                "value": -1
                              }
                            }
                          },
                          {
                            "op": "vector",
                            "args": {
                              "row": {
                                "op": "literal",
                                "value": -1
                              },
                              "column": {
                                "op": "literal",
                                "value": 1
                              }
                            }
                          },
                          {
                            "op": "vector",
                            "args": {
                              "row": {
                                "op": "literal",
                                "value": -1
                              },
                              "column": {
                                "op": "literal",
                                "value": -1
                              }
                            }
                          }
                        ]
                      }
                    },
                    "max_steps": {
                      "op": "literal",
                      "value": 7
                    },
                    "leap": {
                      "op": "literal",
                      "value": false
                    },
                    "orientation": {
                      "op": "literal",
                      "value": 1
                    },
                    "target_occupancy": {
                      "op": "literal",
                      "value": "empty_or_opponent"
                    },
                    "state": {
                      "op": "context",
                      "ref": "observed_state"
                    }
                  }
                },
                "value": {
                  "op": "context",
                  "ref": "argument.to"
                }
              }
            },
            {
              "op": "none_match",
              "args": {
                "items": {
                  "op": "entities_at",
                  "args": {
                    "node": {
                      "op": "context",
                      "ref": "argument.to"
                    }
                  }
                },
                "variable": {
                  "op": "literal",
                  "value": "other"
                },
                "predicate": {
                  "op": "eq",
                  "args": {
                    "a": {
                      "op": "owner",
                      "args": {
                        "entity": {
                          "op": "context",
                          "ref": "local.other"
                        }
                      }
                    },
                    "b": {
                      "op": "owner",
                      "args": {
                        "entity": {
                          "op": "context",
                          "ref": "self"
                        }
                      }
                    }
                  }
                }
              }
            },
            {
              "op": "none_match",
              "args": {
                "items": {
                  "op": "entities_matching",
                  "args": {
                    "entity_type": {
                      "op": "literal",
                      "value": "king"
                    },
                    "owner": {
                      "op": "context",
                      "ref": "actor"
                    },
                    "state": {
                      "op": "preview",
                      "args": {
                        "state": {
                          "op": "context",
                          "ref": "observed_state"
                        },
                        "effects": {
                          "op": "list",
                          "args": {
                            "values": [
                              {
                                "op": "effect_value",
                                "args": {
                                  "name": {
                                    "op": "literal",
                                    "value": "move_entity"
                                  },
                                  "entity": {
                                    "op": "context",
                                    "ref": "self"
                                  },
                                  "destination": {
                                    "op": "context",
                                    "ref": "argument.to"
                                  }
                                }
                              }
                            ]
                          }
                        }
                      }
                    }
                  }
                },
                "variable": {
                  "op": "literal",
                  "value": "protected"
                },
                "predicate": {
                  "op": "threatened",
                  "args": {
                    "entity": {
                      "op": "context",
                      "ref": "local.protected"
                    },
                    "state": {
                      "op": "preview",
                      "args": {
                        "state": {
                          "op": "context",
                          "ref": "observed_state"
                        },
                        "effects": {
                          "op": "list",
                          "args": {
                            "values": [
                              {
                                "op": "effect_value",
                                "args": {
                                  "name": {
                                    "op": "literal",
                                    "value": "move_entity"
                                  },
                                  "entity": {
                                    "op": "context",
                                    "ref": "self"
                                  },
                                  "destination": {
                                    "op": "context",
                                    "ref": "argument.to"
                                  }
                                }
                              }
                            ]
                          }
                        }
                      }
                    }
                  }
                }
              }
            },
            {
              "op": "none_match",
              "args": {
                "items": {
                  "op": "entities_at",
                  "args": {
                    "node": {
                      "op": "context",
                      "ref": "argument.to"
                    }
                  }
                },
                "variable": {
                  "op": "literal",
                  "value": "occupant"
                },
                "predicate": {
                  "op": "contains",
                  "args": {
                    "items": {
                      "op": "entities_of_type",
                      "args": {
                        "entity_type": {
                          "op": "literal",
                          "value": "king"
                        }
                      }
                    },
                    "value": {
                      "op": "context",
                      "ref": "local.occupant"
                    }
                  }
                }
              }
            }
          ]
        }
      },
      "effects": [
        {
          "op": "remove_matching_entities",
          "args": {
            "node": {
              "op": "context",
              "ref": "argument.to"
            },
            "exclude_owner": {
              "op": "context",
              "ref": "actor"
            }
          }
        },
        {
          "op": "move_entity",
          "args": {
            "entity": {
              "op": "context",
              "ref": "self"
            },
            "destination": {
              "op": "context",
              "ref": "argument.to"
            }
          }
        },
        {
          "op": "emit_event",
          "args": {
            "name": {
              "op": "literal",
              "value": "piece.moved"
            }
          }
        },
        {
          "op": "advance_turn",
          "args": {}
        }
      ],
      "priority": 0,
      "parameters": [
        {
          "key": "to",
          "type": "entity"
        }
      ]
    },
    {
      "key": "generate",
      "entity": "queen",
      "trigger": "hook",
      "phase": "turn",
      "condition": {
        "op": "eq",
        "args": {
          "a": {
            "op": "owner",
            "args": {
              "entity": {
                "op": "context",
                "ref": "self"
              }
            }
          },
          "b": {
            "op": "context",
            "ref": "actor"
          }
        }
      },
      "effects": [
        {
          "op": "emit_candidate",
          "args": {
            "source": {
              "op": "context",
              "ref": "self"
            },
            "destination": {
              "op": "context",
              "ref": "candidate"
            }
          }
        }
      ],
      "priority": 0,
      "hook": "action.generate",
      "iterator": {
        "op": "reachable_grid_nodes",
        "args": {
          "entity": {
            "op": "context",
            "ref": "self"
          },
          "directions": {
            "op": "list",
            "args": {
              "values": [
                {
                  "op": "vector",
                  "args": {
                    "row": {
                      "op": "literal",
                      "value": 1
                    },
                    "column": {
                      "op": "literal",
                      "value": 0
                    }
                  }
                },
                {
                  "op": "vector",
                  "args": {
                    "row": {
                      "op": "literal",
                      "value": -1
                    },
                    "column": {
                      "op": "literal",
                      "value": 0
                    }
                  }
                },
                {
                  "op": "vector",
                  "args": {
                    "row": {
                      "op": "literal",
                      "value": 0
                    },
                    "column": {
                      "op": "literal",
                      "value": 1
                    }
                  }
                },
                {
                  "op": "vector",
                  "args": {
                    "row": {
                      "op": "literal",
                      "value": 0
                    },
                    "column": {
                      "op": "literal",
                      "value": -1
                    }
                  }
                },
                {
                  "op": "vector",
                  "args": {
                    "row": {
                      "op": "literal",
                      "value": 1
                    },
                    "column": {
                      "op": "literal",
                      "value": 1
                    }
                  }
                },
                {
                  "op": "vector",
                  "args": {
                    "row": {
                      "op": "literal",
                      "value": 1
                    },
                    "column": {
                      "op": "literal",
                      "value": -1
                    }
                  }
                },
                {
                  "op": "vector",
                  "args": {
                    "row": {
                      "op": "literal",
                      "value": -1
                    },
                    "column": {
                      "op": "literal",
                      "value": 1
                    }
                  }
                },
                {
                  "op": "vector",
                  "args": {
                    "row": {
                      "op": "literal",
                      "value": -1
                    },
                    "column": {
                      "op": "literal",
                      "value": -1
                    }
                  }
                }
              ]
            }
          },
          "max_steps": {
            "op": "literal",
            "value": 7
          },
          "leap": {
            "op": "literal",
            "value": false
          },
          "orientation": {
            "op": "literal",
            "value": 1
          },
          "target_occupancy": {
            "op": "literal",
            "value": "empty_or_opponent"
          },
          "state": {
            "op": "context",
            "ref": "observed_state"
          }
        }
      },
      "variable": "candidate"
    },
    {
      "key": "move",
      "entity": "king",
      "trigger": "command",
      "phase": "turn",
      "condition": {
        "op": "and",
        "args": {
          "values": [
            {
              "op": "eq",
              "args": {
                "a": {
                  "op": "owner",
                  "args": {
                    "entity": {
                      "op": "context",
                      "ref": "self"
                    }
                  }
                },
                "b": {
                  "op": "context",
                  "ref": "actor"
                }
              }
            },
            {
              "op": "phase_is",
              "args": {
                "phase": {
                  "op": "literal",
                  "value": "turn"
                }
              }
            },
            {
              "op": "is_active",
              "args": {
                "participant": {
                  "op": "context",
                  "ref": "actor"
                }
              }
            },
            {
              "op": "contains",
              "args": {
                "items": {
                  "op": "reachable_grid_nodes",
                  "args": {
                    "entity": {
                      "op": "context",
                      "ref": "self"
                    },
                    "directions": {
                      "op": "list",
                      "args": {
                        "values": [
                          {
                            "op": "vector",
                            "args": {
                              "row": {
                                "op": "literal",
                                "value": 1
                              },
                              "column": {
                                "op": "literal",
                                "value": 0
                              }
                            }
                          },
                          {
                            "op": "vector",
                            "args": {
                              "row": {
                                "op": "literal",
                                "value": -1
                              },
                              "column": {
                                "op": "literal",
                                "value": 0
                              }
                            }
                          },
                          {
                            "op": "vector",
                            "args": {
                              "row": {
                                "op": "literal",
                                "value": 0
                              },
                              "column": {
                                "op": "literal",
                                "value": 1
                              }
                            }
                          },
                          {
                            "op": "vector",
                            "args": {
                              "row": {
                                "op": "literal",
                                "value": 0
                              },
                              "column": {
                                "op": "literal",
                                "value": -1
                              }
                            }
                          },
                          {
                            "op": "vector",
                            "args": {
                              "row": {
                                "op": "literal",
                                "value": 1
                              },
                              "column": {
                                "op": "literal",
                                "value": 1
                              }
                            }
                          },
                          {
                            "op": "vector",
                            "args": {
                              "row": {
                                "op": "literal",
                                "value": 1
                              },
                              "column": {
                                "op": "literal",
                                "value": -1
                              }
                            }
                          },
                          {
                            "op": "vector",
                            "args": {
                              "row": {
                                "op": "literal",
                                "value": -1
                              },
                              "column": {
                                "op": "literal",
                                "value": 1
                              }
                            }
                          },
                          {
                            "op": "vector",
                            "args": {
                              "row": {
                                "op": "literal",
                                "value": -1
                              },
                              "column": {
                                "op": "literal",
                                "value": -1
                              }
                            }
                          }
                        ]
                      }
                    },
                    "max_steps": {
                      "op": "literal",
                      "value": 1
                    },
                    "leap": {
                      "op": "literal",
                      "value": false
                    },
                    "orientation": {
                      "op": "literal",
                      "value": 1
                    },
                    "target_occupancy": {
                      "op": "literal",
                      "value": "empty_or_opponent"
                    },
                    "state": {
                      "op": "context",
                      "ref": "observed_state"
                    }
                  }
                },
                "value": {
                  "op": "context",
                  "ref": "argument.to"
                }
              }
            },
            {
              "op": "none_match",
              "args": {
                "items": {
                  "op": "entities_at",
                  "args": {
                    "node": {
                      "op": "context",
                      "ref": "argument.to"
                    }
                  }
                },
                "variable": {
                  "op": "literal",
                  "value": "other"
                },
                "predicate": {
                  "op": "eq",
                  "args": {
                    "a": {
                      "op": "owner",
                      "args": {
                        "entity": {
                          "op": "context",
                          "ref": "local.other"
                        }
                      }
                    },
                    "b": {
                      "op": "owner",
                      "args": {
                        "entity": {
                          "op": "context",
                          "ref": "self"
                        }
                      }
                    }
                  }
                }
              }
            },
            {
              "op": "none_match",
              "args": {
                "items": {
                  "op": "entities_matching",
                  "args": {
                    "entity_type": {
                      "op": "literal",
                      "value": "king"
                    },
                    "owner": {
                      "op": "context",
                      "ref": "actor"
                    },
                    "state": {
                      "op": "preview",
                      "args": {
                        "state": {
                          "op": "context",
                          "ref": "observed_state"
                        },
                        "effects": {
                          "op": "list",
                          "args": {
                            "values": [
                              {
                                "op": "effect_value",
                                "args": {
                                  "name": {
                                    "op": "literal",
                                    "value": "move_entity"
                                  },
                                  "entity": {
                                    "op": "context",
                                    "ref": "self"
                                  },
                                  "destination": {
                                    "op": "context",
                                    "ref": "argument.to"
                                  }
                                }
                              }
                            ]
                          }
                        }
                      }
                    }
                  }
                },
                "variable": {
                  "op": "literal",
                  "value": "protected"
                },
                "predicate": {
                  "op": "threatened",
                  "args": {
                    "entity": {
                      "op": "context",
                      "ref": "local.protected"
                    },
                    "state": {
                      "op": "preview",
                      "args": {
                        "state": {
                          "op": "context",
                          "ref": "observed_state"
                        },
                        "effects": {
                          "op": "list",
                          "args": {
                            "values": [
                              {
                                "op": "effect_value",
                                "args": {
                                  "name": {
                                    "op": "literal",
                                    "value": "move_entity"
                                  },
                                  "entity": {
                                    "op": "context",
                                    "ref": "self"
                                  },
                                  "destination": {
                                    "op": "context",
                                    "ref": "argument.to"
                                  }
                                }
                              }
                            ]
                          }
                        }
                      }
                    }
                  }
                }
              }
            },
            {
              "op": "none_match",
              "args": {
                "items": {
                  "op": "entities_at",
                  "args": {
                    "node": {
                      "op": "context",
                      "ref": "argument.to"
                    }
                  }
                },
                "variable": {
                  "op": "literal",
                  "value": "occupant"
                },
                "predicate": {
                  "op": "contains",
                  "args": {
                    "items": {
                      "op": "entities_of_type",
                      "args": {
                        "entity_type": {
                          "op": "literal",
                          "value": "king"
                        }
                      }
                    },
                    "value": {
                      "op": "context",
                      "ref": "local.occupant"
                    }
                  }
                }
              }
            }
          ]
        }
      },
      "effects": [
        {
          "op": "remove_matching_entities",
          "args": {
            "node": {
              "op": "context",
              "ref": "argument.to"
            },
            "exclude_owner": {
              "op": "context",
              "ref": "actor"
            }
          }
        },
        {
          "op": "move_entity",
          "args": {
            "entity": {
              "op": "context",
              "ref": "self"
            },
            "destination": {
              "op": "context",
              "ref": "argument.to"
            }
          }
        },
        {
          "op": "emit_event",
          "args": {
            "name": {
              "op": "literal",
              "value": "piece.moved"
            }
          }
        },
        {
          "op": "set_field",
          "args": {
            "entity": {
              "op": "context",
              "ref": "self"
            },
            "field": {
              "op": "literal",
              "value": "moved"
            },
            "value": {
              "op": "literal",
              "value": true
            }
          }
        },
        {
          "op": "advance_turn",
          "args": {}
        }
      ],
      "priority": 0,
      "parameters": [
        {
          "key": "to",
          "type": "entity"
        }
      ]
    },
    {
      "key": "generate",
      "entity": "king",
      "trigger": "hook",
      "phase": "turn",
      "condition": {
        "op": "eq",
        "args": {
          "a": {
            "op": "owner",
            "args": {
              "entity": {
                "op": "context",
                "ref": "self"
              }
            }
          },
          "b": {
            "op": "context",
            "ref": "actor"
          }
        }
      },
      "effects": [
        {
          "op": "emit_candidate",
          "args": {
            "source": {
              "op": "context",
              "ref": "self"
            },
            "destination": {
              "op": "context",
              "ref": "candidate"
            }
          }
        }
      ],
      "priority": 0,
      "hook": "action.generate",
      "iterator": {
        "op": "reachable_grid_nodes",
        "args": {
          "entity": {
            "op": "context",
            "ref": "self"
          },
          "directions": {
            "op": "list",
            "args": {
              "values": [
                {
                  "op": "vector",
                  "args": {
                    "row": {
                      "op": "literal",
                      "value": 1
                    },
                    "column": {
                      "op": "literal",
                      "value": 0
                    }
                  }
                },
                {
                  "op": "vector",
                  "args": {
                    "row": {
                      "op": "literal",
                      "value": -1
                    },
                    "column": {
                      "op": "literal",
                      "value": 0
                    }
                  }
                },
                {
                  "op": "vector",
                  "args": {
                    "row": {
                      "op": "literal",
                      "value": 0
                    },
                    "column": {
                      "op": "literal",
                      "value": 1
                    }
                  }
                },
                {
                  "op": "vector",
                  "args": {
                    "row": {
                      "op": "literal",
                      "value": 0
                    },
                    "column": {
                      "op": "literal",
                      "value": -1
                    }
                  }
                },
                {
                  "op": "vector",
                  "args": {
                    "row": {
                      "op": "literal",
                      "value": 1
                    },
                    "column": {
                      "op": "literal",
                      "value": 1
                    }
                  }
                },
                {
                  "op": "vector",
                  "args": {
                    "row": {
                      "op": "literal",
                      "value": 1
                    },
                    "column": {
                      "op": "literal",
                      "value": -1
                    }
                  }
                },
                {
                  "op": "vector",
                  "args": {
                    "row": {
                      "op": "literal",
                      "value": -1
                    },
                    "column": {
                      "op": "literal",
                      "value": 1
                    }
                  }
                },
                {
                  "op": "vector",
                  "args": {
                    "row": {
                      "op": "literal",
                      "value": -1
                    },
                    "column": {
                      "op": "literal",
                      "value": -1
                    }
                  }
                }
              ]
            }
          },
          "max_steps": {
            "op": "literal",
            "value": 1
          },
          "leap": {
            "op": "literal",
            "value": false
          },
          "orientation": {
            "op": "literal",
            "value": 1
          },
          "target_occupancy": {
            "op": "literal",
            "value": "empty_or_opponent"
          },
          "state": {
            "op": "context",
            "ref": "observed_state"
          }
        }
      },
      "variable": "candidate"
    },
    {
      "key": "move",
      "entity": "knight",
      "trigger": "command",
      "phase": "turn",
      "condition": {
        "op": "and",
        "args": {
          "values": [
            {
              "op": "eq",
              "args": {
                "a": {
                  "op": "owner",
                  "args": {
                    "entity": {
                      "op": "context",
                      "ref": "self"
                    }
                  }
                },
                "b": {
                  "op": "context",
                  "ref": "actor"
                }
              }
            },
            {
              "op": "phase_is",
              "args": {
                "phase": {
                  "op": "literal",
                  "value": "turn"
                }
              }
            },
            {
              "op": "is_active",
              "args": {
                "participant": {
                  "op": "context",
                  "ref": "actor"
                }
              }
            },
            {
              "op": "contains",
              "args": {
                "items": {
                  "op": "reachable_grid_nodes",
                  "args": {
                    "entity": {
                      "op": "context",
                      "ref": "self"
                    },
                    "directions": {
                      "op": "list",
                      "args": {
                        "values": [
                          {
                            "op": "vector",
                            "args": {
                              "row": {
                                "op": "literal",
                                "value": 2
                              },
                              "column": {
                                "op": "literal",
                                "value": 1
                              }
                            }
                          },
                          {
                            "op": "vector",
                            "args": {
                              "row": {
                                "op": "literal",
                                "value": 2
                              },
                              "column": {
                                "op": "literal",
                                "value": -1
                              }
                            }
                          },
                          {
                            "op": "vector",
                            "args": {
                              "row": {
                                "op": "literal",
                                "value": -2
                              },
                              "column": {
                                "op": "literal",
                                "value": 1
                              }
                            }
                          },
                          {
                            "op": "vector",
                            "args": {
                              "row": {
                                "op": "literal",
                                "value": -2
                              },
                              "column": {
                                "op": "literal",
                                "value": -1
                              }
                            }
                          },
                          {
                            "op": "vector",
                            "args": {
                              "row": {
                                "op": "literal",
                                "value": 1
                              },
                              "column": {
                                "op": "literal",
                                "value": 2
                              }
                            }
                          },
                          {
                            "op": "vector",
                            "args": {
                              "row": {
                                "op": "literal",
                                "value": 1
                              },
                              "column": {
                                "op": "literal",
                                "value": -2
                              }
                            }
                          },
                          {
                            "op": "vector",
                            "args": {
                              "row": {
                                "op": "literal",
                                "value": -1
                              },
                              "column": {
                                "op": "literal",
                                "value": 2
                              }
                            }
                          },
                          {
                            "op": "vector",
                            "args": {
                              "row": {
                                "op": "literal",
                                "value": -1
                              },
                              "column": {
                                "op": "literal",
                                "value": -2
                              }
                            }
                          }
                        ]
                      }
                    },
                    "max_steps": {
                      "op": "literal",
                      "value": 1
                    },
                    "leap": {
                      "op": "literal",
                      "value": true
                    },
                    "orientation": {
                      "op": "literal",
                      "value": 1
                    },
                    "target_occupancy": {
                      "op": "literal",
                      "value": "empty_or_opponent"
                    },
                    "state": {
                      "op": "context",
                      "ref": "observed_state"
                    }
                  }
                },
                "value": {
                  "op": "context",
                  "ref": "argument.to"
                }
              }
            },
            {
              "op": "none_match",
              "args": {
                "items": {
                  "op": "entities_at",
                  "args": {
                    "node": {
                      "op": "context",
                      "ref": "argument.to"
                    }
                  }
                },
                "variable": {
                  "op": "literal",
                  "value": "other"
                },
                "predicate": {
                  "op": "eq",
                  "args": {
                    "a": {
                      "op": "owner",
                      "args": {
                        "entity": {
                          "op": "context",
                          "ref": "local.other"
                        }
                      }
                    },
                    "b": {
                      "op": "owner",
                      "args": {
                        "entity": {
                          "op": "context",
                          "ref": "self"
                        }
                      }
                    }
                  }
                }
              }
            },
            {
              "op": "none_match",
              "args": {
                "items": {
                  "op": "entities_matching",
                  "args": {
                    "entity_type": {
                      "op": "literal",
                      "value": "king"
                    },
                    "owner": {
                      "op": "context",
                      "ref": "actor"
                    },
                    "state": {
                      "op": "preview",
                      "args": {
                        "state": {
                          "op": "context",
                          "ref": "observed_state"
                        },
                        "effects": {
                          "op": "list",
                          "args": {
                            "values": [
                              {
                                "op": "effect_value",
                                "args": {
                                  "name": {
                                    "op": "literal",
                                    "value": "move_entity"
                                  },
                                  "entity": {
                                    "op": "context",
                                    "ref": "self"
                                  },
                                  "destination": {
                                    "op": "context",
                                    "ref": "argument.to"
                                  }
                                }
                              }
                            ]
                          }
                        }
                      }
                    }
                  }
                },
                "variable": {
                  "op": "literal",
                  "value": "protected"
                },
                "predicate": {
                  "op": "threatened",
                  "args": {
                    "entity": {
                      "op": "context",
                      "ref": "local.protected"
                    },
                    "state": {
                      "op": "preview",
                      "args": {
                        "state": {
                          "op": "context",
                          "ref": "observed_state"
                        },
                        "effects": {
                          "op": "list",
                          "args": {
                            "values": [
                              {
                                "op": "effect_value",
                                "args": {
                                  "name": {
                                    "op": "literal",
                                    "value": "move_entity"
                                  },
                                  "entity": {
                                    "op": "context",
                                    "ref": "self"
                                  },
                                  "destination": {
                                    "op": "context",
                                    "ref": "argument.to"
                                  }
                                }
                              }
                            ]
                          }
                        }
                      }
                    }
                  }
                }
              }
            },
            {
              "op": "none_match",
              "args": {
                "items": {
                  "op": "entities_at",
                  "args": {
                    "node": {
                      "op": "context",
                      "ref": "argument.to"
                    }
                  }
                },
                "variable": {
                  "op": "literal",
                  "value": "occupant"
                },
                "predicate": {
                  "op": "contains",
                  "args": {
                    "items": {
                      "op": "entities_of_type",
                      "args": {
                        "entity_type": {
                          "op": "literal",
                          "value": "king"
                        }
                      }
                    },
                    "value": {
                      "op": "context",
                      "ref": "local.occupant"
                    }
                  }
                }
              }
            }
          ]
        }
      },
      "effects": [
        {
          "op": "remove_matching_entities",
          "args": {
            "node": {
              "op": "context",
              "ref": "argument.to"
            },
            "exclude_owner": {
              "op": "context",
              "ref": "actor"
            }
          }
        },
        {
          "op": "move_entity",
          "args": {
            "entity": {
              "op": "context",
              "ref": "self"
            },
            "destination": {
              "op": "context",
              "ref": "argument.to"
            }
          }
        },
        {
          "op": "emit_event",
          "args": {
            "name": {
              "op": "literal",
              "value": "piece.moved"
            }
          }
        },
        {
          "op": "advance_turn",
          "args": {}
        }
      ],
      "priority": 0,
      "parameters": [
        {
          "key": "to",
          "type": "entity"
        }
      ]
    },
    {
      "key": "generate",
      "entity": "knight",
      "trigger": "hook",
      "phase": "turn",
      "condition": {
        "op": "eq",
        "args": {
          "a": {
            "op": "owner",
            "args": {
              "entity": {
                "op": "context",
                "ref": "self"
              }
            }
          },
          "b": {
            "op": "context",
            "ref": "actor"
          }
        }
      },
      "effects": [
        {
          "op": "emit_candidate",
          "args": {
            "source": {
              "op": "context",
              "ref": "self"
            },
            "destination": {
              "op": "context",
              "ref": "candidate"
            }
          }
        }
      ],
      "priority": 0,
      "hook": "action.generate",
      "iterator": {
        "op": "reachable_grid_nodes",
        "args": {
          "entity": {
            "op": "context",
            "ref": "self"
          },
          "directions": {
            "op": "list",
            "args": {
              "values": [
                {
                  "op": "vector",
                  "args": {
                    "row": {
                      "op": "literal",
                      "value": 2
                    },
                    "column": {
                      "op": "literal",
                      "value": 1
                    }
                  }
                },
                {
                  "op": "vector",
                  "args": {
                    "row": {
                      "op": "literal",
                      "value": 2
                    },
                    "column": {
                      "op": "literal",
                      "value": -1
                    }
                  }
                },
                {
                  "op": "vector",
                  "args": {
                    "row": {
                      "op": "literal",
                      "value": -2
                    },
                    "column": {
                      "op": "literal",
                      "value": 1
                    }
                  }
                },
                {
                  "op": "vector",
                  "args": {
                    "row": {
                      "op": "literal",
                      "value": -2
                    },
                    "column": {
                      "op": "literal",
                      "value": -1
                    }
                  }
                },
                {
                  "op": "vector",
                  "args": {
                    "row": {
                      "op": "literal",
                      "value": 1
                    },
                    "column": {
                      "op": "literal",
                      "value": 2
                    }
                  }
                },
                {
                  "op": "vector",
                  "args": {
                    "row": {
                      "op": "literal",
                      "value": 1
                    },
                    "column": {
                      "op": "literal",
                      "value": -2
                    }
                  }
                },
                {
                  "op": "vector",
                  "args": {
                    "row": {
                      "op": "literal",
                      "value": -1
                    },
                    "column": {
                      "op": "literal",
                      "value": 2
                    }
                  }
                },
                {
                  "op": "vector",
                  "args": {
                    "row": {
                      "op": "literal",
                      "value": -1
                    },
                    "column": {
                      "op": "literal",
                      "value": -2
                    }
                  }
                }
              ]
            }
          },
          "max_steps": {
            "op": "literal",
            "value": 1
          },
          "leap": {
            "op": "literal",
            "value": true
          },
          "orientation": {
            "op": "literal",
            "value": 1
          },
          "target_occupancy": {
            "op": "literal",
            "value": "empty_or_opponent"
          },
          "state": {
            "op": "context",
            "ref": "observed_state"
          }
        }
      },
      "variable": "candidate"
    },
    {
      "key": "move",
      "entity": "pawn",
      "trigger": "command",
      "phase": "turn",
      "condition": {
        "op": "and",
        "args": {
          "values": [
            {
              "op": "eq",
              "args": {
                "a": {
                  "op": "owner",
                  "args": {
                    "entity": {
                      "op": "context",
                      "ref": "self"
                    }
                  }
                },
                "b": {
                  "op": "context",
                  "ref": "actor"
                }
              }
            },
            {
              "op": "phase_is",
              "args": {
                "phase": {
                  "op": "literal",
                  "value": "turn"
                }
              }
            },
            {
              "op": "is_active",
              "args": {
                "participant": {
                  "op": "context",
                  "ref": "actor"
                }
              }
            },
            {
              "op": "contains",
              "args": {
                "items": {
                  "op": "concat",
                  "args": {
                    "a": {
                      "op": "reachable_grid_nodes",
                      "args": {
                        "entity": {
                          "op": "context",
                          "ref": "self"
                        },
                        "directions": {
                          "op": "list",
                          "args": {
                            "values": [
                              {
                                "op": "vector",
                                "args": {
                                  "row": {
                                    "op": "literal",
                                    "value": 1
                                  },
                                  "column": {
                                    "op": "literal",
                                    "value": 0
                                  }
                                }
                              }
                            ]
                          }
                        },
                        "max_steps": {
                          "op": "literal",
                          "value": 1
                        },
                        "leap": {
                          "op": "literal",
                          "value": false
                        },
                        "orientation": {
                          "op": "owner_orientation",
                          "args": {
                            "entity": {
                              "op": "context",
                              "ref": "self"
                            }
                          }
                        },
                        "target_occupancy": {
                          "op": "literal",
                          "value": "empty"
                        },
                        "state": {
                          "op": "context",
                          "ref": "observed_state"
                        }
                      }
                    },
                    "b": {
                      "op": "concat",
                      "args": {
                        "a": {
                          "op": "if",
                          "args": {
                            "condition": {
                              "op": "not",
                              "args": {
                                "value": {
                                  "op": "field",
                                  "args": {
                                    "entity": {
                                      "op": "context",
                                      "ref": "self"
                                    },
                                    "key": {
                                      "op": "literal",
                                      "value": "moved"
                                    }
                                  }
                                }
                              }
                            },
                            "then": {
                              "op": "only_path_distance",
                              "args": {
                                "nodes": {
                                  "op": "reachable_grid_nodes",
                                  "args": {
                                    "entity": {
                                      "op": "context",
                                      "ref": "self"
                                    },
                                    "directions": {
                                      "op": "list",
                                      "args": {
                                        "values": [
                                          {
                                            "op": "vector",
                                            "args": {
                                              "row": {
                                                "op": "literal",
                                                "value": 1
                                              },
                                              "column": {
                                                "op": "literal",
                                                "value": 0
                                              }
                                            }
                                          }
                                        ]
                                      }
                                    },
                                    "max_steps": {
                                      "op": "literal",
                                      "value": 2
                                    },
                                    "leap": {
                                      "op": "literal",
                                      "value": false
                                    },
                                    "orientation": {
                                      "op": "owner_orientation",
                                      "args": {
                                        "entity": {
                                          "op": "context",
                                          "ref": "self"
                                        }
                                      }
                                    },
                                    "target_occupancy": {
                                      "op": "literal",
                                      "value": "empty"
                                    },
                                    "state": {
                                      "op": "context",
                                      "ref": "observed_state"
                                    }
                                  }
                                },
                                "distance": {
                                  "op": "literal",
                                  "value": 2
                                }
                              }
                            },
                            "otherwise": {
                              "op": "list",
                              "args": {
                                "values": []
                              }
                            }
                          }
                        },
                        "b": {
                          "op": "reachable_grid_nodes",
                          "args": {
                            "entity": {
                              "op": "context",
                              "ref": "self"
                            },
                            "directions": {
                              "op": "list",
                              "args": {
                                "values": [
                                  {
                                    "op": "vector",
                                    "args": {
                                      "row": {
                                        "op": "literal",
                                        "value": 1
                                      },
                                      "column": {
                                        "op": "literal",
                                        "value": -1
                                      }
                                    }
                                  },
                                  {
                                    "op": "vector",
                                    "args": {
                                      "row": {
                                        "op": "literal",
                                        "value": 1
                                      },
                                      "column": {
                                        "op": "literal",
                                        "value": 1
                                      }
                                    }
                                  }
                                ]
                              }
                            },
                            "max_steps": {
                              "op": "literal",
                              "value": 1
                            },
                            "leap": {
                              "op": "literal",
                              "value": false
                            },
                            "orientation": {
                              "op": "owner_orientation",
                              "args": {
                                "entity": {
                                  "op": "context",
                                  "ref": "self"
                                }
                              }
                            },
                            "target_occupancy": {
                              "op": "literal",
                              "value": "opponent"
                            },
                            "state": {
                              "op": "context",
                              "ref": "observed_state"
                            }
                          }
                        }
                      }
                    }
                  }
                },
                "value": {
                  "op": "context",
                  "ref": "argument.to"
                }
              }
            },
            {
              "op": "none_match",
              "args": {
                "items": {
                  "op": "entities_at",
                  "args": {
                    "node": {
                      "op": "context",
                      "ref": "argument.to"
                    }
                  }
                },
                "variable": {
                  "op": "literal",
                  "value": "other"
                },
                "predicate": {
                  "op": "eq",
                  "args": {
                    "a": {
                      "op": "owner",
                      "args": {
                        "entity": {
                          "op": "context",
                          "ref": "local.other"
                        }
                      }
                    },
                    "b": {
                      "op": "owner",
                      "args": {
                        "entity": {
                          "op": "context",
                          "ref": "self"
                        }
                      }
                    }
                  }
                }
              }
            },
            {
              "op": "none_match",
              "args": {
                "items": {
                  "op": "entities_matching",
                  "args": {
                    "entity_type": {
                      "op": "literal",
                      "value": "king"
                    },
                    "owner": {
                      "op": "context",
                      "ref": "actor"
                    },
                    "state": {
                      "op": "preview",
                      "args": {
                        "state": {
                          "op": "context",
                          "ref": "observed_state"
                        },
                        "effects": {
                          "op": "list",
                          "args": {
                            "values": [
                              {
                                "op": "effect_value",
                                "args": {
                                  "name": {
                                    "op": "literal",
                                    "value": "move_entity"
                                  },
                                  "entity": {
                                    "op": "context",
                                    "ref": "self"
                                  },
                                  "destination": {
                                    "op": "context",
                                    "ref": "argument.to"
                                  }
                                }
                              }
                            ]
                          }
                        }
                      }
                    }
                  }
                },
                "variable": {
                  "op": "literal",
                  "value": "protected"
                },
                "predicate": {
                  "op": "threatened",
                  "args": {
                    "entity": {
                      "op": "context",
                      "ref": "local.protected"
                    },
                    "state": {
                      "op": "preview",
                      "args": {
                        "state": {
                          "op": "context",
                          "ref": "observed_state"
                        },
                        "effects": {
                          "op": "list",
                          "args": {
                            "values": [
                              {
                                "op": "effect_value",
                                "args": {
                                  "name": {
                                    "op": "literal",
                                    "value": "move_entity"
                                  },
                                  "entity": {
                                    "op": "context",
                                    "ref": "self"
                                  },
                                  "destination": {
                                    "op": "context",
                                    "ref": "argument.to"
                                  }
                                }
                              }
                            ]
                          }
                        }
                      }
                    }
                  }
                }
              }
            },
            {
              "op": "none_match",
              "args": {
                "items": {
                  "op": "entities_at",
                  "args": {
                    "node": {
                      "op": "context",
                      "ref": "argument.to"
                    }
                  }
                },
                "variable": {
                  "op": "literal",
                  "value": "occupant"
                },
                "predicate": {
                  "op": "contains",
                  "args": {
                    "items": {
                      "op": "entities_of_type",
                      "args": {
                        "entity_type": {
                          "op": "literal",
                          "value": "king"
                        }
                      }
                    },
                    "value": {
                      "op": "context",
                      "ref": "local.occupant"
                    }
                  }
                }
              }
            }
          ]
        }
      },
      "effects": [
        {
          "op": "remove_matching_entities",
          "args": {
            "node": {
              "op": "context",
              "ref": "argument.to"
            },
            "exclude_owner": {
              "op": "context",
              "ref": "actor"
            }
          }
        },
        {
          "op": "move_entity",
          "args": {
            "entity": {
              "op": "context",
              "ref": "self"
            },
            "destination": {
              "op": "context",
              "ref": "argument.to"
            }
          }
        },
        {
          "op": "emit_event",
          "args": {
            "name": {
              "op": "literal",
              "value": "piece.moved"
            }
          }
        },
        {
          "op": "set_field",
          "args": {
            "entity": {
              "op": "context",
              "ref": "self"
            },
            "field": {
              "op": "literal",
              "value": "moved"
            },
            "value": {
              "op": "literal",
              "value": true
            }
          }
        },
        {
          "op": "change_entity_type",
          "when": {
            "op": "on_board_edge",
            "args": {
              "entity": {
                "op": "context",
                "ref": "self"
              },
              "edge": {
                "op": "literal",
                "value": "promotion"
              }
            }
          },
          "args": {
            "entity": {
              "op": "context",
              "ref": "self"
            },
            "to": {
              "op": "if",
              "args": {
                "condition": {
                  "op": "is_present",
                  "args": {
                    "value": {
                      "op": "context",
                      "ref": "argument.promotion"
                    }
                  }
                },
                "then": {
                  "op": "context",
                  "ref": "argument.promotion"
                },
                "otherwise": {
                  "op": "literal",
                  "value": "queen"
                }
              }
            }
          }
        },
        {
          "op": "advance_turn",
          "args": {}
        }
      ],
      "priority": 0,
      "parameters": [
        {
          "key": "to",
          "type": "entity"
        },
        {
          "key": "promotion",
          "type": "text",
          "required": false,
          "choices": [
            "queen",
            "rook",
            "bishop",
            "knight"
          ]
        }
      ]
    },
    {
      "key": "generate",
      "entity": "pawn",
      "trigger": "hook",
      "phase": "turn",
      "condition": {
        "op": "eq",
        "args": {
          "a": {
            "op": "owner",
            "args": {
              "entity": {
                "op": "context",
                "ref": "self"
              }
            }
          },
          "b": {
            "op": "context",
            "ref": "actor"
          }
        }
      },
      "effects": [
        {
          "op": "emit_candidate",
          "args": {
            "source": {
              "op": "context",
              "ref": "self"
            },
            "destination": {
              "op": "context",
              "ref": "candidate"
            }
          }
        }
      ],
      "priority": 0,
      "hook": "action.generate",
      "iterator": {
        "op": "concat",
        "args": {
          "a": {
            "op": "reachable_grid_nodes",
            "args": {
              "entity": {
                "op": "context",
                "ref": "self"
              },
              "directions": {
                "op": "list",
                "args": {
                  "values": [
                    {
                      "op": "vector",
                      "args": {
                        "row": {
                          "op": "literal",
                          "value": 1
                        },
                        "column": {
                          "op": "literal",
                          "value": 0
                        }
                      }
                    }
                  ]
                }
              },
              "max_steps": {
                "op": "literal",
                "value": 1
              },
              "leap": {
                "op": "literal",
                "value": false
              },
              "orientation": {
                "op": "owner_orientation",
                "args": {
                  "entity": {
                    "op": "context",
                    "ref": "self"
                  }
                }
              },
              "target_occupancy": {
                "op": "literal",
                "value": "empty"
              },
              "state": {
                "op": "context",
                "ref": "observed_state"
              }
            }
          },
          "b": {
            "op": "concat",
            "args": {
              "a": {
                "op": "if",
                "args": {
                  "condition": {
                    "op": "not",
                    "args": {
                      "value": {
                        "op": "field",
                        "args": {
                          "entity": {
                            "op": "context",
                            "ref": "self"
                          },
                          "key": {
                            "op": "literal",
                            "value": "moved"
                          }
                        }
                      }
                    }
                  },
                  "then": {
                    "op": "only_path_distance",
                    "args": {
                      "nodes": {
                        "op": "reachable_grid_nodes",
                        "args": {
                          "entity": {
                            "op": "context",
                            "ref": "self"
                          },
                          "directions": {
                            "op": "list",
                            "args": {
                              "values": [
                                {
                                  "op": "vector",
                                  "args": {
                                    "row": {
                                      "op": "literal",
                                      "value": 1
                                    },
                                    "column": {
                                      "op": "literal",
                                      "value": 0
                                    }
                                  }
                                }
                              ]
                            }
                          },
                          "max_steps": {
                            "op": "literal",
                            "value": 2
                          },
                          "leap": {
                            "op": "literal",
                            "value": false
                          },
                          "orientation": {
                            "op": "owner_orientation",
                            "args": {
                              "entity": {
                                "op": "context",
                                "ref": "self"
                              }
                            }
                          },
                          "target_occupancy": {
                            "op": "literal",
                            "value": "empty"
                          },
                          "state": {
                            "op": "context",
                            "ref": "observed_state"
                          }
                        }
                      },
                      "distance": {
                        "op": "literal",
                        "value": 2
                      }
                    }
                  },
                  "otherwise": {
                    "op": "list",
                    "args": {
                      "values": []
                    }
                  }
                }
              },
              "b": {
                "op": "reachable_grid_nodes",
                "args": {
                  "entity": {
                    "op": "context",
                    "ref": "self"
                  },
                  "directions": {
                    "op": "list",
                    "args": {
                      "values": [
                        {
                          "op": "vector",
                          "args": {
                            "row": {
                              "op": "literal",
                              "value": 1
                            },
                            "column": {
                              "op": "literal",
                              "value": -1
                            }
                          }
                        },
                        {
                          "op": "vector",
                          "args": {
                            "row": {
                              "op": "literal",
                              "value": 1
                            },
                            "column": {
                              "op": "literal",
                              "value": 1
                            }
                          }
                        }
                      ]
                    }
                  },
                  "max_steps": {
                    "op": "literal",
                    "value": 1
                  },
                  "leap": {
                    "op": "literal",
                    "value": false
                  },
                  "orientation": {
                    "op": "owner_orientation",
                    "args": {
                      "entity": {
                        "op": "context",
                        "ref": "self"
                      }
                    }
                  },
                  "target_occupancy": {
                    "op": "literal",
                    "value": "opponent"
                  },
                  "state": {
                    "op": "context",
                    "ref": "observed_state"
                  }
                }
              }
            }
          }
        }
      },
      "variable": "candidate"
    },
    {
      "key": "castle_king",
      "entity": "king",
      "trigger": "command",
      "phase": "turn",
      "condition": {
        "op": "and",
        "args": {
          "values": [
            {
              "op": "not",
              "args": {
                "value": {
                  "op": "field",
                  "args": {
                    "entity": {
                      "op": "context",
                      "ref": "self"
                    },
                    "key": {
                      "op": "literal",
                      "value": "moved"
                    }
                  }
                }
              }
            },
            {
              "op": "is_present",
              "args": {
                "value": {
                  "op": "first",
                  "args": {
                    "items": {
                      "op": "filter",
                      "args": {
                        "items": {
                          "op": "entities_of_type",
                          "args": {
                            "entity_type": {
                              "op": "literal",
                              "value": "rook"
                            }
                          }
                        },
                        "variable": {
                          "op": "literal",
                          "value": "r"
                        },
                        "predicate": {
                          "op": "and",
                          "args": {
                            "values": [
                              {
                                "op": "eq",
                                "args": {
                                  "a": {
                                    "op": "owner",
                                    "args": {
                                      "entity": {
                                        "op": "context",
                                        "ref": "local.r"
                                      }
                                    }
                                  },
                                  "b": {
                                    "op": "context",
                                    "ref": "actor"
                                  }
                                }
                              },
                              {
                                "op": "not",
                                "args": {
                                  "value": {
                                    "op": "field",
                                    "args": {
                                      "entity": {
                                        "op": "context",
                                        "ref": "local.r"
                                      },
                                      "key": {
                                        "op": "literal",
                                        "value": "moved"
                                      }
                                    }
                                  }
                                }
                              },
                              {
                                "op": "eq",
                                "args": {
                                  "a": {
                                    "op": "entity_location",
                                    "args": {
                                      "entity": {
                                        "op": "context",
                                        "ref": "local.r"
                                      }
                                    }
                                  },
                                  "b": {
                                    "op": "grid_edge",
                                    "args": {
                                      "entity": {
                                        "op": "context",
                                        "ref": "self"
                                      },
                                      "horizontal": {
                                        "op": "literal",
                                        "value": "right"
                                      }
                                    }
                                  }
                                }
                              }
                            ]
                          }
                        }
                      }
                    }
                  }
                }
              }
            },
            {
              "op": "path_clear",
              "args": {
                "nodes": {
                  "op": "grid_between",
                  "args": {
                    "first": {
                      "op": "entity_location",
                      "args": {
                        "entity": {
                          "op": "context",
                          "ref": "self"
                        }
                      }
                    },
                    "last": {
                      "op": "entity_location",
                      "args": {
                        "entity": {
                          "op": "first",
                          "args": {
                            "items": {
                              "op": "filter",
                              "args": {
                                "items": {
                                  "op": "entities_of_type",
                                  "args": {
                                    "entity_type": {
                                      "op": "literal",
                                      "value": "rook"
                                    }
                                  }
                                },
                                "variable": {
                                  "op": "literal",
                                  "value": "r"
                                },
                                "predicate": {
                                  "op": "and",
                                  "args": {
                                    "values": [
                                      {
                                        "op": "eq",
                                        "args": {
                                          "a": {
                                            "op": "owner",
                                            "args": {
                                              "entity": {
                                                "op": "context",
                                                "ref": "local.r"
                                              }
                                            }
                                          },
                                          "b": {
                                            "op": "context",
                                            "ref": "actor"
                                          }
                                        }
                                      },
                                      {
                                        "op": "not",
                                        "args": {
                                          "value": {
                                            "op": "field",
                                            "args": {
                                              "entity": {
                                                "op": "context",
                                                "ref": "local.r"
                                              },
                                              "key": {
                                                "op": "literal",
                                                "value": "moved"
                                              }
                                            }
                                          }
                                        }
                                      },
                                      {
                                        "op": "eq",
                                        "args": {
                                          "a": {
                                            "op": "entity_location",
                                            "args": {
                                              "entity": {
                                                "op": "context",
                                                "ref": "local.r"
                                              }
                                            }
                                          },
                                          "b": {
                                            "op": "grid_edge",
                                            "args": {
                                              "entity": {
                                                "op": "context",
                                                "ref": "self"
                                              },
                                              "horizontal": {
                                                "op": "literal",
                                                "value": "right"
                                              }
                                            }
                                          }
                                        }
                                      }
                                    ]
                                  }
                                }
                              }
                            }
                          }
                        }
                      }
                    }
                  }
                }
              }
            },
            {
              "op": "none_match",
              "args": {
                "items": {
                  "op": "list",
                  "args": {
                    "values": [
                      {
                        "op": "entity_location",
                        "args": {
                          "entity": {
                            "op": "context",
                            "ref": "self"
                          }
                        }
                      },
                      {
                        "op": "grid_offset",
                        "args": {
                          "entity": {
                            "op": "context",
                            "ref": "self"
                          },
                          "row": {
                            "op": "literal",
                            "value": 0
                          },
                          "column": {
                            "op": "literal",
                            "value": 1
                          }
                        }
                      },
                      {
                        "op": "grid_offset",
                        "args": {
                          "entity": {
                            "op": "context",
                            "ref": "self"
                          },
                          "row": {
                            "op": "literal",
                            "value": 0
                          },
                          "column": {
                            "op": "literal",
                            "value": 2
                          }
                        }
                      }
                    ]
                  }
                },
                "variable": {
                  "op": "literal",
                  "value": "square"
                },
                "predicate": {
                  "op": "attacked_node",
                  "args": {
                    "node": {
                      "op": "context",
                      "ref": "local.square"
                    },
                    "by": {
                      "op": "opponents",
                      "args": {
                        "participant": {
                          "op": "context",
                          "ref": "actor"
                        }
                      }
                    }
                  }
                }
              }
            }
          ]
        }
      },
      "effects": [
        {
          "op": "move_entity",
          "args": {
            "entity": {
              "op": "context",
              "ref": "self"
            },
            "destination": {
              "op": "grid_offset",
              "args": {
                "entity": {
                  "op": "context",
                  "ref": "self"
                },
                "row": {
                  "op": "literal",
                  "value": 0
                },
                "column": {
                  "op": "literal",
                  "value": 2
                }
              }
            }
          }
        },
        {
          "op": "move_entity",
          "args": {
            "entity": {
              "op": "first",
              "args": {
                "items": {
                  "op": "filter",
                  "args": {
                    "items": {
                      "op": "entities_of_type",
                      "args": {
                        "entity_type": {
                          "op": "literal",
                          "value": "rook"
                        }
                      }
                    },
                    "variable": {
                      "op": "literal",
                      "value": "r"
                    },
                    "predicate": {
                      "op": "and",
                      "args": {
                        "values": [
                          {
                            "op": "eq",
                            "args": {
                              "a": {
                                "op": "owner",
                                "args": {
                                  "entity": {
                                    "op": "context",
                                    "ref": "local.r"
                                  }
                                }
                              },
                              "b": {
                                "op": "context",
                                "ref": "actor"
                              }
                            }
                          },
                          {
                            "op": "not",
                            "args": {
                              "value": {
                                "op": "field",
                                "args": {
                                  "entity": {
                                    "op": "context",
                                    "ref": "local.r"
                                  },
                                  "key": {
                                    "op": "literal",
                                    "value": "moved"
                                  }
                                }
                              }
                            }
                          },
                          {
                            "op": "eq",
                            "args": {
                              "a": {
                                "op": "entity_location",
                                "args": {
                                  "entity": {
                                    "op": "context",
                                    "ref": "local.r"
                                  }
                                }
                              },
                              "b": {
                                "op": "grid_edge",
                                "args": {
                                  "entity": {
                                    "op": "context",
                                    "ref": "self"
                                  },
                                  "horizontal": {
                                    "op": "literal",
                                    "value": "right"
                                  }
                                }
                              }
                            }
                          }
                        ]
                      }
                    }
                  }
                }
              }
            },
            "destination": {
              "op": "grid_offset",
              "args": {
                "entity": {
                  "op": "context",
                  "ref": "self"
                },
                "row": {
                  "op": "literal",
                  "value": 0
                },
                "column": {
                  "op": "literal",
                  "value": 1
                }
              }
            }
          }
        },
        {
          "op": "set_field",
          "args": {
            "entity": {
              "op": "context",
              "ref": "self"
            },
            "field": {
              "op": "literal",
              "value": "moved"
            },
            "value": {
              "op": "literal",
              "value": true
            }
          }
        },
        {
          "op": "set_field",
          "args": {
            "entity": {
              "op": "first",
              "args": {
                "items": {
                  "op": "filter",
                  "args": {
                    "items": {
                      "op": "entities_of_type",
                      "args": {
                        "entity_type": {
                          "op": "literal",
                          "value": "rook"
                        }
                      }
                    },
                    "variable": {
                      "op": "literal",
                      "value": "r"
                    },
                    "predicate": {
                      "op": "and",
                      "args": {
                        "values": [
                          {
                            "op": "eq",
                            "args": {
                              "a": {
                                "op": "owner",
                                "args": {
                                  "entity": {
                                    "op": "context",
                                    "ref": "local.r"
                                  }
                                }
                              },
                              "b": {
                                "op": "context",
                                "ref": "actor"
                              }
                            }
                          },
                          {
                            "op": "not",
                            "args": {
                              "value": {
                                "op": "field",
                                "args": {
                                  "entity": {
                                    "op": "context",
                                    "ref": "local.r"
                                  },
                                  "key": {
                                    "op": "literal",
                                    "value": "moved"
                                  }
                                }
                              }
                            }
                          },
                          {
                            "op": "eq",
                            "args": {
                              "a": {
                                "op": "entity_location",
                                "args": {
                                  "entity": {
                                    "op": "context",
                                    "ref": "local.r"
                                  }
                                }
                              },
                              "b": {
                                "op": "grid_edge",
                                "args": {
                                  "entity": {
                                    "op": "context",
                                    "ref": "self"
                                  },
                                  "horizontal": {
                                    "op": "literal",
                                    "value": "right"
                                  }
                                }
                              }
                            }
                          }
                        ]
                      }
                    }
                  }
                }
              }
            },
            "field": {
              "op": "literal",
              "value": "moved"
            },
            "value": {
              "op": "literal",
              "value": true
            }
          }
        },
        {
          "op": "emit_event",
          "args": {
            "name": {
              "op": "literal",
              "value": "piece.castled"
            }
          }
        },
        {
          "op": "advance_turn",
          "args": {}
        }
      ],
      "priority": 0
    },
    {
      "key": "castle_queen",
      "entity": "king",
      "trigger": "command",
      "phase": "turn",
      "condition": {
        "op": "and",
        "args": {
          "values": [
            {
              "op": "not",
              "args": {
                "value": {
                  "op": "field",
                  "args": {
                    "entity": {
                      "op": "context",
                      "ref": "self"
                    },
                    "key": {
                      "op": "literal",
                      "value": "moved"
                    }
                  }
                }
              }
            },
            {
              "op": "is_present",
              "args": {
                "value": {
                  "op": "first",
                  "args": {
                    "items": {
                      "op": "filter",
                      "args": {
                        "items": {
                          "op": "entities_of_type",
                          "args": {
                            "entity_type": {
                              "op": "literal",
                              "value": "rook"
                            }
                          }
                        },
                        "variable": {
                          "op": "literal",
                          "value": "r"
                        },
                        "predicate": {
                          "op": "and",
                          "args": {
                            "values": [
                              {
                                "op": "eq",
                                "args": {
                                  "a": {
                                    "op": "owner",
                                    "args": {
                                      "entity": {
                                        "op": "context",
                                        "ref": "local.r"
                                      }
                                    }
                                  },
                                  "b": {
                                    "op": "context",
                                    "ref": "actor"
                                  }
                                }
                              },
                              {
                                "op": "not",
                                "args": {
                                  "value": {
                                    "op": "field",
                                    "args": {
                                      "entity": {
                                        "op": "context",
                                        "ref": "local.r"
                                      },
                                      "key": {
                                        "op": "literal",
                                        "value": "moved"
                                      }
                                    }
                                  }
                                }
                              },
                              {
                                "op": "eq",
                                "args": {
                                  "a": {
                                    "op": "entity_location",
                                    "args": {
                                      "entity": {
                                        "op": "context",
                                        "ref": "local.r"
                                      }
                                    }
                                  },
                                  "b": {
                                    "op": "grid_edge",
                                    "args": {
                                      "entity": {
                                        "op": "context",
                                        "ref": "self"
                                      },
                                      "horizontal": {
                                        "op": "literal",
                                        "value": "left"
                                      }
                                    }
                                  }
                                }
                              }
                            ]
                          }
                        }
                      }
                    }
                  }
                }
              }
            },
            {
              "op": "path_clear",
              "args": {
                "nodes": {
                  "op": "grid_between",
                  "args": {
                    "first": {
                      "op": "entity_location",
                      "args": {
                        "entity": {
                          "op": "context",
                          "ref": "self"
                        }
                      }
                    },
                    "last": {
                      "op": "entity_location",
                      "args": {
                        "entity": {
                          "op": "first",
                          "args": {
                            "items": {
                              "op": "filter",
                              "args": {
                                "items": {
                                  "op": "entities_of_type",
                                  "args": {
                                    "entity_type": {
                                      "op": "literal",
                                      "value": "rook"
                                    }
                                  }
                                },
                                "variable": {
                                  "op": "literal",
                                  "value": "r"
                                },
                                "predicate": {
                                  "op": "and",
                                  "args": {
                                    "values": [
                                      {
                                        "op": "eq",
                                        "args": {
                                          "a": {
                                            "op": "owner",
                                            "args": {
                                              "entity": {
                                                "op": "context",
                                                "ref": "local.r"
                                              }
                                            }
                                          },
                                          "b": {
                                            "op": "context",
                                            "ref": "actor"
                                          }
                                        }
                                      },
                                      {
                                        "op": "not",
                                        "args": {
                                          "value": {
                                            "op": "field",
                                            "args": {
                                              "entity": {
                                                "op": "context",
                                                "ref": "local.r"
                                              },
                                              "key": {
                                                "op": "literal",
                                                "value": "moved"
                                              }
                                            }
                                          }
                                        }
                                      },
                                      {
                                        "op": "eq",
                                        "args": {
                                          "a": {
                                            "op": "entity_location",
                                            "args": {
                                              "entity": {
                                                "op": "context",
                                                "ref": "local.r"
                                              }
                                            }
                                          },
                                          "b": {
                                            "op": "grid_edge",
                                            "args": {
                                              "entity": {
                                                "op": "context",
                                                "ref": "self"
                                              },
                                              "horizontal": {
                                                "op": "literal",
                                                "value": "left"
                                              }
                                            }
                                          }
                                        }
                                      }
                                    ]
                                  }
                                }
                              }
                            }
                          }
                        }
                      }
                    }
                  }
                }
              }
            },
            {
              "op": "none_match",
              "args": {
                "items": {
                  "op": "list",
                  "args": {
                    "values": [
                      {
                        "op": "entity_location",
                        "args": {
                          "entity": {
                            "op": "context",
                            "ref": "self"
                          }
                        }
                      },
                      {
                        "op": "grid_offset",
                        "args": {
                          "entity": {
                            "op": "context",
                            "ref": "self"
                          },
                          "row": {
                            "op": "literal",
                            "value": 0
                          },
                          "column": {
                            "op": "literal",
                            "value": -1
                          }
                        }
                      },
                      {
                        "op": "grid_offset",
                        "args": {
                          "entity": {
                            "op": "context",
                            "ref": "self"
                          },
                          "row": {
                            "op": "literal",
                            "value": 0
                          },
                          "column": {
                            "op": "literal",
                            "value": -2
                          }
                        }
                      }
                    ]
                  }
                },
                "variable": {
                  "op": "literal",
                  "value": "square"
                },
                "predicate": {
                  "op": "attacked_node",
                  "args": {
                    "node": {
                      "op": "context",
                      "ref": "local.square"
                    },
                    "by": {
                      "op": "opponents",
                      "args": {
                        "participant": {
                          "op": "context",
                          "ref": "actor"
                        }
                      }
                    }
                  }
                }
              }
            }
          ]
        }
      },
      "effects": [
        {
          "op": "move_entity",
          "args": {
            "entity": {
              "op": "context",
              "ref": "self"
            },
            "destination": {
              "op": "grid_offset",
              "args": {
                "entity": {
                  "op": "context",
                  "ref": "self"
                },
                "row": {
                  "op": "literal",
                  "value": 0
                },
                "column": {
                  "op": "literal",
                  "value": -2
                }
              }
            }
          }
        },
        {
          "op": "move_entity",
          "args": {
            "entity": {
              "op": "first",
              "args": {
                "items": {
                  "op": "filter",
                  "args": {
                    "items": {
                      "op": "entities_of_type",
                      "args": {
                        "entity_type": {
                          "op": "literal",
                          "value": "rook"
                        }
                      }
                    },
                    "variable": {
                      "op": "literal",
                      "value": "r"
                    },
                    "predicate": {
                      "op": "and",
                      "args": {
                        "values": [
                          {
                            "op": "eq",
                            "args": {
                              "a": {
                                "op": "owner",
                                "args": {
                                  "entity": {
                                    "op": "context",
                                    "ref": "local.r"
                                  }
                                }
                              },
                              "b": {
                                "op": "context",
                                "ref": "actor"
                              }
                            }
                          },
                          {
                            "op": "not",
                            "args": {
                              "value": {
                                "op": "field",
                                "args": {
                                  "entity": {
                                    "op": "context",
                                    "ref": "local.r"
                                  },
                                  "key": {
                                    "op": "literal",
                                    "value": "moved"
                                  }
                                }
                              }
                            }
                          },
                          {
                            "op": "eq",
                            "args": {
                              "a": {
                                "op": "entity_location",
                                "args": {
                                  "entity": {
                                    "op": "context",
                                    "ref": "local.r"
                                  }
                                }
                              },
                              "b": {
                                "op": "grid_edge",
                                "args": {
                                  "entity": {
                                    "op": "context",
                                    "ref": "self"
                                  },
                                  "horizontal": {
                                    "op": "literal",
                                    "value": "left"
                                  }
                                }
                              }
                            }
                          }
                        ]
                      }
                    }
                  }
                }
              }
            },
            "destination": {
              "op": "grid_offset",
              "args": {
                "entity": {
                  "op": "context",
                  "ref": "self"
                },
                "row": {
                  "op": "literal",
                  "value": 0
                },
                "column": {
                  "op": "literal",
                  "value": -1
                }
              }
            }
          }
        },
        {
          "op": "set_field",
          "args": {
            "entity": {
              "op": "context",
              "ref": "self"
            },
            "field": {
              "op": "literal",
              "value": "moved"
            },
            "value": {
              "op": "literal",
              "value": true
            }
          }
        },
        {
          "op": "set_field",
          "args": {
            "entity": {
              "op": "first",
              "args": {
                "items": {
                  "op": "filter",
                  "args": {
                    "items": {
                      "op": "entities_of_type",
                      "args": {
                        "entity_type": {
                          "op": "literal",
                          "value": "rook"
                        }
                      }
                    },
                    "variable": {
                      "op": "literal",
                      "value": "r"
                    },
                    "predicate": {
                      "op": "and",
                      "args": {
                        "values": [
                          {
                            "op": "eq",
                            "args": {
                              "a": {
                                "op": "owner",
                                "args": {
                                  "entity": {
                                    "op": "context",
                                    "ref": "local.r"
                                  }
                                }
                              },
                              "b": {
                                "op": "context",
                                "ref": "actor"
                              }
                            }
                          },
                          {
                            "op": "not",
                            "args": {
                              "value": {
                                "op": "field",
                                "args": {
                                  "entity": {
                                    "op": "context",
                                    "ref": "local.r"
                                  },
                                  "key": {
                                    "op": "literal",
                                    "value": "moved"
                                  }
                                }
                              }
                            }
                          },
                          {
                            "op": "eq",
                            "args": {
                              "a": {
                                "op": "entity_location",
                                "args": {
                                  "entity": {
                                    "op": "context",
                                    "ref": "local.r"
                                  }
                                }
                              },
                              "b": {
                                "op": "grid_edge",
                                "args": {
                                  "entity": {
                                    "op": "context",
                                    "ref": "self"
                                  },
                                  "horizontal": {
                                    "op": "literal",
                                    "value": "left"
                                  }
                                }
                              }
                            }
                          }
                        ]
                      }
                    }
                  }
                }
              }
            },
            "field": {
              "op": "literal",
              "value": "moved"
            },
            "value": {
              "op": "literal",
              "value": true
            }
          }
        },
        {
          "op": "emit_event",
          "args": {
            "name": {
              "op": "literal",
              "value": "piece.castled"
            }
          }
        },
        {
          "op": "advance_turn",
          "args": {}
        }
      ],
      "priority": 0
    },
    {
      "key": "en_passant",
      "entity": "pawn",
      "trigger": "command",
      "phase": "turn",
      "condition": {
        "op": "and",
        "args": {
          "values": [
            {
              "op": "eq",
              "args": {
                "a": {
                  "op": "context",
                  "ref": "argument.to"
                },
                "b": {
                  "op": "field",
                  "args": {
                    "entity": {
                      "op": "context",
                      "ref": "game"
                    },
                    "key": {
                      "op": "literal",
                      "value": "en_passant"
                    }
                  }
                }
              }
            },
            {
              "op": "is_present",
              "args": {
                "value": {
                  "op": "first",
                  "args": {
                    "items": {
                      "op": "filter",
                      "args": {
                        "items": {
                          "op": "entities_of_type",
                          "args": {
                            "entity_type": {
                              "op": "literal",
                              "value": "pawn"
                            }
                          }
                        },
                        "variable": {
                          "op": "literal",
                          "value": "p"
                        },
                        "predicate": {
                          "op": "and",
                          "args": {
                            "values": [
                              {
                                "op": "not",
                                "args": {
                                  "value": {
                                    "op": "eq",
                                    "args": {
                                      "a": {
                                        "op": "owner",
                                        "args": {
                                          "entity": {
                                            "op": "context",
                                            "ref": "local.p"
                                          }
                                        }
                                      },
                                      "b": {
                                        "op": "context",
                                        "ref": "actor"
                                      }
                                    }
                                  }
                                }
                              },
                              {
                                "op": "eq",
                                "args": {
                                  "a": {
                                    "op": "entity_location",
                                    "args": {
                                      "entity": {
                                        "op": "context",
                                        "ref": "local.p"
                                      }
                                    }
                                  },
                                  "b": {
                                    "op": "grid_offset",
                                    "args": {
                                      "entity": {
                                        "op": "context",
                                        "ref": "argument.to"
                                      },
                                      "row": {
                                        "op": "negate",
                                        "args": {
                                          "value": {
                                            "op": "owner_orientation",
                                            "args": {
                                              "entity": {
                                                "op": "context",
                                                "ref": "self"
                                              }
                                            }
                                          }
                                        }
                                      },
                                      "column": {
                                        "op": "literal",
                                        "value": 0
                                      }
                                    }
                                  }
                                }
                              }
                            ]
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
          ]
        }
      },
      "effects": [
        {
          "op": "remove_entity",
          "args": {
            "entity": {
              "op": "first",
              "args": {
                "items": {
                  "op": "filter",
                  "args": {
                    "items": {
                      "op": "entities_of_type",
                      "args": {
                        "entity_type": {
                          "op": "literal",
                          "value": "pawn"
                        }
                      }
                    },
                    "variable": {
                      "op": "literal",
                      "value": "p"
                    },
                    "predicate": {
                      "op": "and",
                      "args": {
                        "values": [
                          {
                            "op": "not",
                            "args": {
                              "value": {
                                "op": "eq",
                                "args": {
                                  "a": {
                                    "op": "owner",
                                    "args": {
                                      "entity": {
                                        "op": "context",
                                        "ref": "local.p"
                                      }
                                    }
                                  },
                                  "b": {
                                    "op": "context",
                                    "ref": "actor"
                                  }
                                }
                              }
                            }
                          },
                          {
                            "op": "eq",
                            "args": {
                              "a": {
                                "op": "entity_location",
                                "args": {
                                  "entity": {
                                    "op": "context",
                                    "ref": "local.p"
                                  }
                                }
                              },
                              "b": {
                                "op": "grid_offset",
                                "args": {
                                  "entity": {
                                    "op": "context",
                                    "ref": "argument.to"
                                  },
                                  "row": {
                                    "op": "negate",
                                    "args": {
                                      "value": {
                                        "op": "owner_orientation",
                                        "args": {
                                          "entity": {
                                            "op": "context",
                                            "ref": "self"
                                          }
                                        }
                                      }
                                    }
                                  },
                                  "column": {
                                    "op": "literal",
                                    "value": 0
                                  }
                                }
                              }
                            }
                          }
                        ]
                      }
                    }
                  }
                }
              }
            }
          }
        },
        {
          "op": "move_entity",
          "args": {
            "entity": {
              "op": "context",
              "ref": "self"
            },
            "destination": {
              "op": "context",
              "ref": "argument.to"
            }
          }
        },
        {
          "op": "set_field",
          "args": {
            "entity": {
              "op": "context",
              "ref": "self"
            },
            "field": {
              "op": "literal",
              "value": "moved"
            },
            "value": {
              "op": "literal",
              "value": true
            }
          }
        },
        {
          "op": "emit_event",
          "args": {
            "name": {
              "op": "literal",
              "value": "piece.captured"
            }
          }
        },
        {
          "op": "advance_turn",
          "args": {}
        }
      ],
      "priority": 0,
      "parameters": [
        {
          "key": "to",
          "type": "entity"
        }
      ]
    },
    {
      "key": "evaluate",
      "entity": "checkmate",
      "trigger": "hook",
      "phase": "*",
      "condition": {
        "op": "and",
        "args": {
          "values": [
            {
              "op": "attacked_node",
              "args": {
                "node": {
                  "op": "entity_location",
                  "args": {
                    "entity": {
                      "op": "first",
                      "args": {
                        "items": {
                          "op": "filter",
                          "args": {
                            "items": {
                              "op": "entities_of_type",
                              "args": {
                                "entity_type": {
                                  "op": "literal",
                                  "value": "king"
                                }
                              }
                            },
                            "variable": {
                              "op": "literal",
                              "value": "e"
                            },
                            "predicate": {
                              "op": "eq",
                              "args": {
                                "a": {
                                  "op": "owner",
                                  "args": {
                                    "entity": {
                                      "op": "context",
                                      "ref": "local.e"
                                    }
                                  }
                                },
                                "b": {
                                  "op": "next_participant",
                                  "args": {
                                    "participant": {
                                      "op": "context",
                                      "ref": "active_participant"
                                    }
                                  }
                                }
                              }
                            }
                          }
                        }
                      }
                    }
                  }
                },
                "by": {
                  "op": "opponents",
                  "args": {
                    "participant": {
                      "op": "next_participant",
                      "args": {
                        "participant": {
                          "op": "context",
                          "ref": "active_participant"
                        }
                      }
                    }
                  }
                }
              }
            },
            {
              "op": "eq",
              "args": {
                "a": {
                  "op": "available_action_count",
                  "args": {
                    "actor": {
                      "op": "next_participant",
                      "args": {
                        "participant": {
                          "op": "context",
                          "ref": "active_participant"
                        }
                      }
                    }
                  }
                },
                "b": {
                  "op": "literal",
                  "value": 0
                }
              }
            }
          ]
        }
      },
      "effects": [
        {
          "op": "complete_objective",
          "args": {
            "entity": {
              "op": "context",
              "ref": "self"
            }
          }
        },
        {
          "op": "finish_game",
          "args": {
            "result": {
              "op": "literal",
              "value": "victory"
            }
          }
        }
      ],
      "priority": 0,
      "hook": "game.evaluate"
    },
    {
      "key": "evaluate",
      "entity": "stalemate",
      "trigger": "hook",
      "phase": "*",
      "condition": {
        "op": "and",
        "args": {
          "values": [
            {
              "op": "not",
              "args": {
                "value": {
                  "op": "attacked_node",
                  "args": {
                    "node": {
                      "op": "entity_location",
                      "args": {
                        "entity": {
                          "op": "first",
                          "args": {
                            "items": {
                              "op": "filter",
                              "args": {
                                "items": {
                                  "op": "entities_of_type",
                                  "args": {
                                    "entity_type": {
                                      "op": "literal",
                                      "value": "king"
                                    }
                                  }
                                },
                                "variable": {
                                  "op": "literal",
                                  "value": "e"
                                },
                                "predicate": {
                                  "op": "eq",
                                  "args": {
                                    "a": {
                                      "op": "owner",
                                      "args": {
                                        "entity": {
                                          "op": "context",
                                          "ref": "local.e"
                                        }
                                      }
                                    },
                                    "b": {
                                      "op": "next_participant",
                                      "args": {
                                        "participant": {
                                          "op": "context",
                                          "ref": "active_participant"
                                        }
                                      }
                                    }
                                  }
                                }
                              }
                            }
                          }
                        }
                      }
                    },
                    "by": {
                      "op": "opponents",
                      "args": {
                        "participant": {
                          "op": "next_participant",
                          "args": {
                            "participant": {
                              "op": "context",
                              "ref": "active_participant"
                            }
                          }
                        }
                      }
                    }
                  }
                }
              }
            },
            {
              "op": "eq",
              "args": {
                "a": {
                  "op": "available_action_count",
                  "args": {
                    "actor": {
                      "op": "next_participant",
                      "args": {
                        "participant": {
                          "op": "context",
                          "ref": "active_participant"
                        }
                      }
                    }
                  }
                },
                "b": {
                  "op": "literal",
                  "value": 0
                }
              }
            }
          ]
        }
      },
      "effects": [
        {
          "op": "complete_objective",
          "args": {
            "entity": {
              "op": "context",
              "ref": "self"
            }
          }
        },
        {
          "op": "finish_game",
          "args": {
            "result": {
              "op": "literal",
              "value": "draw"
            }
          }
        }
      ],
      "priority": 0,
      "hook": "game.evaluate"
    },
    {
      "key": "evaluate",
      "entity": "dead_position",
      "trigger": "hook",
      "phase": "*",
      "condition": {
        "op": "no_reachable_terminal",
        "args": {
          "state": {
            "op": "context",
            "ref": "proposed_state"
          },
          "terminal": {
            "op": "literal",
            "value": "checkmate"
          },
          "max_states": {
            "op": "literal",
            "value": 250000
          }
        }
      },
      "effects": [
        {
          "op": "complete_objective",
          "args": {
            "entity": {
              "op": "context",
              "ref": "self"
            }
          }
        },
        {
          "op": "finish_game",
          "args": {
            "result": {
              "op": "literal",
              "value": "draw"
            }
          }
        }
      ],
      "priority": 0,
      "hook": "game.evaluate"
    },
    {
      "key": "evaluate",
      "entity": "repetition_draw",
      "trigger": "hook",
      "phase": "*",
      "condition": {
        "op": "gte",
        "args": {
          "a": {
            "op": "position_occurrences",
            "args": {
              "state": {
                "op": "context",
                "ref": "proposed_state"
              }
            }
          },
          "b": {
            "op": "literal",
            "value": 3
          }
        }
      },
      "effects": [
        {
          "op": "complete_objective",
          "args": {
            "entity": {
              "op": "context",
              "ref": "self"
            }
          }
        },
        {
          "op": "finish_game",
          "args": {
            "result": {
              "op": "literal",
              "value": "draw"
            }
          }
        }
      ],
      "priority": 0,
      "hook": "game.evaluate"
    },
    {
      "key": "evaluate",
      "entity": "move_count_draw",
      "trigger": "hook",
      "phase": "*",
      "condition": {
        "op": "gte",
        "args": {
          "a": {
            "op": "get_state",
            "args": {
              "state": {
                "op": "context",
                "ref": "proposed_state"
              },
              "field": {
                "op": "literal",
                "value": "halfmove_clock"
              }
            }
          },
          "b": {
            "op": "literal",
            "value": 100
          }
        }
      },
      "effects": [
        {
          "op": "complete_objective",
          "args": {
            "entity": {
              "op": "context",
              "ref": "self"
            }
          }
        },
        {
          "op": "finish_game",
          "args": {
            "result": {
              "op": "literal",
              "value": "draw"
            }
          }
        }
      ],
      "priority": 0,
      "hook": "game.evaluate"
    },
    {
      "key": "evaluate",
      "entity": "timeout",
      "trigger": "hook",
      "phase": "*",
      "condition": {
        "op": "clock_expired",
        "args": {
          "state": {
            "op": "context",
            "ref": "proposed_state"
          }
        }
      },
      "effects": [
        {
          "op": "complete_objective",
          "args": {
            "entity": {
              "op": "context",
              "ref": "self"
            }
          }
        },
        {
          "op": "finish_game",
          "args": {
            "result": {
              "op": "literal",
              "value": "computed"
            }
          }
        }
      ],
      "priority": 0,
      "hook": "game.evaluate"
    },
    {
      "key": "count",
      "entity": "capture_quest",
      "trigger": "hook",
      "phase": "*",
      "condition": {
        "op": "eq",
        "args": {
          "a": {
            "op": "event_attribute",
            "args": {
              "event": {
                "op": "context",
                "ref": "event"
              },
              "attribute": {
                "op": "literal",
                "value": "kind"
              }
            }
          },
          "b": {
            "op": "literal",
            "value": "piece.captured"
          }
        }
      },
      "effects": [
        {
          "op": "increment_field",
          "args": {
            "entity": {
              "op": "context",
              "ref": "self"
            },
            "field": {
              "op": "literal",
              "value": "progress"
            },
            "amount": {
              "op": "literal",
              "value": 1
            }
          }
        },
        {
          "op": "complete_objective",
          "args": {
            "entity": {
              "op": "context",
              "ref": "self"
            }
          },
          "when": {
            "op": "gte",
            "args": {
              "a": {
                "op": "field",
                "args": {
                  "entity": {
                    "op": "context",
                    "ref": "self"
                  },
                  "key": {
                    "op": "literal",
                    "value": "progress"
                  }
                }
              },
              "b": {
                "op": "field",
                "args": {
                  "entity": {
                    "op": "context",
                    "ref": "self"
                  },
                  "key": {
                    "op": "literal",
                    "value": "target"
                  }
                }
              }
            }
          }
        }
      ],
      "priority": 0,
      "hook": "objective.evaluate"
    },
    {
      "key": "count",
      "entity": "promotion_quest",
      "trigger": "hook",
      "phase": "*",
      "condition": {
        "op": "eq",
        "args": {
          "a": {
            "op": "event_attribute",
            "args": {
              "event": {
                "op": "context",
                "ref": "event"
              },
              "attribute": {
                "op": "literal",
                "value": "kind"
              }
            }
          },
          "b": {
            "op": "literal",
            "value": "piece.promoted"
          }
        }
      },
      "effects": [
        {
          "op": "increment_field",
          "args": {
            "entity": {
              "op": "context",
              "ref": "self"
            },
            "field": {
              "op": "literal",
              "value": "progress"
            },
            "amount": {
              "op": "literal",
              "value": 1
            }
          }
        },
        {
          "op": "complete_objective",
          "args": {
            "entity": {
              "op": "context",
              "ref": "self"
            }
          },
          "when": {
            "op": "gte",
            "args": {
              "a": {
                "op": "field",
                "args": {
                  "entity": {
                    "op": "context",
                    "ref": "self"
                  },
                  "key": {
                    "op": "literal",
                    "value": "progress"
                  }
                }
              },
              "b": {
                "op": "field",
                "args": {
                  "entity": {
                    "op": "context",
                    "ref": "self"
                  },
                  "key": {
                    "op": "literal",
                    "value": "target"
                  }
                }
              }
            }
          }
        }
      ],
      "priority": 0,
      "hook": "objective.evaluate"
    },
    {
      "key": "count",
      "entity": "castling_quest",
      "trigger": "hook",
      "phase": "*",
      "condition": {
        "op": "eq",
        "args": {
          "a": {
            "op": "event_attribute",
            "args": {
              "event": {
                "op": "context",
                "ref": "event"
              },
              "attribute": {
                "op": "literal",
                "value": "kind"
              }
            }
          },
          "b": {
            "op": "literal",
            "value": "piece.castled"
          }
        }
      },
      "effects": [
        {
          "op": "increment_field",
          "args": {
            "entity": {
              "op": "context",
              "ref": "self"
            },
            "field": {
              "op": "literal",
              "value": "progress"
            },
            "amount": {
              "op": "literal",
              "value": 1
            }
          }
        },
        {
          "op": "complete_objective",
          "args": {
            "entity": {
              "op": "context",
              "ref": "self"
            }
          },
          "when": {
            "op": "gte",
            "args": {
              "a": {
                "op": "field",
                "args": {
                  "entity": {
                    "op": "context",
                    "ref": "self"
                  },
                  "key": {
                    "op": "literal",
                    "value": "progress"
                  }
                }
              },
              "b": {
                "op": "field",
                "args": {
                  "entity": {
                    "op": "context",
                    "ref": "self"
                  },
                  "key": {
                    "op": "literal",
                    "value": "target"
                  }
                }
              }
            }
          }
        }
      ],
      "priority": 0,
      "hook": "objective.evaluate"
    }
  ],
  "visuals": [
    {
      "entity": "square",
      "primitives": [
        {
          "kind": "rectangle",
          "x": 0,
          "y": 0,
          "width": 100,
          "height": 100,
          "fill": "#e9d6b5"
        }
      ]
    },
    {
      "entity": "king",
      "primitives": [
        {
          "kind": "text",
          "x": 50,
          "y": 54,
          "text": "K",
          "fill": "#222"
        }
      ]
    },
    {
      "entity": "queen",
      "primitives": [
        {
          "kind": "text",
          "x": 50,
          "y": 54,
          "text": "Q",
          "fill": "#222"
        }
      ]
    },
    {
      "entity": "rook",
      "primitives": [
        {
          "kind": "text",
          "x": 50,
          "y": 54,
          "text": "R",
          "fill": "#222"
        }
      ]
    },
    {
      "entity": "bishop",
      "primitives": [
        {
          "kind": "text",
          "x": 50,
          "y": 54,
          "text": "B",
          "fill": "#222"
        }
      ]
    },
    {
      "entity": "knight",
      "primitives": [
        {
          "kind": "text",
          "x": 50,
          "y": 54,
          "text": "K",
          "fill": "#222"
        }
      ]
    },
    {
      "entity": "pawn",
      "primitives": [
        {
          "kind": "text",
          "x": 50,
          "y": 54,
          "text": "P",
          "fill": "#222"
        }
      ]
    }
  ],
  "assets": []
}
```

### english-draughts.json

```json
{
  "format": "bgwq.configuration",
  "format_version": 1,
  "definition": {
    "key": "english-draughts",
    "name": "English Draughts",
    "min_participants": 2,
    "max_participants": 2,
    "semantics_version": 1
  },
  "roles": [
    {
      "key": "seat_0",
      "name": "Player 1",
      "min": 1,
      "max": 1,
      "forward_row": 1
    },
    {
      "key": "seat_1",
      "name": "Player 2",
      "min": 1,
      "max": 1,
      "forward_row": -1
    }
  ],
  "phases": [
    {
      "key": "turn",
      "name": "Turn",
      "initial": true,
      "order": 0
    }
  ],
  "entities": [
    {
      "key": "game",
      "kind": "game",
      "name": "Game"
    },
    {
      "key": "board",
      "kind": "space",
      "name": "Board"
    },
    {
      "key": "square",
      "kind": "space",
      "name": "Square"
    },
    {
      "key": "man",
      "kind": "item",
      "name": "Man"
    },
    {
      "key": "king",
      "kind": "item",
      "name": "King"
    },
    {
      "key": "victory",
      "kind": "objective",
      "name": "Victory"
    },
    {
      "key": "draw",
      "kind": "objective",
      "name": "Draw"
    },
    {
      "key": "capture_quest",
      "kind": "objective",
      "name": "Capture Quest"
    }
  ],
  "seeds": [
    {
      "key": "root",
      "type": "game"
    },
    {
      "key": "board",
      "type": "board",
      "parent": "root"
    },
    {
      "key": "s0_1",
      "type": "square",
      "parent": "board",
      "row": 0,
      "column": 1,
      "x": 100,
      "y": 700
    },
    {
      "key": "s0_3",
      "type": "square",
      "parent": "board",
      "row": 0,
      "column": 3,
      "x": 300,
      "y": 700
    },
    {
      "key": "s0_5",
      "type": "square",
      "parent": "board",
      "row": 0,
      "column": 5,
      "x": 500,
      "y": 700
    },
    {
      "key": "s0_7",
      "type": "square",
      "parent": "board",
      "row": 0,
      "column": 7,
      "x": 700,
      "y": 700
    },
    {
      "key": "s1_0",
      "type": "square",
      "parent": "board",
      "row": 1,
      "column": 0,
      "x": 0,
      "y": 600
    },
    {
      "key": "s1_2",
      "type": "square",
      "parent": "board",
      "row": 1,
      "column": 2,
      "x": 200,
      "y": 600
    },
    {
      "key": "s1_4",
      "type": "square",
      "parent": "board",
      "row": 1,
      "column": 4,
      "x": 400,
      "y": 600
    },
    {
      "key": "s1_6",
      "type": "square",
      "parent": "board",
      "row": 1,
      "column": 6,
      "x": 600,
      "y": 600
    },
    {
      "key": "s2_1",
      "type": "square",
      "parent": "board",
      "row": 2,
      "column": 1,
      "x": 100,
      "y": 500
    },
    {
      "key": "s2_3",
      "type": "square",
      "parent": "board",
      "row": 2,
      "column": 3,
      "x": 300,
      "y": 500
    },
    {
      "key": "s2_5",
      "type": "square",
      "parent": "board",
      "row": 2,
      "column": 5,
      "x": 500,
      "y": 500
    },
    {
      "key": "s2_7",
      "type": "square",
      "parent": "board",
      "row": 2,
      "column": 7,
      "x": 700,
      "y": 500
    },
    {
      "key": "s3_0",
      "type": "square",
      "parent": "board",
      "row": 3,
      "column": 0,
      "x": 0,
      "y": 400
    },
    {
      "key": "s3_2",
      "type": "square",
      "parent": "board",
      "row": 3,
      "column": 2,
      "x": 200,
      "y": 400
    },
    {
      "key": "s3_4",
      "type": "square",
      "parent": "board",
      "row": 3,
      "column": 4,
      "x": 400,
      "y": 400
    },
    {
      "key": "s3_6",
      "type": "square",
      "parent": "board",
      "row": 3,
      "column": 6,
      "x": 600,
      "y": 400
    },
    {
      "key": "s4_1",
      "type": "square",
      "parent": "board",
      "row": 4,
      "column": 1,
      "x": 100,
      "y": 300
    },
    {
      "key": "s4_3",
      "type": "square",
      "parent": "board",
      "row": 4,
      "column": 3,
      "x": 300,
      "y": 300
    },
    {
      "key": "s4_5",
      "type": "square",
      "parent": "board",
      "row": 4,
      "column": 5,
      "x": 500,
      "y": 300
    },
    {
      "key": "s4_7",
      "type": "square",
      "parent": "board",
      "row": 4,
      "column": 7,
      "x": 700,
      "y": 300
    },
    {
      "key": "s5_0",
      "type": "square",
      "parent": "board",
      "row": 5,
      "column": 0,
      "x": 0,
      "y": 200
    },
    {
      "key": "s5_2",
      "type": "square",
      "parent": "board",
      "row": 5,
      "column": 2,
      "x": 200,
      "y": 200
    },
    {
      "key": "s5_4",
      "type": "square",
      "parent": "board",
      "row": 5,
      "column": 4,
      "x": 400,
      "y": 200
    },
    {
      "key": "s5_6",
      "type": "square",
      "parent": "board",
      "row": 5,
      "column": 6,
      "x": 600,
      "y": 200
    },
    {
      "key": "s6_1",
      "type": "square",
      "parent": "board",
      "row": 6,
      "column": 1,
      "x": 100,
      "y": 100
    },
    {
      "key": "s6_3",
      "type": "square",
      "parent": "board",
      "row": 6,
      "column": 3,
      "x": 300,
      "y": 100
    },
    {
      "key": "s6_5",
      "type": "square",
      "parent": "board",
      "row": 6,
      "column": 5,
      "x": 500,
      "y": 100
    },
    {
      "key": "s6_7",
      "type": "square",
      "parent": "board",
      "row": 6,
      "column": 7,
      "x": 700,
      "y": 100
    },
    {
      "key": "s7_0",
      "type": "square",
      "parent": "board",
      "row": 7,
      "column": 0,
      "x": 0,
      "y": 0
    },
    {
      "key": "s7_2",
      "type": "square",
      "parent": "board",
      "row": 7,
      "column": 2,
      "x": 200,
      "y": 0
    },
    {
      "key": "s7_4",
      "type": "square",
      "parent": "board",
      "row": 7,
      "column": 4,
      "x": 400,
      "y": 0
    },
    {
      "key": "s7_6",
      "type": "square",
      "parent": "board",
      "row": 7,
      "column": 6,
      "x": 600,
      "y": 0
    },
    {
      "key": "man_0_0_1",
      "type": "man",
      "owner": 0,
      "location": "s0_1",
      "values": {
        "moved": false
      }
    },
    {
      "key": "man_0_0_3",
      "type": "man",
      "owner": 0,
      "location": "s0_3",
      "values": {
        "moved": false
      }
    },
    {
      "key": "man_0_0_5",
      "type": "man",
      "owner": 0,
      "location": "s0_5",
      "values": {
        "moved": false
      }
    },
    {
      "key": "man_0_0_7",
      "type": "man",
      "owner": 0,
      "location": "s0_7",
      "values": {
        "moved": false
      }
    },
    {
      "key": "man_0_1_0",
      "type": "man",
      "owner": 0,
      "location": "s1_0",
      "values": {
        "moved": false
      }
    },
    {
      "key": "man_0_1_2",
      "type": "man",
      "owner": 0,
      "location": "s1_2",
      "values": {
        "moved": false
      }
    },
    {
      "key": "man_0_1_4",
      "type": "man",
      "owner": 0,
      "location": "s1_4",
      "values": {
        "moved": false
      }
    },
    {
      "key": "man_0_1_6",
      "type": "man",
      "owner": 0,
      "location": "s1_6",
      "values": {
        "moved": false
      }
    },
    {
      "key": "man_0_2_1",
      "type": "man",
      "owner": 0,
      "location": "s2_1",
      "values": {
        "moved": false
      }
    },
    {
      "key": "man_0_2_3",
      "type": "man",
      "owner": 0,
      "location": "s2_3",
      "values": {
        "moved": false
      }
    },
    {
      "key": "man_0_2_5",
      "type": "man",
      "owner": 0,
      "location": "s2_5",
      "values": {
        "moved": false
      }
    },
    {
      "key": "man_0_2_7",
      "type": "man",
      "owner": 0,
      "location": "s2_7",
      "values": {
        "moved": false
      }
    },
    {
      "key": "man_1_5_0",
      "type": "man",
      "owner": 1,
      "location": "s5_0",
      "values": {
        "moved": false
      }
    },
    {
      "key": "man_1_5_2",
      "type": "man",
      "owner": 1,
      "location": "s5_2",
      "values": {
        "moved": false
      }
    },
    {
      "key": "man_1_5_4",
      "type": "man",
      "owner": 1,
      "location": "s5_4",
      "values": {
        "moved": false
      }
    },
    {
      "key": "man_1_5_6",
      "type": "man",
      "owner": 1,
      "location": "s5_6",
      "values": {
        "moved": false
      }
    },
    {
      "key": "man_1_6_1",
      "type": "man",
      "owner": 1,
      "location": "s6_1",
      "values": {
        "moved": false
      }
    },
    {
      "key": "man_1_6_3",
      "type": "man",
      "owner": 1,
      "location": "s6_3",
      "values": {
        "moved": false
      }
    },
    {
      "key": "man_1_6_5",
      "type": "man",
      "owner": 1,
      "location": "s6_5",
      "values": {
        "moved": false
      }
    },
    {
      "key": "man_1_6_7",
      "type": "man",
      "owner": 1,
      "location": "s6_7",
      "values": {
        "moved": false
      }
    },
    {
      "key": "man_1_7_0",
      "type": "man",
      "owner": 1,
      "location": "s7_0",
      "values": {
        "moved": false
      }
    },
    {
      "key": "man_1_7_2",
      "type": "man",
      "owner": 1,
      "location": "s7_2",
      "values": {
        "moved": false
      }
    },
    {
      "key": "man_1_7_4",
      "type": "man",
      "owner": 1,
      "location": "s7_4",
      "values": {
        "moved": false
      }
    },
    {
      "key": "man_1_7_6",
      "type": "man",
      "owner": 1,
      "location": "s7_6",
      "values": {
        "moved": false
      }
    },
    {
      "key": "objective_victory",
      "type": "victory",
      "parent": "root",
      "values": {
        "completed": false,
        "progress": 0
      }
    },
    {
      "key": "objective_draw",
      "type": "draw",
      "parent": "root",
      "values": {
        "completed": false,
        "progress": 0
      }
    },
    {
      "key": "objective_capture_quest",
      "type": "capture_quest",
      "parent": "root",
      "values": {
        "completed": false,
        "progress": 0
      }
    }
  ],
  "links": [],
  "fields": [
    {
      "entity": "man",
      "key": "moved",
      "type": "bool",
      "default": false
    },
    {
      "entity": "king",
      "key": "moved",
      "type": "bool",
      "default": false
    },
    {
      "entity": "victory",
      "key": "completed",
      "type": "bool",
      "default": false
    },
    {
      "entity": "victory",
      "key": "progress",
      "type": "int",
      "default": 0
    },
    {
      "entity": "draw",
      "key": "completed",
      "type": "bool",
      "default": false
    },
    {
      "entity": "draw",
      "key": "progress",
      "type": "int",
      "default": 0
    },
    {
      "entity": "capture_quest",
      "key": "completed",
      "type": "bool",
      "default": false
    },
    {
      "entity": "capture_quest",
      "key": "progress",
      "type": "int",
      "default": 0
    },
    {
      "entity": "game",
      "key": "active_seat",
      "type": "int",
      "default": 0
    },
    {
      "entity": "game",
      "key": "draw_counter",
      "type": "int",
      "default": 0
    }
  ],
  "actions": [
    {
      "key": "step",
      "entity": "man",
      "trigger": "command",
      "phase": "turn",
      "condition": {
        "op": "and",
        "args": {
          "values": [
            {
              "op": "is_active",
              "args": {
                "participant": {
                  "op": "context",
                  "ref": "actor"
                }
              }
            },
            {
              "op": "contains",
              "args": {
                "items": {
                  "op": "reachable_grid_nodes",
                  "args": {
                    "entity": {
                      "op": "context",
                      "ref": "self"
                    },
                    "directions": {
                      "op": "list",
                      "args": {
                        "values": [
                          {
                            "op": "vector",
                            "args": {
                              "row": {
                                "op": "literal",
                                "value": 1
                              },
                              "column": {
                                "op": "literal",
                                "value": -1
                              }
                            }
                          },
                          {
                            "op": "vector",
                            "args": {
                              "row": {
                                "op": "literal",
                                "value": 1
                              },
                              "column": {
                                "op": "literal",
                                "value": 1
                              }
                            }
                          }
                        ]
                      }
                    },
                    "max_steps": {
                      "op": "literal",
                      "value": 1
                    },
                    "leap": {
                      "op": "literal",
                      "value": false
                    },
                    "orientation": {
                      "op": "owner_orientation",
                      "args": {
                        "entity": {
                          "op": "context",
                          "ref": "self"
                        }
                      }
                    },
                    "target_occupancy": {
                      "op": "literal",
                      "value": "empty"
                    },
                    "state": {
                      "op": "context",
                      "ref": "observed_state"
                    }
                  }
                },
                "value": {
                  "op": "context",
                  "ref": "argument.to"
                }
              }
            },
            {
              "op": "not",
              "args": {
                "value": {
                  "op": "any_match",
                  "args": {
                    "items": {
                      "op": "participant_entities",
                      "args": {
                        "participant": {
                          "op": "context",
                          "ref": "actor"
                        }
                      }
                    },
                    "variable": {
                      "op": "literal",
                      "value": "piece"
                    },
                    "predicate": {
                      "op": "gt",
                      "args": {
                        "a": {
                          "op": "count",
                          "args": {
                            "items": {
                              "op": "traverse_paths",
                              "args": {
                                "entity": {
                                  "op": "context",
                                  "ref": "local.piece"
                                },
                                "step_generator": {
                                  "op": "jump_landing_steps",
                                  "args": {
                                    "entity": {
                                      "op": "context",
                                      "ref": "local.piece"
                                    },
                                    "directions": {
                                      "op": "list",
                                      "args": {
                                        "values": [
                                          {
                                            "op": "vector",
                                            "args": {
                                              "row": {
                                                "op": "literal",
                                                "value": 1
                                              },
                                              "column": {
                                                "op": "literal",
                                                "value": -1
                                              }
                                            }
                                          },
                                          {
                                            "op": "vector",
                                            "args": {
                                              "row": {
                                                "op": "literal",
                                                "value": 1
                                              },
                                              "column": {
                                                "op": "literal",
                                                "value": 1
                                              }
                                            }
                                          }
                                        ]
                                      }
                                    },
                                    "orientation": {
                                      "op": "owner_orientation",
                                      "args": {
                                        "entity": {
                                          "op": "context",
                                          "ref": "local.piece"
                                        }
                                      }
                                    },
                                    "flying": {
                                      "op": "literal",
                                      "value": false
                                    },
                                    "max_flight": {
                                      "op": "literal",
                                      "value": 2
                                    },
                                    "target_occupancy": {
                                      "op": "literal",
                                      "value": "empty"
                                    },
                                    "jumped_occupancy": {
                                      "op": "literal",
                                      "value": "opponent"
                                    }
                                  }
                                },
                                "max_depth": {
                                  "op": "literal",
                                  "value": 40
                                },
                                "captured_blockers": {
                                  "op": "literal",
                                  "value": false
                                },
                                "no_repeat_capture": {
                                  "op": "literal",
                                  "value": true
                                },
                                "stop_on_crowning": {
                                  "op": "literal",
                                  "value": true
                                }
                              }
                            }
                          }
                        },
                        "b": {
                          "op": "literal",
                          "value": 0
                        }
                      }
                    }
                  }
                }
              }
            }
          ]
        }
      },
      "effects": [
        {
          "op": "move_entity",
          "args": {
            "entity": {
              "op": "context",
              "ref": "self"
            },
            "destination": {
              "op": "context",
              "ref": "argument.to"
            }
          }
        },
        {
          "op": "change_entity_type",
          "when": {
            "op": "on_board_edge",
            "args": {
              "entity": {
                "op": "context",
                "ref": "self"
              },
              "edge": {
                "op": "literal",
                "value": "promotion"
              }
            }
          },
          "args": {
            "entity": {
              "op": "context",
              "ref": "self"
            },
            "to": {
              "op": "literal",
              "value": "king"
            }
          }
        },
        {
          "op": "advance_turn",
          "args": {}
        }
      ],
      "priority": 0,
      "parameters": [
        {
          "key": "to",
          "type": "entity"
        }
      ]
    },
    {
      "key": "capture",
      "entity": "man",
      "trigger": "command",
      "phase": "turn",
      "condition": {
        "op": "and",
        "args": {
          "values": [
            {
              "op": "is_active",
              "args": {
                "participant": {
                  "op": "context",
                  "ref": "actor"
                }
              }
            },
            {
              "op": "contains",
              "args": {
                "items": {
                  "op": "traverse_paths",
                  "args": {
                    "entity": {
                      "op": "context",
                      "ref": "self"
                    },
                    "step_generator": {
                      "op": "jump_landing_steps",
                      "args": {
                        "entity": {
                          "op": "context",
                          "ref": "self"
                        },
                        "directions": {
                          "op": "list",
                          "args": {
                            "values": [
                              {
                                "op": "vector",
                                "args": {
                                  "row": {
                                    "op": "literal",
                                    "value": 1
                                  },
                                  "column": {
                                    "op": "literal",
                                    "value": -1
                                  }
                                }
                              },
                              {
                                "op": "vector",
                                "args": {
                                  "row": {
                                    "op": "literal",
                                    "value": 1
                                  },
                                  "column": {
                                    "op": "literal",
                                    "value": 1
                                  }
                                }
                              }
                            ]
                          }
                        },
                        "orientation": {
                          "op": "owner_orientation",
                          "args": {
                            "entity": {
                              "op": "context",
                              "ref": "self"
                            }
                          }
                        },
                        "flying": {
                          "op": "literal",
                          "value": false
                        },
                        "max_flight": {
                          "op": "literal",
                          "value": 2
                        },
                        "target_occupancy": {
                          "op": "literal",
                          "value": "empty"
                        },
                        "jumped_occupancy": {
                          "op": "literal",
                          "value": "opponent"
                        }
                      }
                    },
                    "max_depth": {
                      "op": "literal",
                      "value": 40
                    },
                    "captured_blockers": {
                      "op": "literal",
                      "value": false
                    },
                    "no_repeat_capture": {
                      "op": "literal",
                      "value": true
                    },
                    "stop_on_crowning": {
                      "op": "literal",
                      "value": true
                    }
                  }
                },
                "value": {
                  "op": "context",
                  "ref": "argument.path"
                }
              }
            },
            {
              "op": "literal",
              "value": true
            }
          ]
        }
      },
      "effects": [
        {
          "op": "apply_path",
          "args": {
            "entity": {
              "op": "context",
              "ref": "self"
            },
            "path": {
              "op": "context",
              "ref": "argument.path"
            },
            "remove_traversed_entities": {
              "op": "literal",
              "value": true
            }
          }
        },
        {
          "op": "change_entity_type",
          "when": {
            "op": "on_board_edge",
            "args": {
              "entity": {
                "op": "context",
                "ref": "self"
              },
              "edge": {
                "op": "literal",
                "value": "promotion"
              }
            }
          },
          "args": {
            "entity": {
              "op": "context",
              "ref": "self"
            },
            "to": {
              "op": "literal",
              "value": "king"
            }
          }
        },
        {
          "op": "emit_event",
          "args": {
            "name": {
              "op": "literal",
              "value": "piece.captured"
            }
          }
        },
        {
          "op": "advance_turn",
          "args": {}
        }
      ],
      "priority": 0,
      "parameters": [
        {
          "key": "path",
          "type": "path"
        }
      ]
    },
    {
      "key": "candidates",
      "entity": "man",
      "trigger": "hook",
      "phase": "turn",
      "condition": {
        "op": "literal",
        "value": true
      },
      "effects": [
        {
          "op": "emit_candidate",
          "args": {
            "entity": {
              "op": "context",
              "ref": "self"
            },
            "path": {
              "op": "context",
              "ref": "candidate"
            }
          }
        }
      ],
      "priority": 0,
      "hook": "action.generate",
      "iterator": {
        "op": "traverse_paths",
        "args": {
          "entity": {
            "op": "context",
            "ref": "self"
          },
          "step_generator": {
            "op": "jump_landing_steps",
            "args": {
              "entity": {
                "op": "context",
                "ref": "self"
              },
              "directions": {
                "op": "list",
                "args": {
                  "values": [
                    {
                      "op": "vector",
                      "args": {
                        "row": {
                          "op": "literal",
                          "value": 1
                        },
                        "column": {
                          "op": "literal",
                          "value": -1
                        }
                      }
                    },
                    {
                      "op": "vector",
                      "args": {
                        "row": {
                          "op": "literal",
                          "value": 1
                        },
                        "column": {
                          "op": "literal",
                          "value": 1
                        }
                      }
                    }
                  ]
                }
              },
              "orientation": {
                "op": "owner_orientation",
                "args": {
                  "entity": {
                    "op": "context",
                    "ref": "self"
                  }
                }
              },
              "flying": {
                "op": "literal",
                "value": false
              },
              "max_flight": {
                "op": "literal",
                "value": 2
              },
              "target_occupancy": {
                "op": "literal",
                "value": "empty"
              },
              "jumped_occupancy": {
                "op": "literal",
                "value": "opponent"
              }
            }
          },
          "max_depth": {
            "op": "literal",
            "value": 40
          },
          "captured_blockers": {
            "op": "literal",
            "value": false
          },
          "no_repeat_capture": {
            "op": "literal",
            "value": true
          },
          "stop_on_crowning": {
            "op": "literal",
            "value": true
          }
        }
      },
      "variable": "candidate"
    },
    {
      "key": "step",
      "entity": "king",
      "trigger": "command",
      "phase": "turn",
      "condition": {
        "op": "and",
        "args": {
          "values": [
            {
              "op": "is_active",
              "args": {
                "participant": {
                  "op": "context",
                  "ref": "actor"
                }
              }
            },
            {
              "op": "contains",
              "args": {
                "items": {
                  "op": "reachable_grid_nodes",
                  "args": {
                    "entity": {
                      "op": "context",
                      "ref": "self"
                    },
                    "directions": {
                      "op": "list",
                      "args": {
                        "values": [
                          {
                            "op": "vector",
                            "args": {
                              "row": {
                                "op": "literal",
                                "value": 1
                              },
                              "column": {
                                "op": "literal",
                                "value": -1
                              }
                            }
                          },
                          {
                            "op": "vector",
                            "args": {
                              "row": {
                                "op": "literal",
                                "value": 1
                              },
                              "column": {
                                "op": "literal",
                                "value": 1
                              }
                            }
                          },
                          {
                            "op": "vector",
                            "args": {
                              "row": {
                                "op": "literal",
                                "value": -1
                              },
                              "column": {
                                "op": "literal",
                                "value": -1
                              }
                            }
                          },
                          {
                            "op": "vector",
                            "args": {
                              "row": {
                                "op": "literal",
                                "value": -1
                              },
                              "column": {
                                "op": "literal",
                                "value": 1
                              }
                            }
                          }
                        ]
                      }
                    },
                    "max_steps": {
                      "op": "literal",
                      "value": 1
                    },
                    "leap": {
                      "op": "literal",
                      "value": false
                    },
                    "orientation": {
                      "op": "owner_orientation",
                      "args": {
                        "entity": {
                          "op": "context",
                          "ref": "self"
                        }
                      }
                    },
                    "target_occupancy": {
                      "op": "literal",
                      "value": "empty"
                    },
                    "state": {
                      "op": "context",
                      "ref": "observed_state"
                    }
                  }
                },
                "value": {
                  "op": "context",
                  "ref": "argument.to"
                }
              }
            },
            {
              "op": "not",
              "args": {
                "value": {
                  "op": "any_match",
                  "args": {
                    "items": {
                      "op": "participant_entities",
                      "args": {
                        "participant": {
                          "op": "context",
                          "ref": "actor"
                        }
                      }
                    },
                    "variable": {
                      "op": "literal",
                      "value": "piece"
                    },
                    "predicate": {
                      "op": "gt",
                      "args": {
                        "a": {
                          "op": "count",
                          "args": {
                            "items": {
                              "op": "traverse_paths",
                              "args": {
                                "entity": {
                                  "op": "context",
                                  "ref": "local.piece"
                                },
                                "step_generator": {
                                  "op": "jump_landing_steps",
                                  "args": {
                                    "entity": {
                                      "op": "context",
                                      "ref": "local.piece"
                                    },
                                    "directions": {
                                      "op": "list",
                                      "args": {
                                        "values": [
                                          {
                                            "op": "vector",
                                            "args": {
                                              "row": {
                                                "op": "literal",
                                                "value": 1
                                              },
                                              "column": {
                                                "op": "literal",
                                                "value": -1
                                              }
                                            }
                                          },
                                          {
                                            "op": "vector",
                                            "args": {
                                              "row": {
                                                "op": "literal",
                                                "value": 1
                                              },
                                              "column": {
                                                "op": "literal",
                                                "value": 1
                                              }
                                            }
                                          }
                                        ]
                                      }
                                    },
                                    "orientation": {
                                      "op": "owner_orientation",
                                      "args": {
                                        "entity": {
                                          "op": "context",
                                          "ref": "local.piece"
                                        }
                                      }
                                    },
                                    "flying": {
                                      "op": "literal",
                                      "value": false
                                    },
                                    "max_flight": {
                                      "op": "literal",
                                      "value": 2
                                    },
                                    "target_occupancy": {
                                      "op": "literal",
                                      "value": "empty"
                                    },
                                    "jumped_occupancy": {
                                      "op": "literal",
                                      "value": "opponent"
                                    }
                                  }
                                },
                                "max_depth": {
                                  "op": "literal",
                                  "value": 40
                                },
                                "captured_blockers": {
                                  "op": "literal",
                                  "value": false
                                },
                                "no_repeat_capture": {
                                  "op": "literal",
                                  "value": true
                                },
                                "stop_on_crowning": {
                                  "op": "literal",
                                  "value": true
                                }
                              }
                            }
                          }
                        },
                        "b": {
                          "op": "literal",
                          "value": 0
                        }
                      }
                    }
                  }
                }
              }
            }
          ]
        }
      },
      "effects": [
        {
          "op": "move_entity",
          "args": {
            "entity": {
              "op": "context",
              "ref": "self"
            },
            "destination": {
              "op": "context",
              "ref": "argument.to"
            }
          }
        },
        {
          "op": "advance_turn",
          "args": {}
        }
      ],
      "priority": 0,
      "parameters": [
        {
          "key": "to",
          "type": "entity"
        }
      ]
    },
    {
      "key": "capture",
      "entity": "king",
      "trigger": "command",
      "phase": "turn",
      "condition": {
        "op": "and",
        "args": {
          "values": [
            {
              "op": "is_active",
              "args": {
                "participant": {
                  "op": "context",
                  "ref": "actor"
                }
              }
            },
            {
              "op": "contains",
              "args": {
                "items": {
                  "op": "traverse_paths",
                  "args": {
                    "entity": {
                      "op": "context",
                      "ref": "self"
                    },
                    "step_generator": {
                      "op": "jump_landing_steps",
                      "args": {
                        "entity": {
                          "op": "context",
                          "ref": "self"
                        },
                        "directions": {
                          "op": "list",
                          "args": {
                            "values": [
                              {
                                "op": "vector",
                                "args": {
                                  "row": {
                                    "op": "literal",
                                    "value": 1
                                  },
                                  "column": {
                                    "op": "literal",
                                    "value": -1
                                  }
                                }
                              },
                              {
                                "op": "vector",
                                "args": {
                                  "row": {
                                    "op": "literal",
                                    "value": 1
                                  },
                                  "column": {
                                    "op": "literal",
                                    "value": 1
                                  }
                                }
                              }
                            ]
                          }
                        },
                        "orientation": {
                          "op": "owner_orientation",
                          "args": {
                            "entity": {
                              "op": "context",
                              "ref": "self"
                            }
                          }
                        },
                        "flying": {
                          "op": "literal",
                          "value": false
                        },
                        "max_flight": {
                          "op": "literal",
                          "value": 2
                        },
                        "target_occupancy": {
                          "op": "literal",
                          "value": "empty"
                        },
                        "jumped_occupancy": {
                          "op": "literal",
                          "value": "opponent"
                        }
                      }
                    },
                    "max_depth": {
                      "op": "literal",
                      "value": 40
                    },
                    "captured_blockers": {
                      "op": "literal",
                      "value": false
                    },
                    "no_repeat_capture": {
                      "op": "literal",
                      "value": true
                    },
                    "stop_on_crowning": {
                      "op": "literal",
                      "value": true
                    }
                  }
                },
                "value": {
                  "op": "context",
                  "ref": "argument.path"
                }
              }
            },
            {
              "op": "literal",
              "value": true
            }
          ]
        }
      },
      "effects": [
        {
          "op": "apply_path",
          "args": {
            "entity": {
              "op": "context",
              "ref": "self"
            },
            "path": {
              "op": "context",
              "ref": "argument.path"
            },
            "remove_traversed_entities": {
              "op": "literal",
              "value": true
            }
          }
        },
        {
          "op": "emit_event",
          "args": {
            "name": {
              "op": "literal",
              "value": "piece.captured"
            }
          }
        },
        {
          "op": "advance_turn",
          "args": {}
        }
      ],
      "priority": 0,
      "parameters": [
        {
          "key": "path",
          "type": "path"
        }
      ]
    },
    {
      "key": "candidates",
      "entity": "king",
      "trigger": "hook",
      "phase": "turn",
      "condition": {
        "op": "literal",
        "value": true
      },
      "effects": [
        {
          "op": "emit_candidate",
          "args": {
            "entity": {
              "op": "context",
              "ref": "self"
            },
            "path": {
              "op": "context",
              "ref": "candidate"
            }
          }
        }
      ],
      "priority": 0,
      "hook": "action.generate",
      "iterator": {
        "op": "traverse_paths",
        "args": {
          "entity": {
            "op": "context",
            "ref": "self"
          },
          "step_generator": {
            "op": "jump_landing_steps",
            "args": {
              "entity": {
                "op": "context",
                "ref": "self"
              },
              "directions": {
                "op": "list",
                "args": {
                  "values": [
                    {
                      "op": "vector",
                      "args": {
                        "row": {
                          "op": "literal",
                          "value": 1
                        },
                        "column": {
                          "op": "literal",
                          "value": -1
                        }
                      }
                    },
                    {
                      "op": "vector",
                      "args": {
                        "row": {
                          "op": "literal",
                          "value": 1
                        },
                        "column": {
                          "op": "literal",
                          "value": 1
                        }
                      }
                    }
                  ]
                }
              },
              "orientation": {
                "op": "owner_orientation",
                "args": {
                  "entity": {
                    "op": "context",
                    "ref": "self"
                  }
                }
              },
              "flying": {
                "op": "literal",
                "value": false
              },
              "max_flight": {
                "op": "literal",
                "value": 2
              },
              "target_occupancy": {
                "op": "literal",
                "value": "empty"
              },
              "jumped_occupancy": {
                "op": "literal",
                "value": "opponent"
              }
            }
          },
          "max_depth": {
            "op": "literal",
            "value": 40
          },
          "captured_blockers": {
            "op": "literal",
            "value": false
          },
          "no_repeat_capture": {
            "op": "literal",
            "value": true
          },
          "stop_on_crowning": {
            "op": "literal",
            "value": true
          }
        }
      },
      "variable": "candidate"
    },
    {
      "key": "evaluate",
      "entity": "victory",
      "trigger": "hook",
      "phase": "*",
      "condition": {
        "op": "eq",
        "args": {
          "a": {
            "op": "available_action_count",
            "args": {
              "actor": {
                "op": "next_participant",
                "args": {
                  "participant": {
                    "op": "context",
                    "ref": "active_participant"
                  }
                }
              }
            }
          },
          "b": {
            "op": "literal",
            "value": 0
          }
        }
      },
      "effects": [
        {
          "op": "complete_objective",
          "args": {
            "entity": {
              "op": "context",
              "ref": "self"
            }
          }
        },
        {
          "op": "finish_game",
          "args": {
            "result": {
              "op": "literal",
              "value": "victory"
            }
          }
        }
      ],
      "priority": 0,
      "hook": "game.evaluate"
    },
    {
      "key": "evaluate",
      "entity": "draw",
      "trigger": "hook",
      "phase": "*",
      "condition": {
        "op": "gte",
        "args": {
          "a": {
            "op": "field",
            "args": {
              "entity": {
                "op": "context",
                "ref": "game"
              },
              "key": {
                "op": "literal",
                "value": "draw_counter"
              }
            }
          },
          "b": {
            "op": "literal",
            "value": 40
          }
        }
      },
      "effects": [
        {
          "op": "complete_objective",
          "args": {
            "entity": {
              "op": "context",
              "ref": "self"
            }
          }
        },
        {
          "op": "finish_game",
          "args": {
            "result": {
              "op": "literal",
              "value": "draw"
            }
          }
        }
      ],
      "priority": 0,
      "hook": "game.evaluate"
    },
    {
      "key": "count",
      "entity": "capture_quest",
      "trigger": "hook",
      "phase": "*",
      "condition": {
        "op": "eq",
        "args": {
          "a": {
            "op": "event_attribute",
            "args": {
              "event": {
                "op": "context",
                "ref": "event"
              },
              "attribute": {
                "op": "literal",
                "value": "kind"
              }
            }
          },
          "b": {
            "op": "literal",
            "value": "piece.captured"
          }
        }
      },
      "effects": [
        {
          "op": "increment_field",
          "args": {
            "entity": {
              "op": "context",
              "ref": "self"
            },
            "field": {
              "op": "literal",
              "value": "progress"
            },
            "amount": {
              "op": "literal",
              "value": 1
            }
          }
        }
      ],
      "priority": 0,
      "hook": "objective.evaluate"
    }
  ],
  "visuals": [
    {
      "entity": "square",
      "primitives": [
        {
          "kind": "rectangle",
          "width": 100,
          "height": 100,
          "fill": "#734f38"
        }
      ]
    },
    {
      "entity": "man",
      "primitives": [
        {
          "kind": "ellipse",
          "x": 10,
          "y": 10,
          "width": 80,
          "height": 80,
          "fill": "#ddddcc"
        }
      ]
    },
    {
      "entity": "king",
      "primitives": [
        {
          "kind": "ellipse",
          "x": 10,
          "y": 10,
          "width": 80,
          "height": 80,
          "fill": "#ddddcc"
        }
      ]
    }
  ],
  "assets": []
}
```

### international-draughts.json

```json
{
  "format": "bgwq.configuration",
  "format_version": 1,
  "definition": {
    "key": "international-draughts",
    "name": "International Draughts",
    "min_participants": 2,
    "max_participants": 2,
    "semantics_version": 1
  },
  "roles": [
    {
      "key": "seat_0",
      "name": "Player 1",
      "min": 1,
      "max": 1,
      "forward_row": 1
    },
    {
      "key": "seat_1",
      "name": "Player 2",
      "min": 1,
      "max": 1,
      "forward_row": -1
    }
  ],
  "phases": [
    {
      "key": "turn",
      "name": "Turn",
      "initial": true,
      "order": 0
    }
  ],
  "entities": [
    {
      "key": "game",
      "kind": "game",
      "name": "Game"
    },
    {
      "key": "board",
      "kind": "space",
      "name": "Board"
    },
    {
      "key": "square",
      "kind": "space",
      "name": "Square"
    },
    {
      "key": "man",
      "kind": "item",
      "name": "Man"
    },
    {
      "key": "king",
      "kind": "item",
      "name": "King"
    },
    {
      "key": "victory",
      "kind": "objective",
      "name": "Victory"
    },
    {
      "key": "draw",
      "kind": "objective",
      "name": "Draw"
    },
    {
      "key": "capture_quest",
      "kind": "objective",
      "name": "Capture Quest"
    }
  ],
  "seeds": [
    {
      "key": "root",
      "type": "game"
    },
    {
      "key": "board",
      "type": "board",
      "parent": "root"
    },
    {
      "key": "s0_1",
      "type": "square",
      "parent": "board",
      "row": 0,
      "column": 1,
      "x": 100,
      "y": 900
    },
    {
      "key": "s0_3",
      "type": "square",
      "parent": "board",
      "row": 0,
      "column": 3,
      "x": 300,
      "y": 900
    },
    {
      "key": "s0_5",
      "type": "square",
      "parent": "board",
      "row": 0,
      "column": 5,
      "x": 500,
      "y": 900
    },
    {
      "key": "s0_7",
      "type": "square",
      "parent": "board",
      "row": 0,
      "column": 7,
      "x": 700,
      "y": 900
    },
    {
      "key": "s0_9",
      "type": "square",
      "parent": "board",
      "row": 0,
      "column": 9,
      "x": 900,
      "y": 900
    },
    {
      "key": "s1_0",
      "type": "square",
      "parent": "board",
      "row": 1,
      "column": 0,
      "x": 0,
      "y": 800
    },
    {
      "key": "s1_2",
      "type": "square",
      "parent": "board",
      "row": 1,
      "column": 2,
      "x": 200,
      "y": 800
    },
    {
      "key": "s1_4",
      "type": "square",
      "parent": "board",
      "row": 1,
      "column": 4,
      "x": 400,
      "y": 800
    },
    {
      "key": "s1_6",
      "type": "square",
      "parent": "board",
      "row": 1,
      "column": 6,
      "x": 600,
      "y": 800
    },
    {
      "key": "s1_8",
      "type": "square",
      "parent": "board",
      "row": 1,
      "column": 8,
      "x": 800,
      "y": 800
    },
    {
      "key": "s2_1",
      "type": "square",
      "parent": "board",
      "row": 2,
      "column": 1,
      "x": 100,
      "y": 700
    },
    {
      "key": "s2_3",
      "type": "square",
      "parent": "board",
      "row": 2,
      "column": 3,
      "x": 300,
      "y": 700
    },
    {
      "key": "s2_5",
      "type": "square",
      "parent": "board",
      "row": 2,
      "column": 5,
      "x": 500,
      "y": 700
    },
    {
      "key": "s2_7",
      "type": "square",
      "parent": "board",
      "row": 2,
      "column": 7,
      "x": 700,
      "y": 700
    },
    {
      "key": "s2_9",
      "type": "square",
      "parent": "board",
      "row": 2,
      "column": 9,
      "x": 900,
      "y": 700
    },
    {
      "key": "s3_0",
      "type": "square",
      "parent": "board",
      "row": 3,
      "column": 0,
      "x": 0,
      "y": 600
    },
    {
      "key": "s3_2",
      "type": "square",
      "parent": "board",
      "row": 3,
      "column": 2,
      "x": 200,
      "y": 600
    },
    {
      "key": "s3_4",
      "type": "square",
      "parent": "board",
      "row": 3,
      "column": 4,
      "x": 400,
      "y": 600
    },
    {
      "key": "s3_6",
      "type": "square",
      "parent": "board",
      "row": 3,
      "column": 6,
      "x": 600,
      "y": 600
    },
    {
      "key": "s3_8",
      "type": "square",
      "parent": "board",
      "row": 3,
      "column": 8,
      "x": 800,
      "y": 600
    },
    {
      "key": "s4_1",
      "type": "square",
      "parent": "board",
      "row": 4,
      "column": 1,
      "x": 100,
      "y": 500
    },
    {
      "key": "s4_3",
      "type": "square",
      "parent": "board",
      "row": 4,
      "column": 3,
      "x": 300,
      "y": 500
    },
    {
      "key": "s4_5",
      "type": "square",
      "parent": "board",
      "row": 4,
      "column": 5,
      "x": 500,
      "y": 500
    },
    {
      "key": "s4_7",
      "type": "square",
      "parent": "board",
      "row": 4,
      "column": 7,
      "x": 700,
      "y": 500
    },
    {
      "key": "s4_9",
      "type": "square",
      "parent": "board",
      "row": 4,
      "column": 9,
      "x": 900,
      "y": 500
    },
    {
      "key": "s5_0",
      "type": "square",
      "parent": "board",
      "row": 5,
      "column": 0,
      "x": 0,
      "y": 400
    },
    {
      "key": "s5_2",
      "type": "square",
      "parent": "board",
      "row": 5,
      "column": 2,
      "x": 200,
      "y": 400
    },
    {
      "key": "s5_4",
      "type": "square",
      "parent": "board",
      "row": 5,
      "column": 4,
      "x": 400,
      "y": 400
    },
    {
      "key": "s5_6",
      "type": "square",
      "parent": "board",
      "row": 5,
      "column": 6,
      "x": 600,
      "y": 400
    },
    {
      "key": "s5_8",
      "type": "square",
      "parent": "board",
      "row": 5,
      "column": 8,
      "x": 800,
      "y": 400
    },
    {
      "key": "s6_1",
      "type": "square",
      "parent": "board",
      "row": 6,
      "column": 1,
      "x": 100,
      "y": 300
    },
    {
      "key": "s6_3",
      "type": "square",
      "parent": "board",
      "row": 6,
      "column": 3,
      "x": 300,
      "y": 300
    },
    {
      "key": "s6_5",
      "type": "square",
      "parent": "board",
      "row": 6,
      "column": 5,
      "x": 500,
      "y": 300
    },
    {
      "key": "s6_7",
      "type": "square",
      "parent": "board",
      "row": 6,
      "column": 7,
      "x": 700,
      "y": 300
    },
    {
      "key": "s6_9",
      "type": "square",
      "parent": "board",
      "row": 6,
      "column": 9,
      "x": 900,
      "y": 300
    },
    {
      "key": "s7_0",
      "type": "square",
      "parent": "board",
      "row": 7,
      "column": 0,
      "x": 0,
      "y": 200
    },
    {
      "key": "s7_2",
      "type": "square",
      "parent": "board",
      "row": 7,
      "column": 2,
      "x": 200,
      "y": 200
    },
    {
      "key": "s7_4",
      "type": "square",
      "parent": "board",
      "row": 7,
      "column": 4,
      "x": 400,
      "y": 200
    },
    {
      "key": "s7_6",
      "type": "square",
      "parent": "board",
      "row": 7,
      "column": 6,
      "x": 600,
      "y": 200
    },
    {
      "key": "s7_8",
      "type": "square",
      "parent": "board",
      "row": 7,
      "column": 8,
      "x": 800,
      "y": 200
    },
    {
      "key": "s8_1",
      "type": "square",
      "parent": "board",
      "row": 8,
      "column": 1,
      "x": 100,
      "y": 100
    },
    {
      "key": "s8_3",
      "type": "square",
      "parent": "board",
      "row": 8,
      "column": 3,
      "x": 300,
      "y": 100
    },
    {
      "key": "s8_5",
      "type": "square",
      "parent": "board",
      "row": 8,
      "column": 5,
      "x": 500,
      "y": 100
    },
    {
      "key": "s8_7",
      "type": "square",
      "parent": "board",
      "row": 8,
      "column": 7,
      "x": 700,
      "y": 100
    },
    {
      "key": "s8_9",
      "type": "square",
      "parent": "board",
      "row": 8,
      "column": 9,
      "x": 900,
      "y": 100
    },
    {
      "key": "s9_0",
      "type": "square",
      "parent": "board",
      "row": 9,
      "column": 0,
      "x": 0,
      "y": 0
    },
    {
      "key": "s9_2",
      "type": "square",
      "parent": "board",
      "row": 9,
      "column": 2,
      "x": 200,
      "y": 0
    },
    {
      "key": "s9_4",
      "type": "square",
      "parent": "board",
      "row": 9,
      "column": 4,
      "x": 400,
      "y": 0
    },
    {
      "key": "s9_6",
      "type": "square",
      "parent": "board",
      "row": 9,
      "column": 6,
      "x": 600,
      "y": 0
    },
    {
      "key": "s9_8",
      "type": "square",
      "parent": "board",
      "row": 9,
      "column": 8,
      "x": 800,
      "y": 0
    },
    {
      "key": "man_0_0_1",
      "type": "man",
      "owner": 0,
      "location": "s0_1",
      "values": {
        "moved": false
      }
    },
    {
      "key": "man_0_0_3",
      "type": "man",
      "owner": 0,
      "location": "s0_3",
      "values": {
        "moved": false
      }
    },
    {
      "key": "man_0_0_5",
      "type": "man",
      "owner": 0,
      "location": "s0_5",
      "values": {
        "moved": false
      }
    },
    {
      "key": "man_0_0_7",
      "type": "man",
      "owner": 0,
      "location": "s0_7",
      "values": {
        "moved": false
      }
    },
    {
      "key": "man_0_0_9",
      "type": "man",
      "owner": 0,
      "location": "s0_9",
      "values": {
        "moved": false
      }
    },
    {
      "key": "man_0_1_0",
      "type": "man",
      "owner": 0,
      "location": "s1_0",
      "values": {
        "moved": false
      }
    },
    {
      "key": "man_0_1_2",
      "type": "man",
      "owner": 0,
      "location": "s1_2",
      "values": {
        "moved": false
      }
    },
    {
      "key": "man_0_1_4",
      "type": "man",
      "owner": 0,
      "location": "s1_4",
      "values": {
        "moved": false
      }
    },
    {
      "key": "man_0_1_6",
      "type": "man",
      "owner": 0,
      "location": "s1_6",
      "values": {
        "moved": false
      }
    },
    {
      "key": "man_0_1_8",
      "type": "man",
      "owner": 0,
      "location": "s1_8",
      "values": {
        "moved": false
      }
    },
    {
      "key": "man_0_2_1",
      "type": "man",
      "owner": 0,
      "location": "s2_1",
      "values": {
        "moved": false
      }
    },
    {
      "key": "man_0_2_3",
      "type": "man",
      "owner": 0,
      "location": "s2_3",
      "values": {
        "moved": false
      }
    },
    {
      "key": "man_0_2_5",
      "type": "man",
      "owner": 0,
      "location": "s2_5",
      "values": {
        "moved": false
      }
    },
    {
      "key": "man_0_2_7",
      "type": "man",
      "owner": 0,
      "location": "s2_7",
      "values": {
        "moved": false
      }
    },
    {
      "key": "man_0_2_9",
      "type": "man",
      "owner": 0,
      "location": "s2_9",
      "values": {
        "moved": false
      }
    },
    {
      "key": "man_0_3_0",
      "type": "man",
      "owner": 0,
      "location": "s3_0",
      "values": {
        "moved": false
      }
    },
    {
      "key": "man_0_3_2",
      "type": "man",
      "owner": 0,
      "location": "s3_2",
      "values": {
        "moved": false
      }
    },
    {
      "key": "man_0_3_4",
      "type": "man",
      "owner": 0,
      "location": "s3_4",
      "values": {
        "moved": false
      }
    },
    {
      "key": "man_0_3_6",
      "type": "man",
      "owner": 0,
      "location": "s3_6",
      "values": {
        "moved": false
      }
    },
    {
      "key": "man_0_3_8",
      "type": "man",
      "owner": 0,
      "location": "s3_8",
      "values": {
        "moved": false
      }
    },
    {
      "key": "man_1_6_1",
      "type": "man",
      "owner": 1,
      "location": "s6_1",
      "values": {
        "moved": false
      }
    },
    {
      "key": "man_1_6_3",
      "type": "man",
      "owner": 1,
      "location": "s6_3",
      "values": {
        "moved": false
      }
    },
    {
      "key": "man_1_6_5",
      "type": "man",
      "owner": 1,
      "location": "s6_5",
      "values": {
        "moved": false
      }
    },
    {
      "key": "man_1_6_7",
      "type": "man",
      "owner": 1,
      "location": "s6_7",
      "values": {
        "moved": false
      }
    },
    {
      "key": "man_1_6_9",
      "type": "man",
      "owner": 1,
      "location": "s6_9",
      "values": {
        "moved": false
      }
    },
    {
      "key": "man_1_7_0",
      "type": "man",
      "owner": 1,
      "location": "s7_0",
      "values": {
        "moved": false
      }
    },
    {
      "key": "man_1_7_2",
      "type": "man",
      "owner": 1,
      "location": "s7_2",
      "values": {
        "moved": false
      }
    },
    {
      "key": "man_1_7_4",
      "type": "man",
      "owner": 1,
      "location": "s7_4",
      "values": {
        "moved": false
      }
    },
    {
      "key": "man_1_7_6",
      "type": "man",
      "owner": 1,
      "location": "s7_6",
      "values": {
        "moved": false
      }
    },
    {
      "key": "man_1_7_8",
      "type": "man",
      "owner": 1,
      "location": "s7_8",
      "values": {
        "moved": false
      }
    },
    {
      "key": "man_1_8_1",
      "type": "man",
      "owner": 1,
      "location": "s8_1",
      "values": {
        "moved": false
      }
    },
    {
      "key": "man_1_8_3",
      "type": "man",
      "owner": 1,
      "location": "s8_3",
      "values": {
        "moved": false
      }
    },
    {
      "key": "man_1_8_5",
      "type": "man",
      "owner": 1,
      "location": "s8_5",
      "values": {
        "moved": false
      }
    },
    {
      "key": "man_1_8_7",
      "type": "man",
      "owner": 1,
      "location": "s8_7",
      "values": {
        "moved": false
      }
    },
    {
      "key": "man_1_8_9",
      "type": "man",
      "owner": 1,
      "location": "s8_9",
      "values": {
        "moved": false
      }
    },
    {
      "key": "man_1_9_0",
      "type": "man",
      "owner": 1,
      "location": "s9_0",
      "values": {
        "moved": false
      }
    },
    {
      "key": "man_1_9_2",
      "type": "man",
      "owner": 1,
      "location": "s9_2",
      "values": {
        "moved": false
      }
    },
    {
      "key": "man_1_9_4",
      "type": "man",
      "owner": 1,
      "location": "s9_4",
      "values": {
        "moved": false
      }
    },
    {
      "key": "man_1_9_6",
      "type": "man",
      "owner": 1,
      "location": "s9_6",
      "values": {
        "moved": false
      }
    },
    {
      "key": "man_1_9_8",
      "type": "man",
      "owner": 1,
      "location": "s9_8",
      "values": {
        "moved": false
      }
    },
    {
      "key": "objective_victory",
      "type": "victory",
      "parent": "root",
      "values": {
        "completed": false,
        "progress": 0
      }
    },
    {
      "key": "objective_draw",
      "type": "draw",
      "parent": "root",
      "values": {
        "completed": false,
        "progress": 0
      }
    },
    {
      "key": "objective_capture_quest",
      "type": "capture_quest",
      "parent": "root",
      "values": {
        "completed": false,
        "progress": 0
      }
    }
  ],
  "links": [],
  "fields": [
    {
      "entity": "man",
      "key": "moved",
      "type": "bool",
      "default": false
    },
    {
      "entity": "king",
      "key": "moved",
      "type": "bool",
      "default": false
    },
    {
      "entity": "victory",
      "key": "completed",
      "type": "bool",
      "default": false
    },
    {
      "entity": "victory",
      "key": "progress",
      "type": "int",
      "default": 0
    },
    {
      "entity": "draw",
      "key": "completed",
      "type": "bool",
      "default": false
    },
    {
      "entity": "draw",
      "key": "progress",
      "type": "int",
      "default": 0
    },
    {
      "entity": "capture_quest",
      "key": "completed",
      "type": "bool",
      "default": false
    },
    {
      "entity": "capture_quest",
      "key": "progress",
      "type": "int",
      "default": 0
    },
    {
      "entity": "game",
      "key": "active_seat",
      "type": "int",
      "default": 0
    },
    {
      "entity": "game",
      "key": "draw_counter",
      "type": "int",
      "default": 0
    }
  ],
  "actions": [
    {
      "key": "step",
      "entity": "man",
      "trigger": "command",
      "phase": "turn",
      "condition": {
        "op": "and",
        "args": {
          "values": [
            {
              "op": "is_active",
              "args": {
                "participant": {
                  "op": "context",
                  "ref": "actor"
                }
              }
            },
            {
              "op": "contains",
              "args": {
                "items": {
                  "op": "reachable_grid_nodes",
                  "args": {
                    "entity": {
                      "op": "context",
                      "ref": "self"
                    },
                    "directions": {
                      "op": "list",
                      "args": {
                        "values": [
                          {
                            "op": "vector",
                            "args": {
                              "row": {
                                "op": "literal",
                                "value": 1
                              },
                              "column": {
                                "op": "literal",
                                "value": -1
                              }
                            }
                          },
                          {
                            "op": "vector",
                            "args": {
                              "row": {
                                "op": "literal",
                                "value": 1
                              },
                              "column": {
                                "op": "literal",
                                "value": 1
                              }
                            }
                          }
                        ]
                      }
                    },
                    "max_steps": {
                      "op": "literal",
                      "value": 1
                    },
                    "leap": {
                      "op": "literal",
                      "value": false
                    },
                    "orientation": {
                      "op": "owner_orientation",
                      "args": {
                        "entity": {
                          "op": "context",
                          "ref": "self"
                        }
                      }
                    },
                    "target_occupancy": {
                      "op": "literal",
                      "value": "empty"
                    },
                    "state": {
                      "op": "context",
                      "ref": "observed_state"
                    }
                  }
                },
                "value": {
                  "op": "context",
                  "ref": "argument.to"
                }
              }
            },
            {
              "op": "not",
              "args": {
                "value": {
                  "op": "any_match",
                  "args": {
                    "items": {
                      "op": "participant_entities",
                      "args": {
                        "participant": {
                          "op": "context",
                          "ref": "actor"
                        }
                      }
                    },
                    "variable": {
                      "op": "literal",
                      "value": "piece"
                    },
                    "predicate": {
                      "op": "gt",
                      "args": {
                        "a": {
                          "op": "count",
                          "args": {
                            "items": {
                              "op": "traverse_paths",
                              "args": {
                                "entity": {
                                  "op": "context",
                                  "ref": "local.piece"
                                },
                                "step_generator": {
                                  "op": "jump_landing_steps",
                                  "args": {
                                    "entity": {
                                      "op": "context",
                                      "ref": "local.piece"
                                    },
                                    "directions": {
                                      "op": "list",
                                      "args": {
                                        "values": [
                                          {
                                            "op": "vector",
                                            "args": {
                                              "row": {
                                                "op": "literal",
                                                "value": 1
                                              },
                                              "column": {
                                                "op": "literal",
                                                "value": -1
                                              }
                                            }
                                          },
                                          {
                                            "op": "vector",
                                            "args": {
                                              "row": {
                                                "op": "literal",
                                                "value": 1
                                              },
                                              "column": {
                                                "op": "literal",
                                                "value": 1
                                              }
                                            }
                                          },
                                          {
                                            "op": "vector",
                                            "args": {
                                              "row": {
                                                "op": "literal",
                                                "value": -1
                                              },
                                              "column": {
                                                "op": "literal",
                                                "value": -1
                                              }
                                            }
                                          },
                                          {
                                            "op": "vector",
                                            "args": {
                                              "row": {
                                                "op": "literal",
                                                "value": -1
                                              },
                                              "column": {
                                                "op": "literal",
                                                "value": 1
                                              }
                                            }
                                          }
                                        ]
                                      }
                                    },
                                    "orientation": {
                                      "op": "owner_orientation",
                                      "args": {
                                        "entity": {
                                          "op": "context",
                                          "ref": "local.piece"
                                        }
                                      }
                                    },
                                    "flying": {
                                      "op": "literal",
                                      "value": true
                                    },
                                    "max_flight": {
                                      "op": "literal",
                                      "value": 9
                                    },
                                    "target_occupancy": {
                                      "op": "literal",
                                      "value": "empty"
                                    },
                                    "jumped_occupancy": {
                                      "op": "literal",
                                      "value": "opponent"
                                    }
                                  }
                                },
                                "max_depth": {
                                  "op": "literal",
                                  "value": 40
                                },
                                "captured_blockers": {
                                  "op": "literal",
                                  "value": true
                                },
                                "no_repeat_capture": {
                                  "op": "literal",
                                  "value": true
                                },
                                "stop_on_crowning": {
                                  "op": "literal",
                                  "value": false
                                }
                              }
                            }
                          }
                        },
                        "b": {
                          "op": "literal",
                          "value": 0
                        }
                      }
                    }
                  }
                }
              }
            }
          ]
        }
      },
      "effects": [
        {
          "op": "move_entity",
          "args": {
            "entity": {
              "op": "context",
              "ref": "self"
            },
            "destination": {
              "op": "context",
              "ref": "argument.to"
            }
          }
        },
        {
          "op": "change_entity_type",
          "when": {
            "op": "on_board_edge",
            "args": {
              "entity": {
                "op": "context",
                "ref": "self"
              },
              "edge": {
                "op": "literal",
                "value": "promotion"
              }
            }
          },
          "args": {
            "entity": {
              "op": "context",
              "ref": "self"
            },
            "to": {
              "op": "literal",
              "value": "king"
            }
          }
        },
        {
          "op": "advance_turn",
          "args": {}
        }
      ],
      "priority": 0,
      "parameters": [
        {
          "key": "to",
          "type": "entity"
        }
      ]
    },
    {
      "key": "capture",
      "entity": "man",
      "trigger": "command",
      "phase": "turn",
      "condition": {
        "op": "and",
        "args": {
          "values": [
            {
              "op": "is_active",
              "args": {
                "participant": {
                  "op": "context",
                  "ref": "actor"
                }
              }
            },
            {
              "op": "contains",
              "args": {
                "items": {
                  "op": "traverse_paths",
                  "args": {
                    "entity": {
                      "op": "context",
                      "ref": "self"
                    },
                    "step_generator": {
                      "op": "jump_landing_steps",
                      "args": {
                        "entity": {
                          "op": "context",
                          "ref": "self"
                        },
                        "directions": {
                          "op": "list",
                          "args": {
                            "values": [
                              {
                                "op": "vector",
                                "args": {
                                  "row": {
                                    "op": "literal",
                                    "value": 1
                                  },
                                  "column": {
                                    "op": "literal",
                                    "value": -1
                                  }
                                }
                              },
                              {
                                "op": "vector",
                                "args": {
                                  "row": {
                                    "op": "literal",
                                    "value": 1
                                  },
                                  "column": {
                                    "op": "literal",
                                    "value": 1
                                  }
                                }
                              },
                              {
                                "op": "vector",
                                "args": {
                                  "row": {
                                    "op": "literal",
                                    "value": -1
                                  },
                                  "column": {
                                    "op": "literal",
                                    "value": -1
                                  }
                                }
                              },
                              {
                                "op": "vector",
                                "args": {
                                  "row": {
                                    "op": "literal",
                                    "value": -1
                                  },
                                  "column": {
                                    "op": "literal",
                                    "value": 1
                                  }
                                }
                              }
                            ]
                          }
                        },
                        "orientation": {
                          "op": "owner_orientation",
                          "args": {
                            "entity": {
                              "op": "context",
                              "ref": "self"
                            }
                          }
                        },
                        "flying": {
                          "op": "literal",
                          "value": true
                        },
                        "max_flight": {
                          "op": "literal",
                          "value": 9
                        },
                        "target_occupancy": {
                          "op": "literal",
                          "value": "empty"
                        },
                        "jumped_occupancy": {
                          "op": "literal",
                          "value": "opponent"
                        }
                      }
                    },
                    "max_depth": {
                      "op": "literal",
                      "value": 40
                    },
                    "captured_blockers": {
                      "op": "literal",
                      "value": true
                    },
                    "no_repeat_capture": {
                      "op": "literal",
                      "value": true
                    },
                    "stop_on_crowning": {
                      "op": "literal",
                      "value": false
                    }
                  }
                },
                "value": {
                  "op": "context",
                  "ref": "argument.path"
                }
              }
            },
            {
              "op": "eq",
              "args": {
                "a": {
                  "op": "count",
                  "args": {
                    "items": {
                      "op": "path_captured_entities",
                      "args": {
                        "path": {
                          "op": "context",
                          "ref": "argument.path"
                        }
                      }
                    }
                  }
                },
                "b": {
                  "op": "maximum",
                  "args": {
                    "values": {
                      "op": "map",
                      "args": {
                        "items": {
                          "op": "traverse_paths",
                          "args": {
                            "entity": {
                              "op": "context",
                              "ref": "self"
                            },
                            "step_generator": {
                              "op": "jump_landing_steps",
                              "args": {
                                "entity": {
                                  "op": "context",
                                  "ref": "self"
                                },
                                "directions": {
                                  "op": "list",
                                  "args": {
                                    "values": [
                                      {
                                        "op": "vector",
                                        "args": {
                                          "row": {
                                            "op": "literal",
                                            "value": 1
                                          },
                                          "column": {
                                            "op": "literal",
                                            "value": -1
                                          }
                                        }
                                      },
                                      {
                                        "op": "vector",
                                        "args": {
                                          "row": {
                                            "op": "literal",
                                            "value": 1
                                          },
                                          "column": {
                                            "op": "literal",
                                            "value": 1
                                          }
                                        }
                                      },
                                      {
                                        "op": "vector",
                                        "args": {
                                          "row": {
                                            "op": "literal",
                                            "value": -1
                                          },
                                          "column": {
                                            "op": "literal",
                                            "value": -1
                                          }
                                        }
                                      },
                                      {
                                        "op": "vector",
                                        "args": {
                                          "row": {
                                            "op": "literal",
                                            "value": -1
                                          },
                                          "column": {
                                            "op": "literal",
                                            "value": 1
                                          }
                                        }
                                      }
                                    ]
                                  }
                                },
                                "orientation": {
                                  "op": "owner_orientation",
                                  "args": {
                                    "entity": {
                                      "op": "context",
                                      "ref": "self"
                                    }
                                  }
                                },
                                "flying": {
                                  "op": "literal",
                                  "value": true
                                },
                                "max_flight": {
                                  "op": "literal",
                                  "value": 9
                                },
                                "target_occupancy": {
                                  "op": "literal",
                                  "value": "empty"
                                },
                                "jumped_occupancy": {
                                  "op": "literal",
                                  "value": "opponent"
                                }
                              }
                            },
                            "max_depth": {
                              "op": "literal",
                              "value": 40
                            },
                            "captured_blockers": {
                              "op": "literal",
                              "value": true
                            },
                            "no_repeat_capture": {
                              "op": "literal",
                              "value": true
                            },
                            "stop_on_crowning": {
                              "op": "literal",
                              "value": false
                            }
                          }
                        },
                        "variable": {
                          "op": "literal",
                          "value": "p"
                        },
                        "expression": {
                          "op": "count",
                          "args": {
                            "items": {
                              "op": "path_captured_entities",
                              "args": {
                                "path": {
                                  "op": "context",
                                  "ref": "local.p"
                                }
                              }
                            }
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
          ]
        }
      },
      "effects": [
        {
          "op": "apply_path",
          "args": {
            "entity": {
              "op": "context",
              "ref": "self"
            },
            "path": {
              "op": "context",
              "ref": "argument.path"
            },
            "remove_traversed_entities": {
              "op": "literal",
              "value": true
            }
          }
        },
        {
          "op": "change_entity_type",
          "when": {
            "op": "on_board_edge",
            "args": {
              "entity": {
                "op": "context",
                "ref": "self"
              },
              "edge": {
                "op": "literal",
                "value": "promotion"
              }
            }
          },
          "args": {
            "entity": {
              "op": "context",
              "ref": "self"
            },
            "to": {
              "op": "literal",
              "value": "king"
            }
          }
        },
        {
          "op": "emit_event",
          "args": {
            "name": {
              "op": "literal",
              "value": "piece.captured"
            }
          }
        },
        {
          "op": "advance_turn",
          "args": {}
        }
      ],
      "priority": 0,
      "parameters": [
        {
          "key": "path",
          "type": "path"
        }
      ]
    },
    {
      "key": "candidates",
      "entity": "man",
      "trigger": "hook",
      "phase": "turn",
      "condition": {
        "op": "literal",
        "value": true
      },
      "effects": [
        {
          "op": "emit_candidate",
          "args": {
            "entity": {
              "op": "context",
              "ref": "self"
            },
            "path": {
              "op": "context",
              "ref": "candidate"
            }
          }
        }
      ],
      "priority": 0,
      "hook": "action.generate",
      "iterator": {
        "op": "traverse_paths",
        "args": {
          "entity": {
            "op": "context",
            "ref": "self"
          },
          "step_generator": {
            "op": "jump_landing_steps",
            "args": {
              "entity": {
                "op": "context",
                "ref": "self"
              },
              "directions": {
                "op": "list",
                "args": {
                  "values": [
                    {
                      "op": "vector",
                      "args": {
                        "row": {
                          "op": "literal",
                          "value": 1
                        },
                        "column": {
                          "op": "literal",
                          "value": -1
                        }
                      }
                    },
                    {
                      "op": "vector",
                      "args": {
                        "row": {
                          "op": "literal",
                          "value": 1
                        },
                        "column": {
                          "op": "literal",
                          "value": 1
                        }
                      }
                    },
                    {
                      "op": "vector",
                      "args": {
                        "row": {
                          "op": "literal",
                          "value": -1
                        },
                        "column": {
                          "op": "literal",
                          "value": -1
                        }
                      }
                    },
                    {
                      "op": "vector",
                      "args": {
                        "row": {
                          "op": "literal",
                          "value": -1
                        },
                        "column": {
                          "op": "literal",
                          "value": 1
                        }
                      }
                    }
                  ]
                }
              },
              "orientation": {
                "op": "owner_orientation",
                "args": {
                  "entity": {
                    "op": "context",
                    "ref": "self"
                  }
                }
              },
              "flying": {
                "op": "literal",
                "value": true
              },
              "max_flight": {
                "op": "literal",
                "value": 9
              },
              "target_occupancy": {
                "op": "literal",
                "value": "empty"
              },
              "jumped_occupancy": {
                "op": "literal",
                "value": "opponent"
              }
            }
          },
          "max_depth": {
            "op": "literal",
            "value": 40
          },
          "captured_blockers": {
            "op": "literal",
            "value": true
          },
          "no_repeat_capture": {
            "op": "literal",
            "value": true
          },
          "stop_on_crowning": {
            "op": "literal",
            "value": false
          }
        }
      },
      "variable": "candidate"
    },
    {
      "key": "step",
      "entity": "king",
      "trigger": "command",
      "phase": "turn",
      "condition": {
        "op": "and",
        "args": {
          "values": [
            {
              "op": "is_active",
              "args": {
                "participant": {
                  "op": "context",
                  "ref": "actor"
                }
              }
            },
            {
              "op": "contains",
              "args": {
                "items": {
                  "op": "reachable_grid_nodes",
                  "args": {
                    "entity": {
                      "op": "context",
                      "ref": "self"
                    },
                    "directions": {
                      "op": "list",
                      "args": {
                        "values": [
                          {
                            "op": "vector",
                            "args": {
                              "row": {
                                "op": "literal",
                                "value": 1
                              },
                              "column": {
                                "op": "literal",
                                "value": -1
                              }
                            }
                          },
                          {
                            "op": "vector",
                            "args": {
                              "row": {
                                "op": "literal",
                                "value": 1
                              },
                              "column": {
                                "op": "literal",
                                "value": 1
                              }
                            }
                          },
                          {
                            "op": "vector",
                            "args": {
                              "row": {
                                "op": "literal",
                                "value": -1
                              },
                              "column": {
                                "op": "literal",
                                "value": -1
                              }
                            }
                          },
                          {
                            "op": "vector",
                            "args": {
                              "row": {
                                "op": "literal",
                                "value": -1
                              },
                              "column": {
                                "op": "literal",
                                "value": 1
                              }
                            }
                          }
                        ]
                      }
                    },
                    "max_steps": {
                      "op": "literal",
                      "value": 9
                    },
                    "leap": {
                      "op": "literal",
                      "value": false
                    },
                    "orientation": {
                      "op": "owner_orientation",
                      "args": {
                        "entity": {
                          "op": "context",
                          "ref": "self"
                        }
                      }
                    },
                    "target_occupancy": {
                      "op": "literal",
                      "value": "empty"
                    },
                    "state": {
                      "op": "context",
                      "ref": "observed_state"
                    }
                  }
                },
                "value": {
                  "op": "context",
                  "ref": "argument.to"
                }
              }
            },
            {
              "op": "not",
              "args": {
                "value": {
                  "op": "any_match",
                  "args": {
                    "items": {
                      "op": "participant_entities",
                      "args": {
                        "participant": {
                          "op": "context",
                          "ref": "actor"
                        }
                      }
                    },
                    "variable": {
                      "op": "literal",
                      "value": "piece"
                    },
                    "predicate": {
                      "op": "gt",
                      "args": {
                        "a": {
                          "op": "count",
                          "args": {
                            "items": {
                              "op": "traverse_paths",
                              "args": {
                                "entity": {
                                  "op": "context",
                                  "ref": "local.piece"
                                },
                                "step_generator": {
                                  "op": "jump_landing_steps",
                                  "args": {
                                    "entity": {
                                      "op": "context",
                                      "ref": "local.piece"
                                    },
                                    "directions": {
                                      "op": "list",
                                      "args": {
                                        "values": [
                                          {
                                            "op": "vector",
                                            "args": {
                                              "row": {
                                                "op": "literal",
                                                "value": 1
                                              },
                                              "column": {
                                                "op": "literal",
                                                "value": -1
                                              }
                                            }
                                          },
                                          {
                                            "op": "vector",
                                            "args": {
                                              "row": {
                                                "op": "literal",
                                                "value": 1
                                              },
                                              "column": {
                                                "op": "literal",
                                                "value": 1
                                              }
                                            }
                                          },
                                          {
                                            "op": "vector",
                                            "args": {
                                              "row": {
                                                "op": "literal",
                                                "value": -1
                                              },
                                              "column": {
                                                "op": "literal",
                                                "value": -1
                                              }
                                            }
                                          },
                                          {
                                            "op": "vector",
                                            "args": {
                                              "row": {
                                                "op": "literal",
                                                "value": -1
                                              },
                                              "column": {
                                                "op": "literal",
                                                "value": 1
                                              }
                                            }
                                          }
                                        ]
                                      }
                                    },
                                    "orientation": {
                                      "op": "owner_orientation",
                                      "args": {
                                        "entity": {
                                          "op": "context",
                                          "ref": "local.piece"
                                        }
                                      }
                                    },
                                    "flying": {
                                      "op": "literal",
                                      "value": true
                                    },
                                    "max_flight": {
                                      "op": "literal",
                                      "value": 9
                                    },
                                    "target_occupancy": {
                                      "op": "literal",
                                      "value": "empty"
                                    },
                                    "jumped_occupancy": {
                                      "op": "literal",
                                      "value": "opponent"
                                    }
                                  }
                                },
                                "max_depth": {
                                  "op": "literal",
                                  "value": 40
                                },
                                "captured_blockers": {
                                  "op": "literal",
                                  "value": true
                                },
                                "no_repeat_capture": {
                                  "op": "literal",
                                  "value": true
                                },
                                "stop_on_crowning": {
                                  "op": "literal",
                                  "value": false
                                }
                              }
                            }
                          }
                        },
                        "b": {
                          "op": "literal",
                          "value": 0
                        }
                      }
                    }
                  }
                }
              }
            }
          ]
        }
      },
      "effects": [
        {
          "op": "move_entity",
          "args": {
            "entity": {
              "op": "context",
              "ref": "self"
            },
            "destination": {
              "op": "context",
              "ref": "argument.to"
            }
          }
        },
        {
          "op": "advance_turn",
          "args": {}
        }
      ],
      "priority": 0,
      "parameters": [
        {
          "key": "to",
          "type": "entity"
        }
      ]
    },
    {
      "key": "capture",
      "entity": "king",
      "trigger": "command",
      "phase": "turn",
      "condition": {
        "op": "and",
        "args": {
          "values": [
            {
              "op": "is_active",
              "args": {
                "participant": {
                  "op": "context",
                  "ref": "actor"
                }
              }
            },
            {
              "op": "contains",
              "args": {
                "items": {
                  "op": "traverse_paths",
                  "args": {
                    "entity": {
                      "op": "context",
                      "ref": "self"
                    },
                    "step_generator": {
                      "op": "jump_landing_steps",
                      "args": {
                        "entity": {
                          "op": "context",
                          "ref": "self"
                        },
                        "directions": {
                          "op": "list",
                          "args": {
                            "values": [
                              {
                                "op": "vector",
                                "args": {
                                  "row": {
                                    "op": "literal",
                                    "value": 1
                                  },
                                  "column": {
                                    "op": "literal",
                                    "value": -1
                                  }
                                }
                              },
                              {
                                "op": "vector",
                                "args": {
                                  "row": {
                                    "op": "literal",
                                    "value": 1
                                  },
                                  "column": {
                                    "op": "literal",
                                    "value": 1
                                  }
                                }
                              },
                              {
                                "op": "vector",
                                "args": {
                                  "row": {
                                    "op": "literal",
                                    "value": -1
                                  },
                                  "column": {
                                    "op": "literal",
                                    "value": -1
                                  }
                                }
                              },
                              {
                                "op": "vector",
                                "args": {
                                  "row": {
                                    "op": "literal",
                                    "value": -1
                                  },
                                  "column": {
                                    "op": "literal",
                                    "value": 1
                                  }
                                }
                              }
                            ]
                          }
                        },
                        "orientation": {
                          "op": "owner_orientation",
                          "args": {
                            "entity": {
                              "op": "context",
                              "ref": "self"
                            }
                          }
                        },
                        "flying": {
                          "op": "literal",
                          "value": true
                        },
                        "max_flight": {
                          "op": "literal",
                          "value": 9
                        },
                        "target_occupancy": {
                          "op": "literal",
                          "value": "empty"
                        },
                        "jumped_occupancy": {
                          "op": "literal",
                          "value": "opponent"
                        }
                      }
                    },
                    "max_depth": {
                      "op": "literal",
                      "value": 40
                    },
                    "captured_blockers": {
                      "op": "literal",
                      "value": true
                    },
                    "no_repeat_capture": {
                      "op": "literal",
                      "value": true
                    },
                    "stop_on_crowning": {
                      "op": "literal",
                      "value": false
                    }
                  }
                },
                "value": {
                  "op": "context",
                  "ref": "argument.path"
                }
              }
            },
            {
              "op": "eq",
              "args": {
                "a": {
                  "op": "count",
                  "args": {
                    "items": {
                      "op": "path_captured_entities",
                      "args": {
                        "path": {
                          "op": "context",
                          "ref": "argument.path"
                        }
                      }
                    }
                  }
                },
                "b": {
                  "op": "maximum",
                  "args": {
                    "values": {
                      "op": "map",
                      "args": {
                        "items": {
                          "op": "traverse_paths",
                          "args": {
                            "entity": {
                              "op": "context",
                              "ref": "self"
                            },
                            "step_generator": {
                              "op": "jump_landing_steps",
                              "args": {
                                "entity": {
                                  "op": "context",
                                  "ref": "self"
                                },
                                "directions": {
                                  "op": "list",
                                  "args": {
                                    "values": [
                                      {
                                        "op": "vector",
                                        "args": {
                                          "row": {
                                            "op": "literal",
                                            "value": 1
                                          },
                                          "column": {
                                            "op": "literal",
                                            "value": -1
                                          }
                                        }
                                      },
                                      {
                                        "op": "vector",
                                        "args": {
                                          "row": {
                                            "op": "literal",
                                            "value": 1
                                          },
                                          "column": {
                                            "op": "literal",
                                            "value": 1
                                          }
                                        }
                                      },
                                      {
                                        "op": "vector",
                                        "args": {
                                          "row": {
                                            "op": "literal",
                                            "value": -1
                                          },
                                          "column": {
                                            "op": "literal",
                                            "value": -1
                                          }
                                        }
                                      },
                                      {
                                        "op": "vector",
                                        "args": {
                                          "row": {
                                            "op": "literal",
                                            "value": -1
                                          },
                                          "column": {
                                            "op": "literal",
                                            "value": 1
                                          }
                                        }
                                      }
                                    ]
                                  }
                                },
                                "orientation": {
                                  "op": "owner_orientation",
                                  "args": {
                                    "entity": {
                                      "op": "context",
                                      "ref": "self"
                                    }
                                  }
                                },
                                "flying": {
                                  "op": "literal",
                                  "value": true
                                },
                                "max_flight": {
                                  "op": "literal",
                                  "value": 9
                                },
                                "target_occupancy": {
                                  "op": "literal",
                                  "value": "empty"
                                },
                                "jumped_occupancy": {
                                  "op": "literal",
                                  "value": "opponent"
                                }
                              }
                            },
                            "max_depth": {
                              "op": "literal",
                              "value": 40
                            },
                            "captured_blockers": {
                              "op": "literal",
                              "value": true
                            },
                            "no_repeat_capture": {
                              "op": "literal",
                              "value": true
                            },
                            "stop_on_crowning": {
                              "op": "literal",
                              "value": false
                            }
                          }
                        },
                        "variable": {
                          "op": "literal",
                          "value": "p"
                        },
                        "expression": {
                          "op": "count",
                          "args": {
                            "items": {
                              "op": "path_captured_entities",
                              "args": {
                                "path": {
                                  "op": "context",
                                  "ref": "local.p"
                                }
                              }
                            }
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
          ]
        }
      },
      "effects": [
        {
          "op": "apply_path",
          "args": {
            "entity": {
              "op": "context",
              "ref": "self"
            },
            "path": {
              "op": "context",
              "ref": "argument.path"
            },
            "remove_traversed_entities": {
              "op": "literal",
              "value": true
            }
          }
        },
        {
          "op": "emit_event",
          "args": {
            "name": {
              "op": "literal",
              "value": "piece.captured"
            }
          }
        },
        {
          "op": "advance_turn",
          "args": {}
        }
      ],
      "priority": 0,
      "parameters": [
        {
          "key": "path",
          "type": "path"
        }
      ]
    },
    {
      "key": "candidates",
      "entity": "king",
      "trigger": "hook",
      "phase": "turn",
      "condition": {
        "op": "literal",
        "value": true
      },
      "effects": [
        {
          "op": "emit_candidate",
          "args": {
            "entity": {
              "op": "context",
              "ref": "self"
            },
            "path": {
              "op": "context",
              "ref": "candidate"
            }
          }
        }
      ],
      "priority": 0,
      "hook": "action.generate",
      "iterator": {
        "op": "traverse_paths",
        "args": {
          "entity": {
            "op": "context",
            "ref": "self"
          },
          "step_generator": {
            "op": "jump_landing_steps",
            "args": {
              "entity": {
                "op": "context",
                "ref": "self"
              },
              "directions": {
                "op": "list",
                "args": {
                  "values": [
                    {
                      "op": "vector",
                      "args": {
                        "row": {
                          "op": "literal",
                          "value": 1
                        },
                        "column": {
                          "op": "literal",
                          "value": -1
                        }
                      }
                    },
                    {
                      "op": "vector",
                      "args": {
                        "row": {
                          "op": "literal",
                          "value": 1
                        },
                        "column": {
                          "op": "literal",
                          "value": 1
                        }
                      }
                    },
                    {
                      "op": "vector",
                      "args": {
                        "row": {
                          "op": "literal",
                          "value": -1
                        },
                        "column": {
                          "op": "literal",
                          "value": -1
                        }
                      }
                    },
                    {
                      "op": "vector",
                      "args": {
                        "row": {
                          "op": "literal",
                          "value": -1
                        },
                        "column": {
                          "op": "literal",
                          "value": 1
                        }
                      }
                    }
                  ]
                }
              },
              "orientation": {
                "op": "owner_orientation",
                "args": {
                  "entity": {
                    "op": "context",
                    "ref": "self"
                  }
                }
              },
              "flying": {
                "op": "literal",
                "value": true
              },
              "max_flight": {
                "op": "literal",
                "value": 9
              },
              "target_occupancy": {
                "op": "literal",
                "value": "empty"
              },
              "jumped_occupancy": {
                "op": "literal",
                "value": "opponent"
              }
            }
          },
          "max_depth": {
            "op": "literal",
            "value": 40
          },
          "captured_blockers": {
            "op": "literal",
            "value": true
          },
          "no_repeat_capture": {
            "op": "literal",
            "value": true
          },
          "stop_on_crowning": {
            "op": "literal",
            "value": false
          }
        }
      },
      "variable": "candidate"
    },
    {
      "key": "evaluate",
      "entity": "victory",
      "trigger": "hook",
      "phase": "*",
      "condition": {
        "op": "eq",
        "args": {
          "a": {
            "op": "available_action_count",
            "args": {
              "actor": {
                "op": "next_participant",
                "args": {
                  "participant": {
                    "op": "context",
                    "ref": "active_participant"
                  }
                }
              }
            }
          },
          "b": {
            "op": "literal",
            "value": 0
          }
        }
      },
      "effects": [
        {
          "op": "complete_objective",
          "args": {
            "entity": {
              "op": "context",
              "ref": "self"
            }
          }
        },
        {
          "op": "finish_game",
          "args": {
            "result": {
              "op": "literal",
              "value": "victory"
            }
          }
        }
      ],
      "priority": 0,
      "hook": "game.evaluate"
    },
    {
      "key": "evaluate",
      "entity": "draw",
      "trigger": "hook",
      "phase": "*",
      "condition": {
        "op": "gte",
        "args": {
          "a": {
            "op": "field",
            "args": {
              "entity": {
                "op": "context",
                "ref": "game"
              },
              "key": {
                "op": "literal",
                "value": "draw_counter"
              }
            }
          },
          "b": {
            "op": "literal",
            "value": 80
          }
        }
      },
      "effects": [
        {
          "op": "complete_objective",
          "args": {
            "entity": {
              "op": "context",
              "ref": "self"
            }
          }
        },
        {
          "op": "finish_game",
          "args": {
            "result": {
              "op": "literal",
              "value": "draw"
            }
          }
        }
      ],
      "priority": 0,
      "hook": "game.evaluate"
    },
    {
      "key": "count",
      "entity": "capture_quest",
      "trigger": "hook",
      "phase": "*",
      "condition": {
        "op": "eq",
        "args": {
          "a": {
            "op": "event_attribute",
            "args": {
              "event": {
                "op": "context",
                "ref": "event"
              },
              "attribute": {
                "op": "literal",
                "value": "kind"
              }
            }
          },
          "b": {
            "op": "literal",
            "value": "piece.captured"
          }
        }
      },
      "effects": [
        {
          "op": "increment_field",
          "args": {
            "entity": {
              "op": "context",
              "ref": "self"
            },
            "field": {
              "op": "literal",
              "value": "progress"
            },
            "amount": {
              "op": "literal",
              "value": 1
            }
          }
        }
      ],
      "priority": 0,
      "hook": "objective.evaluate"
    }
  ],
  "visuals": [
    {
      "entity": "square",
      "primitives": [
        {
          "kind": "rectangle",
          "width": 100,
          "height": 100,
          "fill": "#734f38"
        }
      ]
    },
    {
      "entity": "man",
      "primitives": [
        {
          "kind": "ellipse",
          "x": 10,
          "y": 10,
          "width": 80,
          "height": 80,
          "fill": "#ddddcc"
        }
      ]
    },
    {
      "entity": "king",
      "primitives": [
        {
          "kind": "ellipse",
          "x": 10,
          "y": 10,
          "width": 80,
          "height": 80,
          "fill": "#ddddcc"
        }
      ]
    }
  ],
  "assets": []
}
```

### moneyproperty.json

```json
{
  "format": "bgwq.configuration",
  "format_version": 1,
  "definition": {
    "key": "moneyproperty",
    "name": "MoneyProperty: Original Property Trading",
    "min_participants": 2,
    "max_participants": 8,
    "semantics_version": 1
  },
  "roles": [
    {
      "key": "seat_0",
      "name": "Player 1",
      "min": 0,
      "max": 1
    },
    {
      "key": "seat_1",
      "name": "Player 2",
      "min": 0,
      "max": 1
    },
    {
      "key": "seat_2",
      "name": "Player 3",
      "min": 0,
      "max": 1
    },
    {
      "key": "seat_3",
      "name": "Player 4",
      "min": 0,
      "max": 1
    },
    {
      "key": "seat_4",
      "name": "Player 5",
      "min": 0,
      "max": 1
    },
    {
      "key": "seat_5",
      "name": "Player 6",
      "min": 0,
      "max": 1
    },
    {
      "key": "seat_6",
      "name": "Player 7",
      "min": 0,
      "max": 1
    },
    {
      "key": "seat_7",
      "name": "Player 8",
      "min": 0,
      "max": 1
    }
  ],
  "phases": [
    {
      "key": "turn_start",
      "name": "Turn Start",
      "initial": true,
      "order": 0
    },
    {
      "key": "roll",
      "name": "Roll",
      "initial": false,
      "order": 1
    },
    {
      "key": "move",
      "name": "Move",
      "initial": false,
      "order": 2
    },
    {
      "key": "resolve",
      "name": "Resolve",
      "initial": false,
      "order": 3
    },
    {
      "key": "decision",
      "name": "Decision",
      "initial": false,
      "order": 4
    },
    {
      "key": "management",
      "name": "Management",
      "initial": false,
      "order": 5
    },
    {
      "key": "turn_end",
      "name": "Turn End",
      "initial": false,
      "order": 6
    }
  ],
  "entities": [
    {
      "key": "game",
      "kind": "game",
      "name": "Game"
    },
    {
      "key": "track",
      "kind": "space",
      "name": "Track"
    },
    {
      "key": "lot",
      "kind": "space",
      "name": "Lot"
    },
    {
      "key": "deck",
      "kind": "space",
      "name": "Deck"
    },
    {
      "key": "inventory",
      "kind": "space",
      "name": "Inventory"
    },
    {
      "key": "token",
      "kind": "item",
      "name": "Token"
    },
    {
      "key": "property",
      "kind": "item",
      "name": "Property"
    },
    {
      "key": "transit",
      "kind": "item",
      "name": "Transit"
    },
    {
      "key": "utility",
      "kind": "item",
      "name": "Utility"
    },
    {
      "key": "building",
      "kind": "item",
      "name": "Building"
    },
    {
      "key": "card",
      "kind": "item",
      "name": "Card"
    },
    {
      "key": "trade_offer",
      "kind": "item",
      "name": "Trade Offer"
    },
    {
      "key": "auction",
      "kind": "item",
      "name": "Auction"
    },
    {
      "key": "bankruptcy",
      "kind": "objective",
      "name": "Bankruptcy"
    },
    {
      "key": "last_solvent",
      "kind": "objective",
      "name": "Last Solvent"
    },
    {
      "key": "wealth_quest",
      "kind": "objective",
      "name": "Wealth Quest"
    }
  ],
  "seeds": [
    {
      "key": "root",
      "type": "game"
    },
    {
      "key": "track",
      "type": "track",
      "parent": "root"
    },
    {
      "key": "events_deck",
      "type": "deck",
      "parent": "root"
    },
    {
      "key": "city_deck",
      "type": "deck",
      "parent": "root"
    },
    {
      "key": "bankruptcy",
      "type": "bankruptcy",
      "parent": "root",
      "values": {
        "completed": false,
        "progress": 0
      }
    },
    {
      "key": "last_solvent",
      "type": "last_solvent",
      "parent": "root",
      "values": {
        "completed": false,
        "progress": 0
      }
    },
    {
      "key": "wealth_quest",
      "type": "wealth_quest",
      "parent": "root",
      "values": {
        "completed": false,
        "progress": 0
      }
    },
    {
      "key": "inventory_0",
      "type": "inventory",
      "parent": "root",
      "owner": 0,
      "values": {
        "balance": 1500
      }
    },
    {
      "key": "inventory_1",
      "type": "inventory",
      "parent": "root",
      "owner": 1,
      "values": {
        "balance": 1500
      }
    },
    {
      "key": "inventory_2",
      "type": "inventory",
      "parent": "root",
      "owner": 2,
      "values": {
        "balance": 1500
      }
    },
    {
      "key": "inventory_3",
      "type": "inventory",
      "parent": "root",
      "owner": 3,
      "values": {
        "balance": 1500
      }
    },
    {
      "key": "inventory_4",
      "type": "inventory",
      "parent": "root",
      "owner": 4,
      "values": {
        "balance": 1500
      }
    },
    {
      "key": "inventory_5",
      "type": "inventory",
      "parent": "root",
      "owner": 5,
      "values": {
        "balance": 1500
      }
    },
    {
      "key": "inventory_6",
      "type": "inventory",
      "parent": "root",
      "owner": 6,
      "values": {
        "balance": 1500
      }
    },
    {
      "key": "inventory_7",
      "type": "inventory",
      "parent": "root",
      "owner": 7,
      "values": {
        "balance": 1500
      }
    },
    {
      "key": "start",
      "type": "lot",
      "parent": "track",
      "order": 0,
      "x": 0,
      "y": 0,
      "values": {
        "name": "Start Plaza",
        "location_kind": "start",
        "price": 0,
        "base_rent": 0,
        "build_cost": 50,
        "mortgage_value": 40,
        "houses": 0,
        "mortgaged": false,
        "group": "district0"
      }
    },
    {
      "key": "lot1",
      "type": "lot",
      "parent": "track",
      "order": 1,
      "x": 80,
      "y": 0,
      "values": {
        "name": "Harbor Lane",
        "location_kind": "property",
        "price": 100,
        "base_rent": 11,
        "build_cost": 50,
        "mortgage_value": 48,
        "houses": 0,
        "mortgaged": false,
        "group": "district0"
      }
    },
    {
      "key": "deed_lot1",
      "type": "property",
      "location": "lot1",
      "parent": "root",
      "values": {
        "mortgaged": false,
        "houses": 0,
        "price": 100,
        "base_rent": 11,
        "build_cost": 50,
        "mortgage_value": 48,
        "group": "district0"
      }
    },
    {
      "key": "event1",
      "type": "lot",
      "parent": "track",
      "order": 2,
      "x": 160,
      "y": 0,
      "values": {
        "name": "Community Events",
        "location_kind": "city",
        "price": 0,
        "base_rent": 0,
        "build_cost": 50,
        "mortgage_value": 56,
        "houses": 0,
        "mortgaged": false,
        "group": "district0"
      }
    },
    {
      "key": "lot2",
      "type": "lot",
      "parent": "track",
      "order": 3,
      "x": 240,
      "y": 0,
      "values": {
        "name": "Cedar Walk",
        "location_kind": "property",
        "price": 100,
        "base_rent": 17,
        "build_cost": 50,
        "mortgage_value": 64,
        "houses": 0,
        "mortgaged": false,
        "group": "district0"
      }
    },
    {
      "key": "deed_lot2",
      "type": "property",
      "location": "lot2",
      "parent": "root",
      "values": {
        "mortgaged": false,
        "houses": 0,
        "price": 100,
        "base_rent": 17,
        "build_cost": 50,
        "mortgage_value": 64,
        "group": "district0"
      }
    },
    {
      "key": "tax1",
      "type": "lot",
      "parent": "track",
      "order": 4,
      "x": 320,
      "y": 0,
      "values": {
        "name": "Municipal Fee",
        "location_kind": "tax",
        "price": 0,
        "base_rent": 0,
        "build_cost": 50,
        "mortgage_value": 72,
        "houses": 0,
        "mortgaged": false,
        "group": "district0",
        "fee": 100
      }
    },
    {
      "key": "rail1",
      "type": "lot",
      "parent": "track",
      "order": 5,
      "x": 400,
      "y": 0,
      "values": {
        "name": "Metro Central",
        "location_kind": "transit",
        "price": 140,
        "base_rent": 23,
        "build_cost": 50,
        "mortgage_value": 80,
        "houses": 0,
        "mortgaged": false,
        "group": "district1"
      }
    },
    {
      "key": "deed_rail1",
      "type": "transit",
      "location": "rail1",
      "parent": "root",
      "values": {
        "mortgaged": false,
        "houses": 0,
        "price": 140,
        "base_rent": 23,
        "build_cost": 50,
        "mortgage_value": 80,
        "group": "district1"
      }
    },
    {
      "key": "lot3",
      "type": "lot",
      "parent": "track",
      "order": 6,
      "x": 480,
      "y": 0,
      "values": {
        "name": "Ash Grove",
        "location_kind": "property",
        "price": 140,
        "base_rent": 26,
        "build_cost": 50,
        "mortgage_value": 88,
        "houses": 0,
        "mortgaged": false,
        "group": "district1"
      }
    },
    {
      "key": "deed_lot3",
      "type": "property",
      "location": "lot3",
      "parent": "root",
      "values": {
        "mortgaged": false,
        "houses": 0,
        "price": 140,
        "base_rent": 26,
        "build_cost": 50,
        "mortgage_value": 88,
        "group": "district1"
      }
    },
    {
      "key": "event2",
      "type": "lot",
      "parent": "track",
      "order": 7,
      "x": 560,
      "y": 0,
      "values": {
        "name": "City Stories",
        "location_kind": "events",
        "price": 0,
        "base_rent": 0,
        "build_cost": 50,
        "mortgage_value": 96,
        "houses": 0,
        "mortgaged": false,
        "group": "district1"
      }
    },
    {
      "key": "lot4",
      "type": "lot",
      "parent": "track",
      "order": 8,
      "x": 640,
      "y": 0,
      "values": {
        "name": "Maple Gardens",
        "location_kind": "property",
        "price": 140,
        "base_rent": 32,
        "build_cost": 50,
        "mortgage_value": 104,
        "houses": 0,
        "mortgaged": false,
        "group": "district1"
      }
    },
    {
      "key": "deed_lot4",
      "type": "property",
      "location": "lot4",
      "parent": "root",
      "values": {
        "mortgaged": false,
        "houses": 0,
        "price": 140,
        "base_rent": 32,
        "build_cost": 50,
        "mortgage_value": 104,
        "group": "district1"
      }
    },
    {
      "key": "lot5",
      "type": "lot",
      "parent": "track",
      "order": 9,
      "x": 720,
      "y": 0,
      "values": {
        "name": "Elm Promenade",
        "location_kind": "property",
        "price": 140,
        "base_rent": 35,
        "build_cost": 50,
        "mortgage_value": 112,
        "houses": 0,
        "mortgaged": false,
        "group": "district1"
      }
    },
    {
      "key": "deed_lot5",
      "type": "property",
      "location": "lot5",
      "parent": "root",
      "values": {
        "mortgaged": false,
        "houses": 0,
        "price": 140,
        "base_rent": 35,
        "build_cost": 50,
        "mortgage_value": 112,
        "group": "district1"
      }
    },
    {
      "key": "rest1",
      "type": "lot",
      "parent": "track",
      "order": 10,
      "x": 800,
      "y": 0,
      "values": {
        "name": "Visitors Lounge",
        "location_kind": "detention",
        "price": 0,
        "base_rent": 0,
        "build_cost": 70,
        "mortgage_value": 120,
        "houses": 0,
        "mortgaged": false,
        "group": "district2"
      }
    },
    {
      "key": "lot6",
      "type": "lot",
      "parent": "track",
      "order": 11,
      "x": 720,
      "y": 80,
      "values": {
        "name": "Bayfront Row",
        "location_kind": "property",
        "price": 180,
        "base_rent": 41,
        "build_cost": 70,
        "mortgage_value": 128,
        "houses": 0,
        "mortgaged": false,
        "group": "district2"
      }
    },
    {
      "key": "deed_lot6",
      "type": "property",
      "location": "lot6",
      "parent": "root",
      "values": {
        "mortgaged": false,
        "houses": 0,
        "price": 180,
        "base_rent": 41,
        "build_cost": 70,
        "mortgage_value": 128,
        "group": "district2"
      }
    },
    {
      "key": "util1",
      "type": "lot",
      "parent": "track",
      "order": 12,
      "x": 640,
      "y": 160,
      "values": {
        "name": "Water Cooperative",
        "location_kind": "utility",
        "price": 180,
        "base_rent": 44,
        "build_cost": 70,
        "mortgage_value": 136,
        "houses": 0,
        "mortgaged": false,
        "group": "district2"
      }
    },
    {
      "key": "deed_util1",
      "type": "utility",
      "location": "util1",
      "parent": "root",
      "values": {
        "mortgaged": false,
        "houses": 0,
        "price": 180,
        "base_rent": 44,
        "build_cost": 70,
        "mortgage_value": 136,
        "group": "district2"
      }
    },
    {
      "key": "lot7",
      "type": "lot",
      "parent": "track",
      "order": 13,
      "x": 560,
      "y": 240,
      "values": {
        "name": "North Crescent",
        "location_kind": "property",
        "price": 180,
        "base_rent": 47,
        "build_cost": 70,
        "mortgage_value": 144,
        "houses": 0,
        "mortgaged": false,
        "group": "district2"
      }
    },
    {
      "key": "deed_lot7",
      "type": "property",
      "location": "lot7",
      "parent": "root",
      "values": {
        "mortgaged": false,
        "houses": 0,
        "price": 180,
        "base_rent": 47,
        "build_cost": 70,
        "mortgage_value": 144,
        "group": "district2"
      }
    },
    {
      "key": "lot8",
      "type": "lot",
      "parent": "track",
      "order": 14,
      "x": 480,
      "y": 320,
      "values": {
        "name": "Canal Passage",
        "location_kind": "property",
        "price": 180,
        "base_rent": 50,
        "build_cost": 70,
        "mortgage_value": 152,
        "houses": 0,
        "mortgaged": false,
        "group": "district2"
      }
    },
    {
      "key": "deed_lot8",
      "type": "property",
      "location": "lot8",
      "parent": "root",
      "values": {
        "mortgaged": false,
        "houses": 0,
        "price": 180,
        "base_rent": 50,
        "build_cost": 70,
        "mortgage_value": 152,
        "group": "district2"
      }
    },
    {
      "key": "rail2",
      "type": "lot",
      "parent": "track",
      "order": 15,
      "x": 400,
      "y": 400,
      "values": {
        "name": "River Transit",
        "location_kind": "transit",
        "price": 220,
        "base_rent": 53,
        "build_cost": 70,
        "mortgage_value": 160,
        "houses": 0,
        "mortgaged": false,
        "group": "district3"
      }
    },
    {
      "key": "deed_rail2",
      "type": "transit",
      "location": "rail2",
      "parent": "root",
      "values": {
        "mortgaged": false,
        "houses": 0,
        "price": 220,
        "base_rent": 53,
        "build_cost": 70,
        "mortgage_value": 160,
        "group": "district3"
      }
    },
    {
      "key": "lot9",
      "type": "lot",
      "parent": "track",
      "order": 16,
      "x": 320,
      "y": 480,
      "values": {
        "name": "Oak Orchard",
        "location_kind": "property",
        "price": 220,
        "base_rent": 56,
        "build_cost": 70,
        "mortgage_value": 168,
        "houses": 0,
        "mortgaged": false,
        "group": "district3"
      }
    },
    {
      "key": "deed_lot9",
      "type": "property",
      "location": "lot9",
      "parent": "root",
      "values": {
        "mortgaged": false,
        "houses": 0,
        "price": 220,
        "base_rent": 56,
        "build_cost": 70,
        "mortgage_value": 168,
        "group": "district3"
      }
    },
    {
      "key": "event3",
      "type": "lot",
      "parent": "track",
      "order": 17,
      "x": 240,
      "y": 560,
      "values": {
        "name": "Community Events",
        "location_kind": "city",
        "price": 0,
        "base_rent": 0,
        "build_cost": 70,
        "mortgage_value": 176,
        "houses": 0,
        "mortgaged": false,
        "group": "district3"
      }
    },
    {
      "key": "lot10",
      "type": "lot",
      "parent": "track",
      "order": 18,
      "x": 160,
      "y": 640,
      "values": {
        "name": "Foundry Square",
        "location_kind": "property",
        "price": 220,
        "base_rent": 62,
        "build_cost": 70,
        "mortgage_value": 184,
        "houses": 0,
        "mortgaged": false,
        "group": "district3"
      }
    },
    {
      "key": "deed_lot10",
      "type": "property",
      "location": "lot10",
      "parent": "root",
      "values": {
        "mortgaged": false,
        "houses": 0,
        "price": 220,
        "base_rent": 62,
        "build_cost": 70,
        "mortgage_value": 184,
        "group": "district3"
      }
    },
    {
      "key": "lot11",
      "type": "lot",
      "parent": "track",
      "order": 19,
      "x": 80,
      "y": 720,
      "values": {
        "name": "Garden Street",
        "location_kind": "property",
        "price": 220,
        "base_rent": 65,
        "build_cost": 70,
        "mortgage_value": 192,
        "houses": 0,
        "mortgaged": false,
        "group": "district3"
      }
    },
    {
      "key": "deed_lot11",
      "type": "property",
      "location": "lot11",
      "parent": "root",
      "values": {
        "mortgaged": false,
        "houses": 0,
        "price": 220,
        "base_rent": 65,
        "build_cost": 70,
        "mortgage_value": 192,
        "group": "district3"
      }
    },
    {
      "key": "break1",
      "type": "lot",
      "parent": "track",
      "order": 20,
      "x": 0,
      "y": 800,
      "values": {
        "name": "Open Commons",
        "location_kind": "rest",
        "price": 0,
        "base_rent": 0,
        "build_cost": 90,
        "mortgage_value": 200,
        "houses": 0,
        "mortgaged": false,
        "group": "district4"
      }
    },
    {
      "key": "lot12",
      "type": "lot",
      "parent": "track",
      "order": 21,
      "x": 80,
      "y": 800,
      "values": {
        "name": "Willow Heights",
        "location_kind": "property",
        "price": 260,
        "base_rent": 71,
        "build_cost": 90,
        "mortgage_value": 208,
        "houses": 0,
        "mortgaged": false,
        "group": "district4"
      }
    },
    {
      "key": "deed_lot12",
      "type": "property",
      "location": "lot12",
      "parent": "root",
      "values": {
        "mortgaged": false,
        "houses": 0,
        "price": 260,
        "base_rent": 71,
        "build_cost": 90,
        "mortgage_value": 208,
        "group": "district4"
      }
    },
    {
      "key": "event4",
      "type": "lot",
      "parent": "track",
      "order": 22,
      "x": 160,
      "y": 800,
      "values": {
        "name": "City Stories",
        "location_kind": "events",
        "price": 0,
        "base_rent": 0,
        "build_cost": 90,
        "mortgage_value": 216,
        "houses": 0,
        "mortgaged": false,
        "group": "district4"
      }
    },
    {
      "key": "lot13",
      "type": "lot",
      "parent": "track",
      "order": 23,
      "x": 240,
      "y": 800,
      "values": {
        "name": "Sunset Pier",
        "location_kind": "property",
        "price": 260,
        "base_rent": 77,
        "build_cost": 90,
        "mortgage_value": 224,
        "houses": 0,
        "mortgaged": false,
        "group": "district4"
      }
    },
    {
      "key": "deed_lot13",
      "type": "property",
      "location": "lot13",
      "parent": "root",
      "values": {
        "mortgaged": false,
        "houses": 0,
        "price": 260,
        "base_rent": 77,
        "build_cost": 90,
        "mortgage_value": 224,
        "group": "district4"
      }
    },
    {
      "key": "lot14",
      "type": "lot",
      "parent": "track",
      "order": 24,
      "x": 320,
      "y": 800,
      "values": {
        "name": "Cypress Boulevard",
        "location_kind": "property",
        "price": 260,
        "base_rent": 80,
        "build_cost": 90,
        "mortgage_value": 232,
        "houses": 0,
        "mortgaged": false,
        "group": "district4"
      }
    },
    {
      "key": "deed_lot14",
      "type": "property",
      "location": "lot14",
      "parent": "root",
      "values": {
        "mortgaged": false,
        "houses": 0,
        "price": 260,
        "base_rent": 80,
        "build_cost": 90,
        "mortgage_value": 232,
        "group": "district4"
      }
    },
    {
      "key": "rail3",
      "type": "lot",
      "parent": "track",
      "order": 25,
      "x": 400,
      "y": 800,
      "values": {
        "name": "Highland Railway",
        "location_kind": "transit",
        "price": 300,
        "base_rent": 83,
        "build_cost": 90,
        "mortgage_value": 240,
        "houses": 0,
        "mortgaged": false,
        "group": "district5"
      }
    },
    {
      "key": "deed_rail3",
      "type": "transit",
      "location": "rail3",
      "parent": "root",
      "values": {
        "mortgaged": false,
        "houses": 0,
        "price": 300,
        "base_rent": 83,
        "build_cost": 90,
        "mortgage_value": 240,
        "group": "district5"
      }
    },
    {
      "key": "lot15",
      "type": "lot",
      "parent": "track",
      "order": 26,
      "x": 480,
      "y": 800,
      "values": {
        "name": "Lakehouse Avenue",
        "location_kind": "property",
        "price": 300,
        "base_rent": 86,
        "build_cost": 90,
        "mortgage_value": 248,
        "houses": 0,
        "mortgaged": false,
        "group": "district5"
      }
    },
    {
      "key": "deed_lot15",
      "type": "property",
      "location": "lot15",
      "parent": "root",
      "values": {
        "mortgaged": false,
        "houses": 0,
        "price": 300,
        "base_rent": 86,
        "build_cost": 90,
        "mortgage_value": 248,
        "group": "district5"
      }
    },
    {
      "key": "lot16",
      "type": "lot",
      "parent": "track",
      "order": 27,
      "x": 560,
      "y": 800,
      "values": {
        "name": "Hillgate Road",
        "location_kind": "property",
        "price": 300,
        "base_rent": 89,
        "build_cost": 90,
        "mortgage_value": 256,
        "houses": 0,
        "mortgaged": false,
        "group": "district5"
      }
    },
    {
      "key": "deed_lot16",
      "type": "property",
      "location": "lot16",
      "parent": "root",
      "values": {
        "mortgaged": false,
        "houses": 0,
        "price": 300,
        "base_rent": 89,
        "build_cost": 90,
        "mortgage_value": 256,
        "group": "district5"
      }
    },
    {
      "key": "util2",
      "type": "lot",
      "parent": "track",
      "order": 28,
      "x": 640,
      "y": 800,
      "values": {
        "name": "Solar Collective",
        "location_kind": "utility",
        "price": 300,
        "base_rent": 92,
        "build_cost": 90,
        "mortgage_value": 264,
        "houses": 0,
        "mortgaged": false,
        "group": "district5"
      }
    },
    {
      "key": "deed_util2",
      "type": "utility",
      "location": "util2",
      "parent": "root",
      "values": {
        "mortgaged": false,
        "houses": 0,
        "price": 300,
        "base_rent": 92,
        "build_cost": 90,
        "mortgage_value": 264,
        "group": "district5"
      }
    },
    {
      "key": "lot17",
      "type": "lot",
      "parent": "track",
      "order": 29,
      "x": 720,
      "y": 800,
      "values": {
        "name": "Old Market",
        "location_kind": "property",
        "price": 300,
        "base_rent": 95,
        "build_cost": 90,
        "mortgage_value": 272,
        "houses": 0,
        "mortgaged": false,
        "group": "district5"
      }
    },
    {
      "key": "deed_lot17",
      "type": "property",
      "location": "lot17",
      "parent": "root",
      "values": {
        "mortgaged": false,
        "houses": 0,
        "price": 300,
        "base_rent": 95,
        "build_cost": 90,
        "mortgage_value": 272,
        "group": "district5"
      }
    },
    {
      "key": "goto",
      "type": "lot",
      "parent": "track",
      "order": 30,
      "x": 800,
      "y": 800,
      "values": {
        "name": "Go to Visitors Lounge",
        "location_kind": "goto",
        "price": 0,
        "base_rent": 0,
        "build_cost": 110,
        "mortgage_value": 280,
        "houses": 0,
        "mortgaged": false,
        "group": "district6"
      }
    },
    {
      "key": "lot18",
      "type": "lot",
      "parent": "track",
      "order": 31,
      "x": 720,
      "y": 720,
      "values": {
        "name": "Copper Street",
        "location_kind": "property",
        "price": 340,
        "base_rent": 101,
        "build_cost": 110,
        "mortgage_value": 288,
        "houses": 0,
        "mortgaged": false,
        "group": "district6"
      }
    },
    {
      "key": "deed_lot18",
      "type": "property",
      "location": "lot18",
      "parent": "root",
      "values": {
        "mortgaged": false,
        "houses": 0,
        "price": 340,
        "base_rent": 101,
        "build_cost": 110,
        "mortgage_value": 288,
        "group": "district6"
      }
    },
    {
      "key": "lot19",
      "type": "lot",
      "parent": "track",
      "order": 32,
      "x": 640,
      "y": 640,
      "values": {
        "name": "Market Place",
        "location_kind": "property",
        "price": 340,
        "base_rent": 104,
        "build_cost": 110,
        "mortgage_value": 296,
        "houses": 0,
        "mortgaged": false,
        "group": "district6"
      }
    },
    {
      "key": "deed_lot19",
      "type": "property",
      "location": "lot19",
      "parent": "root",
      "values": {
        "mortgaged": false,
        "houses": 0,
        "price": 340,
        "base_rent": 104,
        "build_cost": 110,
        "mortgage_value": 296,
        "group": "district6"
      }
    },
    {
      "key": "event5",
      "type": "lot",
      "parent": "track",
      "order": 33,
      "x": 560,
      "y": 560,
      "values": {
        "name": "Community Events",
        "location_kind": "city",
        "price": 0,
        "base_rent": 0,
        "build_cost": 110,
        "mortgage_value": 304,
        "houses": 0,
        "mortgaged": false,
        "group": "district6"
      }
    },
    {
      "key": "lot20",
      "type": "lot",
      "parent": "track",
      "order": 34,
      "x": 480,
      "y": 480,
      "values": {
        "name": "Granite Tower",
        "location_kind": "property",
        "price": 340,
        "base_rent": 110,
        "build_cost": 110,
        "mortgage_value": 312,
        "houses": 0,
        "mortgaged": false,
        "group": "district6"
      }
    },
    {
      "key": "deed_lot20",
      "type": "property",
      "location": "lot20",
      "parent": "root",
      "values": {
        "mortgaged": false,
        "houses": 0,
        "price": 340,
        "base_rent": 110,
        "build_cost": 110,
        "mortgage_value": 312,
        "group": "district6"
      }
    },
    {
      "key": "rail4",
      "type": "lot",
      "parent": "track",
      "order": 35,
      "x": 400,
      "y": 400,
      "values": {
        "name": "Coastal Transit",
        "location_kind": "transit",
        "price": 380,
        "base_rent": 113,
        "build_cost": 110,
        "mortgage_value": 320,
        "houses": 0,
        "mortgaged": false,
        "group": "district7"
      }
    },
    {
      "key": "deed_rail4",
      "type": "transit",
      "location": "rail4",
      "parent": "root",
      "values": {
        "mortgaged": false,
        "houses": 0,
        "price": 380,
        "base_rent": 113,
        "build_cost": 110,
        "mortgage_value": 320,
        "group": "district7"
      }
    },
    {
      "key": "event6",
      "type": "lot",
      "parent": "track",
      "order": 36,
      "x": 320,
      "y": 320,
      "values": {
        "name": "City Stories",
        "location_kind": "events",
        "price": 0,
        "base_rent": 0,
        "build_cost": 110,
        "mortgage_value": 328,
        "houses": 0,
        "mortgaged": false,
        "group": "district7"
      }
    },
    {
      "key": "lot21",
      "type": "lot",
      "parent": "track",
      "order": 37,
      "x": 240,
      "y": 240,
      "values": {
        "name": "Silver Promenade",
        "location_kind": "property",
        "price": 380,
        "base_rent": 119,
        "build_cost": 110,
        "mortgage_value": 336,
        "houses": 0,
        "mortgaged": false,
        "group": "district7"
      }
    },
    {
      "key": "deed_lot21",
      "type": "property",
      "location": "lot21",
      "parent": "root",
      "values": {
        "mortgaged": false,
        "houses": 0,
        "price": 380,
        "base_rent": 119,
        "build_cost": 110,
        "mortgage_value": 336,
        "group": "district7"
      }
    },
    {
      "key": "tax2",
      "type": "lot",
      "parent": "track",
      "order": 38,
      "x": 160,
      "y": 160,
      "values": {
        "name": "Transit Tax",
        "location_kind": "tax",
        "price": 0,
        "base_rent": 0,
        "build_cost": 110,
        "mortgage_value": 344,
        "houses": 0,
        "mortgaged": false,
        "group": "district7",
        "fee": 150
      }
    },
    {
      "key": "lot22",
      "type": "lot",
      "parent": "track",
      "order": 39,
      "x": 80,
      "y": 80,
      "values": {
        "name": "Summit Terrace",
        "location_kind": "property",
        "price": 380,
        "base_rent": 125,
        "build_cost": 110,
        "mortgage_value": 352,
        "houses": 0,
        "mortgaged": false,
        "group": "district7"
      }
    },
    {
      "key": "deed_lot22",
      "type": "property",
      "location": "lot22",
      "parent": "root",
      "values": {
        "mortgaged": false,
        "houses": 0,
        "price": 380,
        "base_rent": 125,
        "build_cost": 110,
        "mortgage_value": 352,
        "group": "district7"
      }
    },
    {
      "key": "token_0",
      "type": "token",
      "owner": 0,
      "location": "start",
      "values": {
        "detained": false,
        "doubles": 0,
        "detention_attempts": 0
      }
    },
    {
      "key": "token_1",
      "type": "token",
      "owner": 1,
      "location": "start",
      "values": {
        "detained": false,
        "doubles": 0,
        "detention_attempts": 0
      }
    },
    {
      "key": "token_2",
      "type": "token",
      "owner": 2,
      "location": "start",
      "values": {
        "detained": false,
        "doubles": 0,
        "detention_attempts": 0
      }
    },
    {
      "key": "token_3",
      "type": "token",
      "owner": 3,
      "location": "start",
      "values": {
        "detained": false,
        "doubles": 0,
        "detention_attempts": 0
      }
    },
    {
      "key": "token_4",
      "type": "token",
      "owner": 4,
      "location": "start",
      "values": {
        "detained": false,
        "doubles": 0,
        "detention_attempts": 0
      }
    },
    {
      "key": "token_5",
      "type": "token",
      "owner": 5,
      "location": "start",
      "values": {
        "detained": false,
        "doubles": 0,
        "detention_attempts": 0
      }
    },
    {
      "key": "token_6",
      "type": "token",
      "owner": 6,
      "location": "start",
      "values": {
        "detained": false,
        "doubles": 0,
        "detention_attempts": 0
      }
    },
    {
      "key": "token_7",
      "type": "token",
      "owner": 7,
      "location": "start",
      "values": {
        "detained": false,
        "doubles": 0,
        "detention_attempts": 0
      }
    },
    {
      "key": "events_deck_card_0",
      "type": "card",
      "parent": "events_deck",
      "order": 0,
      "values": {
        "text": "Receive a community grant",
        "operation": "credit",
        "amount": 120
      }
    },
    {
      "key": "events_deck_card_1",
      "type": "card",
      "parent": "events_deck",
      "order": 1,
      "values": {
        "text": "Support the local library",
        "operation": "debit",
        "amount": 50
      }
    },
    {
      "key": "events_deck_card_2",
      "type": "card",
      "parent": "events_deck",
      "order": 2,
      "values": {
        "text": "Travel to Start Plaza",
        "operation": "advance",
        "amount": 0
      }
    },
    {
      "key": "events_deck_card_3",
      "type": "card",
      "parent": "events_deck",
      "order": 3,
      "values": {
        "text": "Sponsor a public garden",
        "operation": "debit",
        "amount": 70
      }
    },
    {
      "key": "events_deck_card_4",
      "type": "card",
      "parent": "events_deck",
      "order": 4,
      "values": {
        "text": "Volunteer recognition award",
        "operation": "credit",
        "amount": 80
      }
    },
    {
      "key": "events_deck_card_5",
      "type": "card",
      "parent": "events_deck",
      "order": 5,
      "values": {
        "text": "Pay bridge maintenance",
        "operation": "debit",
        "amount": 45
      }
    },
    {
      "key": "events_deck_card_6",
      "type": "card",
      "parent": "events_deck",
      "order": 6,
      "values": {
        "text": "Local art prize",
        "operation": "credit",
        "amount": 150
      }
    },
    {
      "key": "events_deck_card_7",
      "type": "card",
      "parent": "events_deck",
      "order": 7,
      "values": {
        "text": "Neighborhood clean-up",
        "operation": "debit",
        "amount": 30
      }
    },
    {
      "key": "events_deck_card_8",
      "type": "card",
      "parent": "events_deck",
      "order": 8,
      "values": {
        "text": "Move three locations",
        "operation": "relative",
        "amount": 3
      }
    },
    {
      "key": "events_deck_card_9",
      "type": "card",
      "parent": "events_deck",
      "order": 9,
      "values": {
        "text": "Receive a transit rebate",
        "operation": "credit",
        "amount": 60
      }
    },
    {
      "key": "events_deck_card_10",
      "type": "card",
      "parent": "events_deck",
      "order": 10,
      "values": {
        "text": "Property repairs",
        "operation": "debit",
        "amount": 110
      }
    },
    {
      "key": "events_deck_card_11",
      "type": "card",
      "parent": "events_deck",
      "order": 11,
      "values": {
        "text": "Tourism bonus",
        "operation": "credit",
        "amount": 95
      }
    },
    {
      "key": "city_deck_card_0",
      "type": "card",
      "parent": "city_deck",
      "order": 0,
      "values": {
        "text": "Neighborhood clean-up",
        "operation": "debit",
        "amount": 30
      }
    },
    {
      "key": "city_deck_card_1",
      "type": "card",
      "parent": "city_deck",
      "order": 1,
      "values": {
        "text": "Move three locations",
        "operation": "relative",
        "amount": 3
      }
    },
    {
      "key": "city_deck_card_2",
      "type": "card",
      "parent": "city_deck",
      "order": 2,
      "values": {
        "text": "Receive a transit rebate",
        "operation": "credit",
        "amount": 60
      }
    },
    {
      "key": "city_deck_card_3",
      "type": "card",
      "parent": "city_deck",
      "order": 3,
      "values": {
        "text": "Property repairs",
        "operation": "debit",
        "amount": 110
      }
    },
    {
      "key": "city_deck_card_4",
      "type": "card",
      "parent": "city_deck",
      "order": 4,
      "values": {
        "text": "Tourism bonus",
        "operation": "credit",
        "amount": 95
      }
    },
    {
      "key": "city_deck_card_5",
      "type": "card",
      "parent": "city_deck",
      "order": 5,
      "values": {
        "text": "Receive a community grant",
        "operation": "credit",
        "amount": 120
      }
    },
    {
      "key": "city_deck_card_6",
      "type": "card",
      "parent": "city_deck",
      "order": 6,
      "values": {
        "text": "Support the local library",
        "operation": "debit",
        "amount": 50
      }
    },
    {
      "key": "city_deck_card_7",
      "type": "card",
      "parent": "city_deck",
      "order": 7,
      "values": {
        "text": "Travel to Start Plaza",
        "operation": "advance",
        "amount": 0
      }
    },
    {
      "key": "city_deck_card_8",
      "type": "card",
      "parent": "city_deck",
      "order": 8,
      "values": {
        "text": "Sponsor a public garden",
        "operation": "debit",
        "amount": 70
      }
    },
    {
      "key": "city_deck_card_9",
      "type": "card",
      "parent": "city_deck",
      "order": 9,
      "values": {
        "text": "Volunteer recognition award",
        "operation": "credit",
        "amount": 80
      }
    },
    {
      "key": "city_deck_card_10",
      "type": "card",
      "parent": "city_deck",
      "order": 10,
      "values": {
        "text": "Pay bridge maintenance",
        "operation": "debit",
        "amount": 45
      }
    },
    {
      "key": "city_deck_card_11",
      "type": "card",
      "parent": "city_deck",
      "order": 11,
      "values": {
        "text": "Local art prize",
        "operation": "credit",
        "amount": 150
      }
    },
    {
      "key": "bank",
      "type": "inventory",
      "parent": "root",
      "values": {
        "balance": 1000000
      }
    }
  ],
  "links": [
    {
      "source": "start",
      "target": "lot1",
      "relation": "next",
      "order": 0
    },
    {
      "source": "lot1",
      "target": "event1",
      "relation": "next",
      "order": 0
    },
    {
      "source": "event1",
      "target": "lot2",
      "relation": "next",
      "order": 0
    },
    {
      "source": "lot2",
      "target": "tax1",
      "relation": "next",
      "order": 0
    },
    {
      "source": "tax1",
      "target": "rail1",
      "relation": "next",
      "order": 0
    },
    {
      "source": "rail1",
      "target": "lot3",
      "relation": "next",
      "order": 0
    },
    {
      "source": "lot3",
      "target": "event2",
      "relation": "next",
      "order": 0
    },
    {
      "source": "event2",
      "target": "lot4",
      "relation": "next",
      "order": 0
    },
    {
      "source": "lot4",
      "target": "lot5",
      "relation": "next",
      "order": 0
    },
    {
      "source": "lot5",
      "target": "rest1",
      "relation": "next",
      "order": 0
    },
    {
      "source": "rest1",
      "target": "lot6",
      "relation": "next",
      "order": 0
    },
    {
      "source": "lot6",
      "target": "util1",
      "relation": "next",
      "order": 0
    },
    {
      "source": "util1",
      "target": "lot7",
      "relation": "next",
      "order": 0
    },
    {
      "source": "lot7",
      "target": "lot8",
      "relation": "next",
      "order": 0
    },
    {
      "source": "lot8",
      "target": "rail2",
      "relation": "next",
      "order": 0
    },
    {
      "source": "rail2",
      "target": "lot9",
      "relation": "next",
      "order": 0
    },
    {
      "source": "lot9",
      "target": "event3",
      "relation": "next",
      "order": 0
    },
    {
      "source": "event3",
      "target": "lot10",
      "relation": "next",
      "order": 0
    },
    {
      "source": "lot10",
      "target": "lot11",
      "relation": "next",
      "order": 0
    },
    {
      "source": "lot11",
      "target": "break1",
      "relation": "next",
      "order": 0
    },
    {
      "source": "break1",
      "target": "lot12",
      "relation": "next",
      "order": 0
    },
    {
      "source": "lot12",
      "target": "event4",
      "relation": "next",
      "order": 0
    },
    {
      "source": "event4",
      "target": "lot13",
      "relation": "next",
      "order": 0
    },
    {
      "source": "lot13",
      "target": "lot14",
      "relation": "next",
      "order": 0
    },
    {
      "source": "lot14",
      "target": "rail3",
      "relation": "next",
      "order": 0
    },
    {
      "source": "rail3",
      "target": "lot15",
      "relation": "next",
      "order": 0
    },
    {
      "source": "lot15",
      "target": "lot16",
      "relation": "next",
      "order": 0
    },
    {
      "source": "lot16",
      "target": "util2",
      "relation": "next",
      "order": 0
    },
    {
      "source": "util2",
      "target": "lot17",
      "relation": "next",
      "order": 0
    },
    {
      "source": "lot17",
      "target": "goto",
      "relation": "next",
      "order": 0
    },
    {
      "source": "goto",
      "target": "lot18",
      "relation": "next",
      "order": 0
    },
    {
      "source": "lot18",
      "target": "lot19",
      "relation": "next",
      "order": 0
    },
    {
      "source": "lot19",
      "target": "event5",
      "relation": "next",
      "order": 0
    },
    {
      "source": "event5",
      "target": "lot20",
      "relation": "next",
      "order": 0
    },
    {
      "source": "lot20",
      "target": "rail4",
      "relation": "next",
      "order": 0
    },
    {
      "source": "rail4",
      "target": "event6",
      "relation": "next",
      "order": 0
    },
    {
      "source": "event6",
      "target": "lot21",
      "relation": "next",
      "order": 0
    },
    {
      "source": "lot21",
      "target": "tax2",
      "relation": "next",
      "order": 0
    },
    {
      "source": "tax2",
      "target": "lot22",
      "relation": "next",
      "order": 0
    },
    {
      "source": "lot22",
      "target": "start",
      "relation": "next",
      "order": 0
    },
    {
      "source": "event1",
      "target": "city_deck",
      "relation": "draws_from"
    },
    {
      "source": "event3",
      "target": "city_deck",
      "relation": "draws_from"
    },
    {
      "source": "event5",
      "target": "city_deck",
      "relation": "draws_from"
    }
  ],
  "fields": [
    {
      "entity": "lot",
      "key": "name",
      "type": "text",
      "default": ""
    },
    {
      "entity": "lot",
      "key": "location_kind",
      "type": "text",
      "default": ""
    },
    {
      "entity": "lot",
      "key": "group",
      "type": "text",
      "default": ""
    },
    {
      "entity": "lot",
      "key": "price",
      "type": "int",
      "default": 0
    },
    {
      "entity": "lot",
      "key": "base_rent",
      "type": "int",
      "default": 0
    },
    {
      "entity": "lot",
      "key": "build_cost",
      "type": "int",
      "default": 0
    },
    {
      "entity": "lot",
      "key": "mortgage_value",
      "type": "int",
      "default": 0
    },
    {
      "entity": "lot",
      "key": "houses",
      "type": "int",
      "default": 0
    },
    {
      "entity": "lot",
      "key": "mortgaged",
      "type": "bool",
      "default": false
    },
    {
      "entity": "property",
      "key": "price",
      "type": "int",
      "default": 0
    },
    {
      "entity": "property",
      "key": "base_rent",
      "type": "int",
      "default": 0
    },
    {
      "entity": "property",
      "key": "houses",
      "type": "int",
      "default": 0
    },
    {
      "entity": "property",
      "key": "mortgaged",
      "type": "bool",
      "default": false
    },
    {
      "entity": "transit",
      "key": "price",
      "type": "int",
      "default": 0
    },
    {
      "entity": "transit",
      "key": "base_rent",
      "type": "int",
      "default": 0
    },
    {
      "entity": "transit",
      "key": "houses",
      "type": "int",
      "default": 0
    },
    {
      "entity": "transit",
      "key": "mortgaged",
      "type": "bool",
      "default": false
    },
    {
      "entity": "utility",
      "key": "price",
      "type": "int",
      "default": 0
    },
    {
      "entity": "utility",
      "key": "base_rent",
      "type": "int",
      "default": 0
    },
    {
      "entity": "utility",
      "key": "houses",
      "type": "int",
      "default": 0
    },
    {
      "entity": "utility",
      "key": "mortgaged",
      "type": "bool",
      "default": false
    },
    {
      "entity": "token",
      "key": "detained",
      "type": "bool",
      "default": false
    },
    {
      "entity": "token",
      "key": "doubles",
      "type": "int",
      "default": 0
    },
    {
      "entity": "inventory",
      "key": "balance",
      "type": "int",
      "default": 1500
    },
    {
      "entity": "card",
      "key": "text",
      "type": "text",
      "default": ""
    },
    {
      "entity": "card",
      "key": "operation",
      "type": "text",
      "default": ""
    },
    {
      "entity": "card",
      "key": "amount",
      "type": "int",
      "default": 0
    },
    {
      "entity": "bankruptcy",
      "key": "completed",
      "type": "bool",
      "default": false
    },
    {
      "entity": "bankruptcy",
      "key": "progress",
      "type": "int",
      "default": 0
    },
    {
      "entity": "last_solvent",
      "key": "completed",
      "type": "bool",
      "default": false
    },
    {
      "entity": "last_solvent",
      "key": "progress",
      "type": "int",
      "default": 0
    },
    {
      "entity": "wealth_quest",
      "key": "completed",
      "type": "bool",
      "default": false
    },
    {
      "entity": "wealth_quest",
      "key": "progress",
      "type": "int",
      "default": 0
    },
    {
      "entity": "game",
      "key": "current_roll",
      "type": "int",
      "default": 0
    },
    {
      "entity": "game",
      "key": "pending_auction",
      "type": "bool",
      "default": false
    },
    {
      "entity": "game",
      "key": "round",
      "type": "int",
      "default": 0
    },
    {
      "entity": "game",
      "key": "outcome",
      "type": "text",
      "default": ""
    },
    {
      "entity": "property",
      "key": "build_cost",
      "type": "int",
      "default": 50
    },
    {
      "entity": "transit",
      "key": "build_cost",
      "type": "int",
      "default": 50
    },
    {
      "entity": "utility",
      "key": "build_cost",
      "type": "int",
      "default": 50
    },
    {
      "entity": "property",
      "key": "mortgage_value",
      "type": "int",
      "default": 0
    },
    {
      "entity": "transit",
      "key": "mortgage_value",
      "type": "int",
      "default": 0
    },
    {
      "entity": "utility",
      "key": "mortgage_value",
      "type": "int",
      "default": 0
    },
    {
      "entity": "property",
      "key": "group",
      "type": "text",
      "default": ""
    },
    {
      "entity": "transit",
      "key": "group",
      "type": "text",
      "default": ""
    },
    {
      "entity": "utility",
      "key": "group",
      "type": "text",
      "default": ""
    },
    {
      "entity": "lot",
      "key": "fee",
      "type": "int",
      "default": 0
    },
    {
      "entity": "token",
      "key": "detention_attempts",
      "type": "int",
      "default": 0
    }
  ],
  "actions": [
    {
      "key": "begin_turn",
      "entity": "game",
      "trigger": "hook",
      "hook": "phase.enter",
      "phase": "turn_start",
      "condition": {
        "op": "literal",
        "value": true
      },
      "effects": [
        {
          "op": "set_phase",
          "args": {
            "phase": {
              "op": "literal",
              "value": "roll"
            }
          }
        }
      ],
      "priority": 0
    },
    {
      "key": "roll",
      "entity": "game",
      "trigger": "command",
      "phase": "roll",
      "condition": {
        "op": "and",
        "args": {
          "values": [
            {
              "op": "and",
              "args": {
                "values": [
                  {
                    "op": "is_active",
                    "args": {
                      "participant": {
                        "op": "context",
                        "ref": "actor"
                      }
                    }
                  },
                  {
                    "op": "phase_is",
                    "args": {
                      "phase": {
                        "op": "literal",
                        "value": "roll"
                      }
                    }
                  }
                ]
              }
            },
            {
              "op": "not",
              "args": {
                "value": {
                  "op": "field",
                  "args": {
                    "entity": {
                      "op": "entity_owned_by",
                      "args": {
                        "participant": {
                          "op": "context",
                          "ref": "actor"
                        },
                        "entity_type": {
                          "op": "literal",
                          "value": "token"
                        }
                      }
                    },
                    "key": {
                      "op": "literal",
                      "value": "detained"
                    }
                  }
                }
              }
            }
          ]
        }
      },
      "effects": [
        {
          "op": "trusted_random_int",
          "args": {
            "name": {
              "op": "literal",
              "value": "die1"
            },
            "lower": {
              "op": "literal",
              "value": 1
            },
            "upper": {
              "op": "literal",
              "value": 6
            }
          }
        },
        {
          "op": "trusted_random_int",
          "args": {
            "name": {
              "op": "literal",
              "value": "die2"
            },
            "lower": {
              "op": "literal",
              "value": 1
            },
            "upper": {
              "op": "literal",
              "value": 6
            }
          }
        },
        {
          "op": "set_field",
          "args": {
            "entity": {
              "op": "context",
              "ref": "self"
            },
            "field": {
              "op": "literal",
              "value": "current_roll"
            },
            "value": {
              "op": "add",
              "args": {
                "a": {
                  "op": "context",
                  "ref": "random.die1"
                },
                "b": {
                  "op": "context",
                  "ref": "random.die2"
                }
              }
            }
          }
        },
        {
          "op": "set_field",
          "args": {
            "entity": {
              "op": "entity_owned_by",
              "args": {
                "participant": {
                  "op": "context",
                  "ref": "actor"
                },
                "entity_type": {
                  "op": "literal",
                  "value": "token"
                }
              }
            },
            "field": {
              "op": "literal",
              "value": "doubles"
            },
            "value": {
              "op": "if",
              "args": {
                "condition": {
                  "op": "eq",
                  "args": {
                    "a": {
                      "op": "context",
                      "ref": "random.die1"
                    },
                    "b": {
                      "op": "context",
                      "ref": "random.die2"
                    }
                  }
                },
                "then": {
                  "op": "add",
                  "args": {
                    "a": {
                      "op": "field",
                      "args": {
                        "entity": {
                          "op": "entity_owned_by",
                          "args": {
                            "participant": {
                              "op": "context",
                              "ref": "actor"
                            },
                            "entity_type": {
                              "op": "literal",
                              "value": "token"
                            }
                          }
                        },
                        "key": {
                          "op": "literal",
                          "value": "doubles"
                        }
                      }
                    },
                    "b": {
                      "op": "literal",
                      "value": 1
                    }
                  }
                },
                "otherwise": {
                  "op": "literal",
                  "value": 0
                }
              }
            }
          }
        },
        {
          "op": "set_phase",
          "args": {
            "phase": {
              "op": "if",
              "args": {
                "condition": {
                  "op": "gte",
                  "args": {
                    "a": {
                      "op": "field",
                      "args": {
                        "entity": {
                          "op": "entity_owned_by",
                          "args": {
                            "participant": {
                              "op": "context",
                              "ref": "actor"
                            },
                            "entity_type": {
                              "op": "literal",
                              "value": "token"
                            }
                          }
                        },
                        "key": {
                          "op": "literal",
                          "value": "doubles"
                        }
                      }
                    },
                    "b": {
                      "op": "literal",
                      "value": 3
                    }
                  }
                },
                "then": {
                  "op": "literal",
                  "value": "management"
                },
                "otherwise": {
                  "op": "literal",
                  "value": "move"
                }
              }
            }
          }
        },
        {
          "op": "move_entity",
          "when": {
            "op": "gte",
            "args": {
              "a": {
                "op": "field",
                "args": {
                  "entity": {
                    "op": "entity_owned_by",
                    "args": {
                      "participant": {
                        "op": "context",
                        "ref": "actor"
                      },
                      "entity_type": {
                        "op": "literal",
                        "value": "token"
                      }
                    }
                  },
                  "key": {
                    "op": "literal",
                    "value": "doubles"
                  }
                }
              },
              "b": {
                "op": "literal",
                "value": 3
              }
            }
          },
          "args": {
            "entity": {
              "op": "entity_owned_by",
              "args": {
                "participant": {
                  "op": "context",
                  "ref": "actor"
                },
                "entity_type": {
                  "op": "literal",
                  "value": "token"
                }
              }
            },
            "destination": {
              "op": "entity_by_seed",
              "args": {
                "key": {
                  "op": "literal",
                  "value": "rest1"
                }
              }
            }
          }
        },
        {
          "op": "set_field",
          "when": {
            "op": "gte",
            "args": {
              "a": {
                "op": "field",
                "args": {
                  "entity": {
                    "op": "entity_owned_by",
                    "args": {
                      "participant": {
                        "op": "context",
                        "ref": "actor"
                      },
                      "entity_type": {
                        "op": "literal",
                        "value": "token"
                      }
                    }
                  },
                  "key": {
                    "op": "literal",
                    "value": "doubles"
                  }
                }
              },
              "b": {
                "op": "literal",
                "value": 3
              }
            }
          },
          "args": {
            "entity": {
              "op": "entity_owned_by",
              "args": {
                "participant": {
                  "op": "context",
                  "ref": "actor"
                },
                "entity_type": {
                  "op": "literal",
                  "value": "token"
                }
              }
            },
            "field": {
              "op": "literal",
              "value": "detained"
            },
            "value": {
              "op": "literal",
              "value": true
            }
          }
        },
        {
          "op": "set_field",
          "when": {
            "op": "gte",
            "args": {
              "a": {
                "op": "field",
                "args": {
                  "entity": {
                    "op": "entity_owned_by",
                    "args": {
                      "participant": {
                        "op": "context",
                        "ref": "actor"
                      },
                      "entity_type": {
                        "op": "literal",
                        "value": "token"
                      }
                    }
                  },
                  "key": {
                    "op": "literal",
                    "value": "doubles"
                  }
                }
              },
              "b": {
                "op": "literal",
                "value": 3
              }
            }
          },
          "args": {
            "entity": {
              "op": "entity_owned_by",
              "args": {
                "participant": {
                  "op": "context",
                  "ref": "actor"
                },
                "entity_type": {
                  "op": "literal",
                  "value": "token"
                }
              }
            },
            "field": {
              "op": "literal",
              "value": "detention_attempts"
            },
            "value": {
              "op": "literal",
              "value": 0
            }
          }
        },
        {
          "op": "set_field",
          "when": {
            "op": "gte",
            "args": {
              "a": {
                "op": "field",
                "args": {
                  "entity": {
                    "op": "entity_owned_by",
                    "args": {
                      "participant": {
                        "op": "context",
                        "ref": "actor"
                      },
                      "entity_type": {
                        "op": "literal",
                        "value": "token"
                      }
                    }
                  },
                  "key": {
                    "op": "literal",
                    "value": "doubles"
                  }
                }
              },
              "b": {
                "op": "literal",
                "value": 3
              }
            }
          },
          "args": {
            "entity": {
              "op": "entity_owned_by",
              "args": {
                "participant": {
                  "op": "context",
                  "ref": "actor"
                },
                "entity_type": {
                  "op": "literal",
                  "value": "token"
                }
              }
            },
            "field": {
              "op": "literal",
              "value": "doubles"
            },
            "value": {
              "op": "literal",
              "value": 0
            }
          }
        }
      ],
      "priority": 0
    },
    {
      "key": "move",
      "entity": "token",
      "trigger": "hook",
      "phase": "move",
      "condition": {
        "op": "and",
        "args": {
          "values": [
            {
              "op": "phase_is",
              "args": {
                "phase": {
                  "op": "literal",
                  "value": "move"
                }
              }
            },
            {
              "op": "eq",
              "args": {
                "a": {
                  "op": "owner",
                  "args": {
                    "entity": {
                      "op": "context",
                      "ref": "self"
                    }
                  }
                },
                "b": {
                  "op": "context",
                  "ref": "active_participant"
                }
              }
            }
          ]
        }
      },
      "effects": [
        {
          "op": "move_entity",
          "args": {
            "entity": {
              "op": "context",
              "ref": "self"
            },
            "destination": {
              "op": "path_last",
              "args": {
                "path": {
                  "op": "track_advance",
                  "args": {
                    "entity": {
                      "op": "context",
                      "ref": "self"
                    },
                    "steps": {
                      "op": "field",
                      "args": {
                        "entity": {
                          "op": "context",
                          "ref": "game"
                        },
                        "key": {
                          "op": "literal",
                          "value": "current_roll"
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        },
        {
          "op": "emit_traversal_events",
          "args": {
            "entity": {
              "op": "context",
              "ref": "self"
            },
            "steps": {
              "op": "field",
              "args": {
                "entity": {
                  "op": "context",
                  "ref": "game"
                },
                "key": {
                  "op": "literal",
                  "value": "current_roll"
                }
              }
            },
            "hook": {
              "op": "literal",
              "value": "space.passed"
            }
          }
        },
        {
          "op": "set_phase",
          "args": {
            "phase": {
              "op": "literal",
              "value": "resolve"
            }
          }
        }
      ],
      "priority": 0,
      "hook": "phase.enter"
    },
    {
      "key": "resolve_location",
      "entity": "lot",
      "trigger": "hook",
      "phase": "resolve",
      "condition": {
        "op": "entity_at",
        "args": {
          "entity": {
            "op": "context",
            "ref": "self"
          },
          "participant": {
            "op": "context",
            "ref": "active_participant"
          }
        }
      },
      "effects": [
        {
          "op": "emit_event",
          "args": {
            "name": {
              "op": "literal",
              "value": "space.landed"
            }
          }
        },
        {
          "op": "set_phase",
          "args": {
            "phase": {
              "op": "literal",
              "value": "decision"
            }
          }
        }
      ],
      "priority": 0,
      "hook": "phase.enter"
    },
    {
      "key": "buy",
      "entity": "property",
      "trigger": "command",
      "phase": "decision",
      "condition": {
        "op": "and",
        "args": {
          "values": [
            {
              "op": "and",
              "args": {
                "values": [
                  {
                    "op": "and",
                    "args": {
                      "values": [
                        {
                          "op": "eq",
                          "args": {
                            "a": {
                              "op": "owner",
                              "args": {
                                "entity": {
                                  "op": "context",
                                  "ref": "self"
                                }
                              }
                            },
                            "b": {
                              "op": "literal",
                              "value": null
                            }
                          }
                        },
                        {
                          "op": "gte",
                          "args": {
                            "a": {
                              "op": "field",
                              "args": {
                                "entity": {
                                  "op": "entity_owned_by",
                                  "args": {
                                    "participant": {
                                      "op": "context",
                                      "ref": "actor"
                                    },
                                    "entity_type": {
                                      "op": "literal",
                                      "value": "inventory"
                                    }
                                  }
                                },
                                "key": {
                                  "op": "literal",
                                  "value": "balance"
                                }
                              }
                            },
                            "b": {
                              "op": "field",
                              "args": {
                                "entity": {
                                  "op": "context",
                                  "ref": "self"
                                },
                                "key": {
                                  "op": "literal",
                                  "value": "price"
                                }
                              }
                            }
                          }
                        }
                      ]
                    }
                  },
                  {
                    "op": "eq",
                    "args": {
                      "a": {
                        "op": "entity_location",
                        "args": {
                          "entity": {
                            "op": "context",
                            "ref": "self"
                          }
                        }
                      },
                      "b": {
                        "op": "entity_location",
                        "args": {
                          "entity": {
                            "op": "entity_owned_by",
                            "args": {
                              "participant": {
                                "op": "context",
                                "ref": "actor"
                              },
                              "entity_type": {
                                "op": "literal",
                                "value": "token"
                              }
                            }
                          }
                        }
                      }
                    }
                  }
                ]
              }
            },
            {
              "op": "phase_is",
              "args": {
                "phase": {
                  "op": "literal",
                  "value": "decision"
                }
              }
            }
          ]
        }
      },
      "effects": [
        {
          "op": "transfer_resource",
          "args": {
            "source": {
              "op": "context",
              "ref": "actor"
            },
            "target": {
              "op": "context",
              "ref": "bank"
            },
            "amount": {
              "op": "field",
              "args": {
                "entity": {
                  "op": "context",
                  "ref": "self"
                },
                "key": {
                  "op": "literal",
                  "value": "price"
                }
              }
            }
          }
        },
        {
          "op": "set_owner",
          "args": {
            "entity": {
              "op": "context",
              "ref": "self"
            },
            "owner": {
              "op": "context",
              "ref": "actor"
            }
          }
        },
        {
          "op": "set_phase",
          "args": {
            "phase": {
              "op": "literal",
              "value": "management"
            }
          }
        }
      ],
      "priority": 0
    },
    {
      "key": "decline_purchase",
      "entity": "property",
      "trigger": "command",
      "phase": "decision",
      "condition": {
        "op": "and",
        "args": {
          "values": [
            {
              "op": "eq",
              "args": {
                "a": {
                  "op": "owner",
                  "args": {
                    "entity": {
                      "op": "context",
                      "ref": "self"
                    }
                  }
                },
                "b": {
                  "op": "literal",
                  "value": null
                }
              }
            },
            {
              "op": "eq",
              "args": {
                "a": {
                  "op": "entity_location",
                  "args": {
                    "entity": {
                      "op": "context",
                      "ref": "self"
                    }
                  }
                },
                "b": {
                  "op": "entity_location",
                  "args": {
                    "entity": {
                      "op": "entity_owned_by",
                      "args": {
                        "participant": {
                          "op": "context",
                          "ref": "actor"
                        },
                        "entity_type": {
                          "op": "literal",
                          "value": "token"
                        }
                      }
                    }
                  }
                }
              }
            }
          ]
        }
      },
      "effects": [
        {
          "op": "open_decision",
          "args": {
            "decision": {
              "op": "literal",
              "value": "auction"
            },
            "entity": {
              "op": "context",
              "ref": "self"
            }
          }
        },
        {
          "op": "set_phase",
          "args": {
            "phase": {
              "op": "literal",
              "value": "decision"
            }
          }
        }
      ],
      "priority": 0
    },
    {
      "key": "bid",
      "entity": "auction",
      "trigger": "command",
      "phase": "decision",
      "condition": {
        "op": "and",
        "args": {
          "values": [
            {
              "op": "decision_is_open",
              "args": {
                "decision": {
                  "op": "context",
                  "ref": "self"
                }
              }
            },
            {
              "op": "contains",
              "args": {
                "items": {
                  "op": "decision_eligible",
                  "args": {
                    "decision": {
                      "op": "context",
                      "ref": "self"
                    }
                  }
                },
                "value": {
                  "op": "context",
                  "ref": "actor"
                }
              }
            },
            {
              "op": "gte",
              "args": {
                "a": {
                  "op": "field",
                  "args": {
                    "entity": {
                      "op": "entity_owned_by",
                      "args": {
                        "participant": {
                          "op": "context",
                          "ref": "actor"
                        },
                        "entity_type": {
                          "op": "literal",
                          "value": "inventory"
                        }
                      }
                    },
                    "key": {
                      "op": "literal",
                      "value": "balance"
                    }
                  }
                },
                "b": {
                  "op": "context",
                  "ref": "argument.amount"
                }
              }
            },
            {
              "op": "gt",
              "args": {
                "a": {
                  "op": "context",
                  "ref": "argument.amount"
                },
                "b": {
                  "op": "maximum_or",
                  "args": {
                    "items": {
                      "op": "map",
                      "args": {
                        "items": {
                          "op": "decision_responses",
                          "args": {
                            "decision": {
                              "op": "context",
                              "ref": "self"
                            }
                          }
                        },
                        "variable": {
                          "op": "literal",
                          "value": "response"
                        },
                        "expression": {
                          "op": "record_field",
                          "args": {
                            "record": {
                              "op": "context",
                              "ref": "local.response"
                            },
                            "key": {
                              "op": "literal",
                              "value": "amount"
                            }
                          }
                        }
                      }
                    },
                    "default": {
                      "op": "literal",
                      "value": 0
                    }
                  }
                }
              }
            }
          ]
        }
      },
      "effects": [
        {
          "op": "record_decision",
          "args": {
            "entity": {
              "op": "context",
              "ref": "self"
            },
            "actor": {
              "op": "context",
              "ref": "actor"
            },
            "amount": {
              "op": "context",
              "ref": "argument.amount"
            }
          }
        }
      ],
      "priority": 0,
      "parameters": [
        {
          "key": "amount",
          "type": "int"
        }
      ]
    },
    {
      "key": "resolve_auction",
      "entity": "auction",
      "trigger": "hook",
      "phase": "decision",
      "condition": {
        "op": "and",
        "args": {
          "values": [
            {
              "op": "decision_is_open",
              "args": {
                "decision": {
                  "op": "context",
                  "ref": "self"
                }
              }
            },
            {
              "op": "eq",
              "args": {
                "a": {
                  "op": "count",
                  "args": {
                    "items": {
                      "op": "decision_responses",
                      "args": {
                        "decision": {
                          "op": "context",
                          "ref": "self"
                        }
                      }
                    }
                  }
                },
                "b": {
                  "op": "count",
                  "args": {
                    "items": {
                      "op": "decision_eligible",
                      "args": {
                        "decision": {
                          "op": "context",
                          "ref": "self"
                        }
                      }
                    }
                  }
                }
              }
            }
          ]
        }
      },
      "effects": [
        {
          "op": "resolve_decision",
          "args": {
            "entity": {
              "op": "context",
              "ref": "self"
            }
          }
        },
        {
          "op": "transfer_resource",
          "when": {
            "op": "is_present",
            "args": {
              "value": {
                "op": "best_by",
                "args": {
                  "items": {
                    "op": "decision_responses",
                    "args": {
                      "decision": {
                        "op": "context",
                        "ref": "self"
                      }
                    }
                  },
                  "field": {
                    "op": "literal",
                    "value": "amount"
                  },
                  "order": {
                    "op": "literal",
                    "value": "descending"
                  }
                }
              }
            }
          },
          "args": {
            "source": {
              "op": "record_field",
              "args": {
                "record": {
                  "op": "best_by",
                  "args": {
                    "items": {
                      "op": "decision_responses",
                      "args": {
                        "decision": {
                          "op": "context",
                          "ref": "self"
                        }
                      }
                    },
                    "field": {
                      "op": "literal",
                      "value": "amount"
                    },
                    "order": {
                      "op": "literal",
                      "value": "descending"
                    }
                  }
                },
                "key": {
                  "op": "literal",
                  "value": "participant"
                }
              }
            },
            "target": {
              "op": "context",
              "ref": "bank"
            },
            "amount": {
              "op": "record_field",
              "args": {
                "record": {
                  "op": "best_by",
                  "args": {
                    "items": {
                      "op": "decision_responses",
                      "args": {
                        "decision": {
                          "op": "context",
                          "ref": "self"
                        }
                      }
                    },
                    "field": {
                      "op": "literal",
                      "value": "amount"
                    },
                    "order": {
                      "op": "literal",
                      "value": "descending"
                    }
                  }
                },
                "key": {
                  "op": "literal",
                  "value": "amount"
                }
              }
            }
          }
        },
        {
          "op": "set_owner",
          "when": {
            "op": "is_present",
            "args": {
              "value": {
                "op": "best_by",
                "args": {
                  "items": {
                    "op": "decision_responses",
                    "args": {
                      "decision": {
                        "op": "context",
                        "ref": "self"
                      }
                    }
                  },
                  "field": {
                    "op": "literal",
                    "value": "amount"
                  },
                  "order": {
                    "op": "literal",
                    "value": "descending"
                  }
                }
              }
            }
          },
          "args": {
            "entity": {
              "op": "decision_subject",
              "args": {
                "decision": {
                  "op": "context",
                  "ref": "self"
                }
              }
            },
            "owner": {
              "op": "record_field",
              "args": {
                "record": {
                  "op": "best_by",
                  "args": {
                    "items": {
                      "op": "decision_responses",
                      "args": {
                        "decision": {
                          "op": "context",
                          "ref": "self"
                        }
                      }
                    },
                    "field": {
                      "op": "literal",
                      "value": "amount"
                    },
                    "order": {
                      "op": "literal",
                      "value": "descending"
                    }
                  }
                },
                "key": {
                  "op": "literal",
                  "value": "participant"
                }
              }
            }
          }
        },
        {
          "op": "set_phase",
          "args": {
            "phase": {
              "op": "literal",
              "value": "management"
            }
          }
        }
      ],
      "priority": 0,
      "hook": "decision.resolved"
    },
    {
      "key": "charge_rent",
      "entity": "property",
      "trigger": "hook",
      "phase": "resolve",
      "condition": {
        "op": "and",
        "args": {
          "values": [
            {
              "op": "and",
              "args": {
                "values": [
                  {
                    "op": "not",
                    "args": {
                      "value": {
                        "op": "eq",
                        "args": {
                          "a": {
                            "op": "owner",
                            "args": {
                              "entity": {
                                "op": "context",
                                "ref": "self"
                              }
                            }
                          },
                          "b": {
                            "op": "literal",
                            "value": null
                          }
                        }
                      }
                    }
                  },
                  {
                    "op": "not",
                    "args": {
                      "value": {
                        "op": "eq",
                        "args": {
                          "a": {
                            "op": "owner",
                            "args": {
                              "entity": {
                                "op": "context",
                                "ref": "self"
                              }
                            }
                          },
                          "b": {
                            "op": "context",
                            "ref": "active_participant"
                          }
                        }
                      }
                    }
                  }
                ]
              }
            },
            {
              "op": "eq",
              "args": {
                "a": {
                  "op": "entity_location",
                  "args": {
                    "entity": {
                      "op": "context",
                      "ref": "self"
                    }
                  }
                },
                "b": {
                  "op": "entity_location",
                  "args": {
                    "entity": {
                      "op": "entity_owned_by",
                      "args": {
                        "participant": {
                          "op": "context",
                          "ref": "active_participant"
                        },
                        "entity_type": {
                          "op": "literal",
                          "value": "token"
                        }
                      }
                    }
                  }
                }
              }
            }
          ]
        }
      },
      "effects": [
        {
          "op": "transfer_resource",
          "args": {
            "source": {
              "op": "context",
              "ref": "active_participant"
            },
            "target": {
              "op": "owner",
              "args": {
                "entity": {
                  "op": "context",
                  "ref": "self"
                }
              }
            },
            "amount": {
              "op": "multiply",
              "args": {
                "a": {
                  "op": "field",
                  "args": {
                    "entity": {
                      "op": "context",
                      "ref": "self"
                    },
                    "key": {
                      "op": "literal",
                      "value": "base_rent"
                    }
                  }
                },
                "b": {
                  "op": "add",
                  "args": {
                    "a": {
                      "op": "literal",
                      "value": 1
                    },
                    "b": {
                      "op": "field",
                      "args": {
                        "entity": {
                          "op": "context",
                          "ref": "self"
                        },
                        "key": {
                          "op": "literal",
                          "value": "houses"
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      ],
      "priority": 0,
      "hook": "space.landed"
    },
    {
      "key": "mortgage",
      "entity": "property",
      "trigger": "command",
      "phase": "management",
      "condition": {
        "op": "and",
        "args": {
          "values": [
            {
              "op": "eq",
              "args": {
                "a": {
                  "op": "owner",
                  "args": {
                    "entity": {
                      "op": "context",
                      "ref": "self"
                    }
                  }
                },
                "b": {
                  "op": "context",
                  "ref": "actor"
                }
              }
            },
            {
              "op": "not",
              "args": {
                "value": {
                  "op": "field",
                  "args": {
                    "entity": {
                      "op": "context",
                      "ref": "self"
                    },
                    "key": {
                      "op": "literal",
                      "value": "mortgaged"
                    }
                  }
                }
              }
            },
            {
              "op": "eq",
              "args": {
                "a": {
                  "op": "field",
                  "args": {
                    "entity": {
                      "op": "context",
                      "ref": "self"
                    },
                    "key": {
                      "op": "literal",
                      "value": "houses"
                    }
                  }
                },
                "b": {
                  "op": "literal",
                  "value": 0
                }
              }
            }
          ]
        }
      },
      "effects": [
        {
          "op": "set_field",
          "args": {
            "entity": {
              "op": "context",
              "ref": "self"
            },
            "field": {
              "op": "literal",
              "value": "mortgaged"
            },
            "value": {
              "op": "literal",
              "value": true
            }
          }
        },
        {
          "op": "credit_resource",
          "args": {
            "participant": {
              "op": "context",
              "ref": "actor"
            },
            "amount": {
              "op": "field",
              "args": {
                "entity": {
                  "op": "context",
                  "ref": "self"
                },
                "key": {
                  "op": "literal",
                  "value": "mortgage_value"
                }
              }
            }
          }
        }
      ],
      "priority": 0
    },
    {
      "key": "unmortgage",
      "entity": "property",
      "trigger": "command",
      "phase": "management",
      "condition": {
        "op": "and",
        "args": {
          "values": [
            {
              "op": "eq",
              "args": {
                "a": {
                  "op": "owner",
                  "args": {
                    "entity": {
                      "op": "context",
                      "ref": "self"
                    }
                  }
                },
                "b": {
                  "op": "context",
                  "ref": "actor"
                }
              }
            },
            {
              "op": "field",
              "args": {
                "entity": {
                  "op": "context",
                  "ref": "self"
                },
                "key": {
                  "op": "literal",
                  "value": "mortgaged"
                }
              }
            },
            {
              "op": "gte",
              "args": {
                "a": {
                  "op": "field",
                  "args": {
                    "entity": {
                      "op": "entity_owned_by",
                      "args": {
                        "participant": {
                          "op": "context",
                          "ref": "actor"
                        },
                        "entity_type": {
                          "op": "literal",
                          "value": "inventory"
                        }
                      }
                    },
                    "key": {
                      "op": "literal",
                      "value": "balance"
                    }
                  }
                },
                "b": {
                  "op": "floor_divide",
                  "args": {
                    "a": {
                      "op": "add",
                      "args": {
                        "a": {
                          "op": "multiply",
                          "args": {
                            "a": {
                              "op": "field",
                              "args": {
                                "entity": {
                                  "op": "context",
                                  "ref": "self"
                                },
                                "key": {
                                  "op": "literal",
                                  "value": "mortgage_value"
                                }
                              }
                            },
                            "b": {
                              "op": "literal",
                              "value": 110
                            }
                          }
                        },
                        "b": {
                          "op": "literal",
                          "value": 99
                        }
                      }
                    },
                    "b": {
                      "op": "literal",
                      "value": 100
                    }
                  }
                }
              }
            }
          ]
        }
      },
      "effects": [
        {
          "op": "debit_resource",
          "args": {
            "participant": {
              "op": "context",
              "ref": "actor"
            },
            "amount": {
              "op": "floor_divide",
              "args": {
                "a": {
                  "op": "add",
                  "args": {
                    "a": {
                      "op": "multiply",
                      "args": {
                        "a": {
                          "op": "field",
                          "args": {
                            "entity": {
                              "op": "context",
                              "ref": "self"
                            },
                            "key": {
                              "op": "literal",
                              "value": "mortgage_value"
                            }
                          }
                        },
                        "b": {
                          "op": "literal",
                          "value": 110
                        }
                      }
                    },
                    "b": {
                      "op": "literal",
                      "value": 99
                    }
                  }
                },
                "b": {
                  "op": "literal",
                  "value": 100
                }
              }
            }
          }
        },
        {
          "op": "set_field",
          "args": {
            "entity": {
              "op": "context",
              "ref": "self"
            },
            "field": {
              "op": "literal",
              "value": "mortgaged"
            },
            "value": {
              "op": "literal",
              "value": false
            }
          }
        }
      ],
      "priority": 0
    },
    {
      "key": "build",
      "entity": "property",
      "trigger": "command",
      "phase": "management",
      "condition": {
        "op": "and",
        "args": {
          "values": [
            {
              "op": "eq",
              "args": {
                "a": {
                  "op": "owner",
                  "args": {
                    "entity": {
                      "op": "context",
                      "ref": "self"
                    }
                  }
                },
                "b": {
                  "op": "context",
                  "ref": "actor"
                }
              }
            },
            {
              "op": "not",
              "args": {
                "value": {
                  "op": "field",
                  "args": {
                    "entity": {
                      "op": "context",
                      "ref": "self"
                    },
                    "key": {
                      "op": "literal",
                      "value": "mortgaged"
                    }
                  }
                }
              }
            },
            {
              "op": "lt",
              "args": {
                "a": {
                  "op": "field",
                  "args": {
                    "entity": {
                      "op": "context",
                      "ref": "self"
                    },
                    "key": {
                      "op": "literal",
                      "value": "houses"
                    }
                  }
                },
                "b": {
                  "op": "literal",
                  "value": 5
                }
              }
            },
            {
              "op": "gte",
              "args": {
                "a": {
                  "op": "field",
                  "args": {
                    "entity": {
                      "op": "entity_owned_by",
                      "args": {
                        "participant": {
                          "op": "context",
                          "ref": "actor"
                        },
                        "entity_type": {
                          "op": "literal",
                          "value": "inventory"
                        }
                      }
                    },
                    "key": {
                      "op": "literal",
                      "value": "balance"
                    }
                  }
                },
                "b": {
                  "op": "field",
                  "args": {
                    "entity": {
                      "op": "context",
                      "ref": "self"
                    },
                    "key": {
                      "op": "literal",
                      "value": "build_cost"
                    }
                  }
                }
              }
            }
          ]
        }
      },
      "effects": [
        {
          "op": "debit_resource",
          "args": {
            "participant": {
              "op": "context",
              "ref": "actor"
            },
            "amount": {
              "op": "field",
              "args": {
                "entity": {
                  "op": "context",
                  "ref": "self"
                },
                "key": {
                  "op": "literal",
                  "value": "build_cost"
                }
              }
            }
          }
        },
        {
          "op": "increment_field",
          "args": {
            "entity": {
              "op": "context",
              "ref": "self"
            },
            "field": {
              "op": "literal",
              "value": "houses"
            },
            "amount": {
              "op": "literal",
              "value": 1
            }
          }
        }
      ],
      "priority": 0
    },
    {
      "key": "sell_building",
      "entity": "property",
      "trigger": "command",
      "phase": "management",
      "condition": {
        "op": "and",
        "args": {
          "values": [
            {
              "op": "eq",
              "args": {
                "a": {
                  "op": "owner",
                  "args": {
                    "entity": {
                      "op": "context",
                      "ref": "self"
                    }
                  }
                },
                "b": {
                  "op": "context",
                  "ref": "actor"
                }
              }
            },
            {
              "op": "gt",
              "args": {
                "a": {
                  "op": "field",
                  "args": {
                    "entity": {
                      "op": "context",
                      "ref": "self"
                    },
                    "key": {
                      "op": "literal",
                      "value": "houses"
                    }
                  }
                },
                "b": {
                  "op": "literal",
                  "value": 0
                }
              }
            }
          ]
        }
      },
      "effects": [
        {
          "op": "increment_field",
          "args": {
            "entity": {
              "op": "context",
              "ref": "self"
            },
            "field": {
              "op": "literal",
              "value": "houses"
            },
            "amount": {
              "op": "literal",
              "value": -1
            }
          }
        },
        {
          "op": "credit_resource",
          "args": {
            "participant": {
              "op": "context",
              "ref": "actor"
            },
            "amount": {
              "op": "floor_divide",
              "args": {
                "a": {
                  "op": "field",
                  "args": {
                    "entity": {
                      "op": "context",
                      "ref": "self"
                    },
                    "key": {
                      "op": "literal",
                      "value": "build_cost"
                    }
                  }
                },
                "b": {
                  "op": "literal",
                  "value": 2
                }
              }
            }
          }
        }
      ],
      "priority": 0
    },
    {
      "key": "draw",
      "entity": "deck",
      "trigger": "hook",
      "phase": "resolve",
      "condition": {
        "op": "has_relation",
        "args": {
          "source": {
            "op": "context",
            "ref": "location"
          },
          "target": {
            "op": "context",
            "ref": "self"
          },
          "relation": {
            "op": "literal",
            "value": "draws_from"
          }
        }
      },
      "effects": [
        {
          "op": "draw_collection_item",
          "args": {
            "deck": {
              "op": "context",
              "ref": "self"
            }
          }
        },
        {
          "op": "emit_event",
          "args": {
            "name": {
              "op": "literal",
              "value": "card.drawn"
            },
            "entity": {
              "op": "context",
              "ref": "drawn_card"
            }
          }
        }
      ],
      "priority": 0,
      "hook": "space.landed"
    },
    {
      "key": "propose_trade",
      "entity": "trade_offer",
      "trigger": "command",
      "phase": "management",
      "condition": {
        "op": "transfer_plan_valid",
        "args": {
          "plan": {
            "op": "context",
            "ref": "argument.offer"
          },
          "state": {
            "op": "context",
            "ref": "observed_state"
          }
        }
      },
      "effects": [
        {
          "op": "create_entity",
          "args": {
            "type": {
              "op": "literal",
              "value": "trade_offer"
            },
            "fields": {
              "op": "context",
              "ref": "argument.offer"
            }
          }
        },
        {
          "op": "open_decision",
          "args": {
            "decision": {
              "op": "literal",
              "value": "trade"
            },
            "entity": {
              "op": "context",
              "ref": "created_entity"
            }
          }
        }
      ],
      "priority": 0,
      "parameters": [
        {
          "key": "offer",
          "type": "record"
        }
      ]
    },
    {
      "key": "accept_trade",
      "entity": "trade_offer",
      "trigger": "command",
      "phase": "decision",
      "condition": {
        "op": "and",
        "args": {
          "values": [
            {
              "op": "and",
              "args": {
                "values": [
                  {
                    "op": "decision_is_open",
                    "args": {
                      "decision": {
                        "op": "context",
                        "ref": "self"
                      }
                    }
                  },
                  {
                    "op": "contains",
                    "args": {
                      "items": {
                        "op": "decision_eligible",
                        "args": {
                          "decision": {
                            "op": "context",
                            "ref": "self"
                          }
                        }
                      },
                      "value": {
                        "op": "context",
                        "ref": "actor"
                      }
                    }
                  }
                ]
              }
            },
            {
              "op": "transfer_plan_valid",
              "args": {
                "plan": {
                  "op": "decision_payload",
                  "args": {
                    "decision": {
                      "op": "context",
                      "ref": "self"
                    }
                  }
                },
                "state": {
                  "op": "context",
                  "ref": "observed_state"
                }
              }
            }
          ]
        }
      },
      "effects": [
        {
          "op": "execute_transfer_plan",
          "args": {
            "plan": {
              "op": "decision_payload",
              "args": {
                "decision": {
                  "op": "context",
                  "ref": "self"
                }
              }
            }
          }
        },
        {
          "op": "resolve_decision",
          "args": {
            "entity": {
              "op": "context",
              "ref": "self"
            }
          }
        }
      ],
      "priority": 0
    },
    {
      "key": "reject_trade",
      "entity": "trade_offer",
      "trigger": "command",
      "phase": "decision",
      "condition": {
        "op": "and",
        "args": {
          "values": [
            {
              "op": "decision_is_open",
              "args": {
                "decision": {
                  "op": "context",
                  "ref": "self"
                }
              }
            },
            {
              "op": "contains",
              "args": {
                "items": {
                  "op": "decision_eligible",
                  "args": {
                    "decision": {
                      "op": "context",
                      "ref": "self"
                    }
                  }
                },
                "value": {
                  "op": "context",
                  "ref": "actor"
                }
              }
            }
          ]
        }
      },
      "effects": [
        {
          "op": "resolve_decision",
          "args": {
            "entity": {
              "op": "context",
              "ref": "self"
            }
          }
        }
      ],
      "priority": 0
    },
    {
      "key": "end_turn",
      "entity": "game",
      "trigger": "command",
      "phase": "management",
      "condition": {
        "op": "eq",
        "args": {
          "a": {
            "op": "count",
            "args": {
              "items": {
                "op": "entities_matching",
                "args": {
                  "entity_type": {
                    "op": "literal",
                    "value": "decision"
                  },
                  "where": {
                    "op": "field",
                    "args": {
                      "entity": {
                        "op": "context",
                        "ref": "candidate"
                      },
                      "key": {
                        "op": "literal",
                        "value": "open"
                      }
                    }
                  }
                }
              }
            }
          },
          "b": {
            "op": "literal",
            "value": 0
          }
        }
      },
      "effects": [
        {
          "op": "advance_turn",
          "args": {},
          "when": {
            "op": "eq",
            "args": {
              "a": {
                "op": "field",
                "args": {
                  "entity": {
                    "op": "entity_owned_by",
                    "args": {
                      "participant": {
                        "op": "context",
                        "ref": "actor"
                      },
                      "entity_type": {
                        "op": "literal",
                        "value": "token"
                      }
                    }
                  },
                  "key": {
                    "op": "literal",
                    "value": "doubles"
                  }
                }
              },
              "b": {
                "op": "literal",
                "value": 0
              }
            }
          }
        },
        {
          "op": "set_phase",
          "args": {
            "phase": {
              "op": "literal",
              "value": "roll"
            }
          }
        }
      ],
      "priority": 0
    },
    {
      "key": "bankruptcy",
      "entity": "bankruptcy",
      "trigger": "hook",
      "phase": "*",
      "condition": {
        "op": "lt",
        "args": {
          "a": {
            "op": "field",
            "args": {
              "entity": {
                "op": "entity_owned_by",
                "args": {
                  "participant": {
                    "op": "context",
                    "ref": "active_participant"
                  },
                  "entity_type": {
                    "op": "literal",
                    "value": "inventory"
                  }
                }
              },
              "key": {
                "op": "literal",
                "value": "balance"
              }
            }
          },
          "b": {
            "op": "literal",
            "value": 0
          }
        }
      },
      "effects": [
        {
          "op": "execute_transfer_plan",
          "args": {
            "plan": {
              "op": "liquidation_transfer_plan",
              "args": {
                "debtor": {
                  "op": "context",
                  "ref": "active_participant"
                },
                "creditor": {
                  "op": "get_state",
                  "args": {
                    "field": {
                      "op": "literal",
                      "value": "creditor"
                    }
                  }
                },
                "assets": {
                  "op": "participant_entities",
                  "args": {
                    "participant": {
                      "op": "context",
                      "ref": "active_participant"
                    }
                  }
                },
                "reserve": {
                  "op": "literal",
                  "value": 0
                }
              }
            }
          }
        },
        {
          "op": "eliminate_participant",
          "args": {
            "participant": {
              "op": "context",
              "ref": "active_participant"
            }
          }
        }
      ],
      "priority": 0,
      "hook": "game.evaluate"
    },
    {
      "key": "win",
      "entity": "last_solvent",
      "trigger": "hook",
      "phase": "*",
      "condition": {
        "op": "eq",
        "args": {
          "a": {
            "op": "count",
            "args": {
              "items": {
                "op": "filter",
                "args": {
                  "items": {
                    "op": "participants",
                    "args": {}
                  },
                  "variable": {
                    "op": "literal",
                    "value": "person"
                  },
                  "condition": {
                    "op": "gte",
                    "args": {
                      "a": {
                        "op": "field",
                        "args": {
                          "entity": {
                            "op": "entity_owned_by",
                            "args": {
                              "participant": {
                                "op": "context",
                                "ref": "local.person"
                              },
                              "entity_type": {
                                "op": "literal",
                                "value": "inventory"
                              }
                            }
                          },
                          "key": {
                            "op": "literal",
                            "value": "balance"
                          }
                        }
                      },
                      "b": {
                        "op": "literal",
                        "value": 0
                      }
                    }
                  }
                }
              }
            }
          },
          "b": {
            "op": "literal",
            "value": 1
          }
        }
      },
      "effects": [
        {
          "op": "complete_objective",
          "args": {
            "entity": {
              "op": "context",
              "ref": "self"
            }
          }
        },
        {
          "op": "finish_game",
          "args": {
            "result": {
              "op": "literal",
              "value": "last_solvent"
            }
          }
        }
      ],
      "priority": 0,
      "hook": "game.evaluate"
    },
    {
      "key": "wealth",
      "entity": "wealth_quest",
      "trigger": "hook",
      "phase": "*",
      "condition": {
        "op": "gte",
        "args": {
          "a": {
            "op": "field",
            "args": {
              "entity": {
                "op": "entity_owned_by",
                "args": {
                  "participant": {
                    "op": "context",
                    "ref": "active_participant"
                  },
                  "entity_type": {
                    "op": "literal",
                    "value": "inventory"
                  }
                }
              },
              "key": {
                "op": "literal",
                "value": "balance"
              }
            }
          },
          "b": {
            "op": "literal",
            "value": 3000
          }
        }
      },
      "effects": [
        {
          "op": "complete_objective",
          "args": {
            "entity": {
              "op": "context",
              "ref": "self"
            }
          }
        }
      ],
      "priority": 0,
      "hook": "objective.evaluate"
    },
    {
      "key": "fee_on_landing",
      "entity": "lot",
      "trigger": "hook",
      "hook": "space.landed",
      "phase": "resolve",
      "condition": {
        "op": "and",
        "args": {
          "values": [
            {
              "op": "eq",
              "args": {
                "a": {
                  "op": "field",
                  "args": {
                    "entity": {
                      "op": "context",
                      "ref": "self"
                    },
                    "key": {
                      "op": "literal",
                      "value": "location_kind"
                    }
                  }
                },
                "b": {
                  "op": "literal",
                  "value": "tax"
                }
              }
            },
            {
              "op": "entity_at",
              "args": {
                "entity": {
                  "op": "context",
                  "ref": "self"
                },
                "participant": {
                  "op": "context",
                  "ref": "active_participant"
                }
              }
            }
          ]
        }
      },
      "effects": [
        {
          "op": "debit_resource",
          "args": {
            "participant": {
              "op": "context",
              "ref": "active_participant"
            },
            "amount": {
              "op": "field",
              "args": {
                "entity": {
                  "op": "context",
                  "ref": "self"
                },
                "key": {
                  "op": "literal",
                  "value": "fee"
                }
              }
            }
          }
        }
      ],
      "priority": 0
    },
    {
      "key": "send_to_detention",
      "entity": "lot",
      "trigger": "hook",
      "hook": "space.landed",
      "phase": "resolve",
      "condition": {
        "op": "and",
        "args": {
          "values": [
            {
              "op": "eq",
              "args": {
                "a": {
                  "op": "field",
                  "args": {
                    "entity": {
                      "op": "context",
                      "ref": "self"
                    },
                    "key": {
                      "op": "literal",
                      "value": "location_kind"
                    }
                  }
                },
                "b": {
                  "op": "literal",
                  "value": "goto"
                }
              }
            },
            {
              "op": "entity_at",
              "args": {
                "entity": {
                  "op": "context",
                  "ref": "self"
                },
                "participant": {
                  "op": "context",
                  "ref": "active_participant"
                }
              }
            }
          ]
        }
      },
      "effects": [
        {
          "op": "move_entity",
          "args": {
            "entity": {
              "op": "entity_owned_by",
              "args": {
                "participant": {
                  "op": "context",
                  "ref": "active_participant"
                },
                "entity_type": {
                  "op": "literal",
                  "value": "token"
                }
              }
            },
            "destination": {
              "op": "entity_by_seed",
              "args": {
                "key": {
                  "op": "literal",
                  "value": "rest1"
                }
              }
            }
          }
        },
        {
          "op": "set_field",
          "args": {
            "entity": {
              "op": "entity_owned_by",
              "args": {
                "participant": {
                  "op": "context",
                  "ref": "active_participant"
                },
                "entity_type": {
                  "op": "literal",
                  "value": "token"
                }
              }
            },
            "field": {
              "op": "literal",
              "value": "detained"
            },
            "value": {
              "op": "literal",
              "value": true
            }
          }
        },
        {
          "op": "set_field",
          "args": {
            "entity": {
              "op": "entity_owned_by",
              "args": {
                "participant": {
                  "op": "context",
                  "ref": "actor"
                },
                "entity_type": {
                  "op": "literal",
                  "value": "token"
                }
              }
            },
            "field": {
              "op": "literal",
              "value": "detention_attempts"
            },
            "value": {
              "op": "literal",
              "value": 0
            }
          }
        },
        {
          "op": "set_field",
          "args": {
            "entity": {
              "op": "entity_owned_by",
              "args": {
                "participant": {
                  "op": "context",
                  "ref": "actor"
                },
                "entity_type": {
                  "op": "literal",
                  "value": "token"
                }
              }
            },
            "field": {
              "op": "literal",
              "value": "doubles"
            },
            "value": {
              "op": "literal",
              "value": 0
            }
          }
        }
      ],
      "priority": 0
    },
    {
      "key": "start_reward",
      "entity": "lot",
      "trigger": "hook",
      "hook": "space.passed",
      "phase": "*",
      "condition": {
        "op": "eq",
        "args": {
          "a": {
            "op": "context",
            "ref": "self"
          },
          "b": {
            "op": "entity_by_seed",
            "args": {
              "key": {
                "op": "literal",
                "value": "start"
              }
            }
          }
        }
      },
      "effects": [
        {
          "op": "credit_resource",
          "args": {
            "participant": {
              "op": "context",
              "ref": "active_participant"
            },
            "amount": {
              "op": "literal",
              "value": 200
            }
          }
        }
      ],
      "priority": 0
    },
    {
      "key": "card_credit",
      "entity": "card",
      "trigger": "hook",
      "hook": "card.drawn",
      "phase": "*",
      "condition": {
        "op": "and",
        "args": {
          "values": [
            {
              "op": "eq",
              "args": {
                "a": {
                  "op": "context",
                  "ref": "self"
                },
                "b": {
                  "op": "context",
                  "ref": "drawn_card"
                }
              }
            },
            {
              "op": "eq",
              "args": {
                "a": {
                  "op": "field",
                  "args": {
                    "entity": {
                      "op": "context",
                      "ref": "self"
                    },
                    "key": {
                      "op": "literal",
                      "value": "operation"
                    }
                  }
                },
                "b": {
                  "op": "literal",
                  "value": "credit"
                }
              }
            }
          ]
        }
      },
      "effects": [
        {
          "op": "credit_resource",
          "args": {
            "participant": {
              "op": "context",
              "ref": "active_participant"
            },
            "amount": {
              "op": "field",
              "args": {
                "entity": {
                  "op": "context",
                  "ref": "self"
                },
                "key": {
                  "op": "literal",
                  "value": "amount"
                }
              }
            }
          }
        }
      ],
      "priority": 0
    },
    {
      "key": "card_debit",
      "entity": "card",
      "trigger": "hook",
      "hook": "card.drawn",
      "phase": "*",
      "condition": {
        "op": "and",
        "args": {
          "values": [
            {
              "op": "eq",
              "args": {
                "a": {
                  "op": "context",
                  "ref": "self"
                },
                "b": {
                  "op": "context",
                  "ref": "drawn_card"
                }
              }
            },
            {
              "op": "eq",
              "args": {
                "a": {
                  "op": "field",
                  "args": {
                    "entity": {
                      "op": "context",
                      "ref": "self"
                    },
                    "key": {
                      "op": "literal",
                      "value": "operation"
                    }
                  }
                },
                "b": {
                  "op": "literal",
                  "value": "debit"
                }
              }
            }
          ]
        }
      },
      "effects": [
        {
          "op": "debit_resource",
          "args": {
            "participant": {
              "op": "context",
              "ref": "active_participant"
            },
            "amount": {
              "op": "field",
              "args": {
                "entity": {
                  "op": "context",
                  "ref": "self"
                },
                "key": {
                  "op": "literal",
                  "value": "amount"
                }
              }
            }
          }
        }
      ],
      "priority": 0
    },
    {
      "key": "card_advance",
      "entity": "card",
      "trigger": "hook",
      "hook": "card.drawn",
      "phase": "*",
      "condition": {
        "op": "and",
        "args": {
          "values": [
            {
              "op": "eq",
              "args": {
                "a": {
                  "op": "context",
                  "ref": "self"
                },
                "b": {
                  "op": "context",
                  "ref": "drawn_card"
                }
              }
            },
            {
              "op": "eq",
              "args": {
                "a": {
                  "op": "field",
                  "args": {
                    "entity": {
                      "op": "context",
                      "ref": "self"
                    },
                    "key": {
                      "op": "literal",
                      "value": "operation"
                    }
                  }
                },
                "b": {
                  "op": "literal",
                  "value": "advance"
                }
              }
            }
          ]
        }
      },
      "effects": [
        {
          "op": "move_entity",
          "args": {
            "entity": {
              "op": "entity_owned_by",
              "args": {
                "participant": {
                  "op": "context",
                  "ref": "active_participant"
                },
                "entity_type": {
                  "op": "literal",
                  "value": "token"
                }
              }
            },
            "destination": {
              "op": "entity_by_seed",
              "args": {
                "key": {
                  "op": "literal",
                  "value": "start"
                }
              }
            }
          }
        }
      ],
      "priority": 0
    },
    {
      "key": "card_relative",
      "entity": "card",
      "trigger": "hook",
      "hook": "card.drawn",
      "phase": "*",
      "condition": {
        "op": "and",
        "args": {
          "values": [
            {
              "op": "eq",
              "args": {
                "a": {
                  "op": "context",
                  "ref": "self"
                },
                "b": {
                  "op": "context",
                  "ref": "drawn_card"
                }
              }
            },
            {
              "op": "eq",
              "args": {
                "a": {
                  "op": "field",
                  "args": {
                    "entity": {
                      "op": "context",
                      "ref": "self"
                    },
                    "key": {
                      "op": "literal",
                      "value": "operation"
                    }
                  }
                },
                "b": {
                  "op": "literal",
                  "value": "relative"
                }
              }
            }
          ]
        }
      },
      "effects": [
        {
          "op": "move_entity",
          "args": {
            "entity": {
              "op": "entity_owned_by",
              "args": {
                "participant": {
                  "op": "context",
                  "ref": "active_participant"
                },
                "entity_type": {
                  "op": "literal",
                  "value": "token"
                }
              }
            },
            "destination": {
              "op": "path_last",
              "args": {
                "path": {
                  "op": "track_advance",
                  "args": {
                    "entity": {
                      "op": "entity_owned_by",
                      "args": {
                        "participant": {
                          "op": "context",
                          "ref": "active_participant"
                        },
                        "entity_type": {
                          "op": "literal",
                          "value": "token"
                        }
                      }
                    },
                    "steps": {
                      "op": "field",
                      "args": {
                        "entity": {
                          "op": "context",
                          "ref": "self"
                        },
                        "key": {
                          "op": "literal",
                          "value": "amount"
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      ],
      "priority": 0
    },
    {
      "key": "roll_detained",
      "entity": "game",
      "trigger": "command",
      "phase": "roll",
      "condition": {
        "op": "and",
        "args": {
          "values": [
            {
              "op": "and",
              "args": {
                "values": [
                  {
                    "op": "is_active",
                    "args": {
                      "participant": {
                        "op": "context",
                        "ref": "actor"
                      }
                    }
                  },
                  {
                    "op": "phase_is",
                    "args": {
                      "phase": {
                        "op": "literal",
                        "value": "roll"
                      }
                    }
                  }
                ]
              }
            },
            {
              "op": "field",
              "args": {
                "entity": {
                  "op": "entity_owned_by",
                  "args": {
                    "participant": {
                      "op": "context",
                      "ref": "actor"
                    },
                    "entity_type": {
                      "op": "literal",
                      "value": "token"
                    }
                  }
                },
                "key": {
                  "op": "literal",
                  "value": "detained"
                }
              }
            }
          ]
        }
      },
      "effects": [
        {
          "op": "trusted_random_int",
          "args": {
            "name": {
              "op": "literal",
              "value": "die1"
            },
            "lower": {
              "op": "literal",
              "value": 1
            },
            "upper": {
              "op": "literal",
              "value": 6
            }
          }
        },
        {
          "op": "trusted_random_int",
          "args": {
            "name": {
              "op": "literal",
              "value": "die2"
            },
            "lower": {
              "op": "literal",
              "value": 1
            },
            "upper": {
              "op": "literal",
              "value": 6
            }
          }
        },
        {
          "op": "set_field",
          "args": {
            "entity": {
              "op": "context",
              "ref": "self"
            },
            "field": {
              "op": "literal",
              "value": "current_roll"
            },
            "value": {
              "op": "add",
              "args": {
                "a": {
                  "op": "context",
                  "ref": "random.die1"
                },
                "b": {
                  "op": "context",
                  "ref": "random.die2"
                }
              }
            }
          }
        },
        {
          "op": "set_field",
          "args": {
            "entity": {
              "op": "entity_owned_by",
              "args": {
                "participant": {
                  "op": "context",
                  "ref": "actor"
                },
                "entity_type": {
                  "op": "literal",
                  "value": "token"
                }
              }
            },
            "field": {
              "op": "literal",
              "value": "detention_attempts"
            },
            "value": {
              "op": "if",
              "args": {
                "condition": {
                  "op": "eq",
                  "args": {
                    "a": {
                      "op": "context",
                      "ref": "random.die1"
                    },
                    "b": {
                      "op": "context",
                      "ref": "random.die2"
                    }
                  }
                },
                "then": {
                  "op": "literal",
                  "value": 0
                },
                "otherwise": {
                  "op": "add",
                  "args": {
                    "a": {
                      "op": "field",
                      "args": {
                        "entity": {
                          "op": "entity_owned_by",
                          "args": {
                            "participant": {
                              "op": "context",
                              "ref": "actor"
                            },
                            "entity_type": {
                              "op": "literal",
                              "value": "token"
                            }
                          }
                        },
                        "key": {
                          "op": "literal",
                          "value": "detention_attempts"
                        }
                      }
                    },
                    "b": {
                      "op": "literal",
                      "value": 1
                    }
                  }
                }
              }
            }
          }
        },
        {
          "op": "debit_resource",
          "when": {
            "op": "and",
            "args": {
              "values": [
                {
                  "op": "not",
                  "args": {
                    "value": {
                      "op": "eq",
                      "args": {
                        "a": {
                          "op": "context",
                          "ref": "random.die1"
                        },
                        "b": {
                          "op": "context",
                          "ref": "random.die2"
                        }
                      }
                    }
                  }
                },
                {
                  "op": "gte",
                  "args": {
                    "a": {
                      "op": "field",
                      "args": {
                        "entity": {
                          "op": "entity_owned_by",
                          "args": {
                            "participant": {
                              "op": "context",
                              "ref": "actor"
                            },
                            "entity_type": {
                              "op": "literal",
                              "value": "token"
                            }
                          }
                        },
                        "key": {
                          "op": "literal",
                          "value": "detention_attempts"
                        }
                      }
                    },
                    "b": {
                      "op": "literal",
                      "value": 3
                    }
                  }
                }
              ]
            }
          },
          "args": {
            "participant": {
              "op": "context",
              "ref": "actor"
            },
            "amount": {
              "op": "literal",
              "value": 50
            }
          }
        },
        {
          "op": "set_field",
          "args": {
            "entity": {
              "op": "entity_owned_by",
              "args": {
                "participant": {
                  "op": "context",
                  "ref": "actor"
                },
                "entity_type": {
                  "op": "literal",
                  "value": "token"
                }
              }
            },
            "field": {
              "op": "literal",
              "value": "detained"
            },
            "value": {
              "op": "not",
              "args": {
                "value": {
                  "op": "or",
                  "args": {
                    "values": [
                      {
                        "op": "eq",
                        "args": {
                          "a": {
                            "op": "context",
                            "ref": "random.die1"
                          },
                          "b": {
                            "op": "context",
                            "ref": "random.die2"
                          }
                        }
                      },
                      {
                        "op": "gte",
                        "args": {
                          "a": {
                            "op": "field",
                            "args": {
                              "entity": {
                                "op": "entity_owned_by",
                                "args": {
                                  "participant": {
                                    "op": "context",
                                    "ref": "actor"
                                  },
                                  "entity_type": {
                                    "op": "literal",
                                    "value": "token"
                                  }
                                }
                              },
                              "key": {
                                "op": "literal",
                                "value": "detention_attempts"
                              }
                            }
                          },
                          "b": {
                            "op": "literal",
                            "value": 3
                          }
                        }
                      }
                    ]
                  }
                }
              }
            }
          }
        },
        {
          "op": "set_field",
          "args": {
            "entity": {
              "op": "entity_owned_by",
              "args": {
                "participant": {
                  "op": "context",
                  "ref": "actor"
                },
                "entity_type": {
                  "op": "literal",
                  "value": "token"
                }
              }
            },
            "field": {
              "op": "literal",
              "value": "doubles"
            },
            "value": {
              "op": "literal",
              "value": 0
            }
          }
        },
        {
          "op": "set_phase",
          "args": {
            "phase": {
              "op": "if",
              "args": {
                "condition": {
                  "op": "or",
                  "args": {
                    "values": [
                      {
                        "op": "eq",
                        "args": {
                          "a": {
                            "op": "context",
                            "ref": "random.die1"
                          },
                          "b": {
                            "op": "context",
                            "ref": "random.die2"
                          }
                        }
                      },
                      {
                        "op": "gte",
                        "args": {
                          "a": {
                            "op": "field",
                            "args": {
                              "entity": {
                                "op": "entity_owned_by",
                                "args": {
                                  "participant": {
                                    "op": "context",
                                    "ref": "actor"
                                  },
                                  "entity_type": {
                                    "op": "literal",
                                    "value": "token"
                                  }
                                }
                              },
                              "key": {
                                "op": "literal",
                                "value": "detention_attempts"
                              }
                            }
                          },
                          "b": {
                            "op": "literal",
                            "value": 3
                          }
                        }
                      }
                    ]
                  }
                },
                "then": {
                  "op": "literal",
                  "value": "move"
                },
                "otherwise": {
                  "op": "literal",
                  "value": "management"
                }
              }
            }
          }
        }
      ],
      "priority": 0
    },
    {
      "key": "pay_release",
      "entity": "game",
      "trigger": "command",
      "phase": "roll",
      "condition": {
        "op": "and",
        "args": {
          "values": [
            {
              "op": "and",
              "args": {
                "values": [
                  {
                    "op": "is_active",
                    "args": {
                      "participant": {
                        "op": "context",
                        "ref": "actor"
                      }
                    }
                  },
                  {
                    "op": "phase_is",
                    "args": {
                      "phase": {
                        "op": "literal",
                        "value": "roll"
                      }
                    }
                  }
                ]
              }
            },
            {
              "op": "field",
              "args": {
                "entity": {
                  "op": "entity_owned_by",
                  "args": {
                    "participant": {
                      "op": "context",
                      "ref": "actor"
                    },
                    "entity_type": {
                      "op": "literal",
                      "value": "token"
                    }
                  }
                },
                "key": {
                  "op": "literal",
                  "value": "detained"
                }
              }
            },
            {
              "op": "gte",
              "args": {
                "a": {
                  "op": "field",
                  "args": {
                    "entity": {
                      "op": "entity_owned_by",
                      "args": {
                        "participant": {
                          "op": "context",
                          "ref": "actor"
                        },
                        "entity_type": {
                          "op": "literal",
                          "value": "inventory"
                        }
                      }
                    },
                    "key": {
                      "op": "literal",
                      "value": "balance"
                    }
                  }
                },
                "b": {
                  "op": "literal",
                  "value": 50
                }
              }
            }
          ]
        }
      },
      "effects": [
        {
          "op": "debit_resource",
          "args": {
            "participant": {
              "op": "context",
              "ref": "actor"
            },
            "amount": {
              "op": "literal",
              "value": 50
            }
          }
        },
        {
          "op": "set_field",
          "args": {
            "entity": {
              "op": "entity_owned_by",
              "args": {
                "participant": {
                  "op": "context",
                  "ref": "actor"
                },
                "entity_type": {
                  "op": "literal",
                  "value": "token"
                }
              }
            },
            "field": {
              "op": "literal",
              "value": "detained"
            },
            "value": {
              "op": "literal",
              "value": false
            }
          }
        },
        {
          "op": "set_field",
          "args": {
            "entity": {
              "op": "entity_owned_by",
              "args": {
                "participant": {
                  "op": "context",
                  "ref": "actor"
                },
                "entity_type": {
                  "op": "literal",
                  "value": "token"
                }
              }
            },
            "field": {
              "op": "literal",
              "value": "detention_attempts"
            },
            "value": {
              "op": "literal",
              "value": 0
            }
          }
        }
      ],
      "priority": 0
    }
  ],
  "visuals": [
    {
      "entity": "lot",
      "primitives": [
        {
          "kind": "rectangle",
          "width": 80,
          "height": 80,
          "fill": "#e9e2d5"
        },
        {
          "kind": "text",
          "x": 5,
          "y": 20,
          "text": "Property",
          "fill": "#111"
        }
      ]
    },
    {
      "entity": "token",
      "primitives": [
        {
          "kind": "ellipse",
          "width": 24,
          "height": 24,
          "x": 10,
          "y": 10,
          "fill": "#de532e"
        }
      ]
    },
    {
      "entity": "property",
      "primitives": [
        {
          "kind": "rectangle",
          "width": 56,
          "height": 70,
          "fill": "#e6ddc0"
        }
      ]
    },
    {
      "entity": "card",
      "primitives": [
        {
          "kind": "rectangle",
          "width": 140,
          "height": 80,
          "fill": "#faf5dc"
        }
      ]
    }
  ],
  "assets": []
}
```

## 6.3 Registry and provisioning data

`packages/server/supabase/seed.sql` installs the stable hook vocabulary and Storage bucket data. The operator registry is generated from the pure Python engine's registered signatures and compared to all operator keys referenced by built-ins. The database stores immutable metadata; it does not execute operator code. The source of game behavior remains the imported per-game JSON translated to relational rows.

```sql
-- Registry metadata must be generated from engine/operators.py without drift.
-- Binary assets are uploaded via server/asset service; metadata is relational.
-- Supabase Storage buckets are data rows and belong in DML, not in Drizzle schema.
INSERT INTO storage.buckets(id,name,public, file_size_limit, allowed_mime_types)
VALUES ('bgwq-visuals','bgwq-visuals',false,2097152,ARRAY['image/png','image/webp'])
ON CONFLICT (id) DO NOTHING;

INSERT INTO bgwq.hooks (key,ordinal,summary) VALUES
 ('game.initialize',0,'Populate entity seeds and default values'),
 ('action.generate',10,'Produce candidate participant commands'),
 ('action.validate',20,'Validate candidate commands against configuration'),
 ('action.before',30,'Evaluate pre-transition automatic actions'),
 ('action.apply',40,'Execute validated command effects'),
 ('action.after',50,'Evaluate post-transition actions'),
 ('space.passed',55,'Notify configured traversal pass events'),
 ('space.landed',56,'Notify configured arrival'),
 ('phase.enter',60,'Enter configured phase'),
 ('phase.exit',65,'Exit configured phase'),
 ('card.drawn',68,'Resolve a drawn card through actions on its entity type'),
 ('decision.resolved',70,'Decision is ready for settlement'),
 ('objective.evaluate',80,'Evaluate configured objectives and quests'),
 ('game.evaluate',90,'Resolve configured terminal objectives')
ON CONFLICT (key) DO NOTHING;
```

A validated import preserves stable local keys, makes a new draft version, hydrates entity types/seeds/links, fields, expressions and actions into normalized rows, stages assets, validates the exact operator catalog, and publishes only when all referenced assets and declarations resolve. Export reverses the mapping to canonical sorted JSON, embedding binary assets as Base64; database UUIDs and Storage URLs are not serialized. Hidden runtime state is never included in a configuration export.


## 6.4 Generic operator contracts

The JSON object below is the canonical per-operator semantic contract consumed by validation and generated documentation. Each operation defines its argument names, observed call signatures and deterministic behavior. `requires-decomposition` is a publication blocker, never an implicit Python extension point. A specification contract does not, by itself, prove the implementation exists or passes behavioral tests.

```json
{
  "format": "bgwq.operator-contract",
  "version": 1,
  "operators": {
    "add": {
      "category": "expression",
      "arguments": [
        "a",
        "b"
      ],
      "observed_signatures": [
        {
          "kind": "expression",
          "keys": [
            "a",
            "b"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Exact checked integer or decimal addition; integer overflow rejects evaluation."
    },
    "advance_turn": {
      "category": "effect",
      "arguments": [],
      "observed_signatures": [
        {
          "kind": "effect",
          "keys": []
        }
      ],
      "status": "specified",
      "semantics": "Move active actor to next eligible participant per definition and increment the configured turn counter."
    },
    "and": {
      "category": "expression",
      "arguments": [
        "values"
      ],
      "observed_signatures": [
        {
          "kind": "expression",
          "keys": [
            "values"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Left-to-right short-circuit conjunction over Boolean arguments."
    },
    "any_match": {
      "category": "expression",
      "arguments": [
        "items",
        "predicate",
        "variable"
      ],
      "observed_signatures": [
        {
          "kind": "expression",
          "keys": [
            "items",
            "predicate",
            "variable"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Return true if any item satisfies the predicate; short circuit left-to-right."
    },
    "apply_path": {
      "category": "effect",
      "arguments": [
        "entity",
        "path",
        "remove_traversed_entities"
      ],
      "observed_signatures": [
        {
          "kind": "effect",
          "keys": [
            "entity",
            "path",
            "remove_traversed_entities"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Validate every step/capture in the provided typed path against its generation witness, remove marked entities and move actor to terminal location atomically."
    },
    "attacked_node": {
      "category": "expression",
      "arguments": [
        "by",
        "node"
      ],
      "observed_signatures": [
        {
          "kind": "expression",
          "keys": [
            "by",
            "node"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Return whether the node is reached by the configured nonmutating threat-projection actions for any attacker in the supplied set; never recurse into legal-action checking."
    },
    "available_action_count": {
      "category": "expression",
      "arguments": [
        "actor"
      ],
      "observed_signatures": [
        {
          "kind": "expression",
          "keys": [
            "actor"
          ]
        }
      ],
      "status": "specified",
      "semantics": "After legality phase only, count the actor’s fully validated currently available commands without launching recursive action generation."
    },
    "best_by": {
      "category": "expression",
      "arguments": [
        "field",
        "items",
        "order"
      ],
      "observed_signatures": [
        {
          "kind": "expression",
          "keys": [
            "field",
            "items",
            "order"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Return the first record with extremal declared comparable field, ordered ascending/descending by argument; ties are broken by original ordered position."
    },
    "change_entity_type": {
      "category": "effect",
      "arguments": [
        "entity",
        "to"
      ],
      "observed_signatures": [
        {
          "kind": "effect",
          "keys": [
            "entity",
            "to"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Change an entity to a compatible configured entity type; invalid remaining fields require an explicit mapping or fail."
    },
    "clock_expired": {
      "category": "expression",
      "arguments": [
        "state"
      ],
      "observed_signatures": [
        {
          "kind": "expression",
          "keys": [
            "state"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Return true iff the trusted clock projection reports an active clock at zero remaining milliseconds."
    },
    "complete_objective": {
      "category": "effect",
      "arguments": [
        "entity"
      ],
      "observed_signatures": [
        {
          "kind": "effect",
          "keys": [
            "entity"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Set one objective entity completion flag and emit a typed completion event."
    },
    "concat": {
      "category": "expression",
      "arguments": [
        "a",
        "b"
      ],
      "observed_signatures": [
        {
          "kind": "expression",
          "keys": [
            "a",
            "b"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Concatenate two compatible typed ordered lists without removing duplicates."
    },
    "contains": {
      "category": "expression",
      "arguments": [
        "items",
        "value"
      ],
      "observed_signatures": [
        {
          "kind": "expression",
          "keys": [
            "items",
            "value"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Type-preserving membership test; list and set equality use canonical reference identity."
    },
    "context": {
      "category": "expression",
      "arguments": [],
      "observed_signatures": [
        {
          "kind": "expression",
          "keys": []
        }
      ],
      "status": "specified",
      "semantics": "Read an available lexically scoped context value. Missing values are typed evaluation errors."
    },
    "count": {
      "category": "expression",
      "arguments": [
        "items"
      ],
      "observed_signatures": [
        {
          "kind": "expression",
          "keys": [
            "items"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Length of a bounded collection."
    },
    "create_entity": {
      "category": "effect",
      "arguments": [
        "fields",
        "type"
      ],
      "observed_signatures": [
        {
          "kind": "effect",
          "keys": [
            "fields",
            "type"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Create an instance of an entity type from the pinned definition and initialize declared fields/relationships."
    },
    "credit_resource": {
      "category": "effect",
      "arguments": [
        "amount",
        "participant"
      ],
      "observed_signatures": [
        {
          "kind": "effect",
          "keys": [
            "amount",
            "participant"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Increment an owned resource field of the referenced participant’s configured inventory."
    },
    "debit_resource": {
      "category": "effect",
      "arguments": [
        "amount",
        "participant"
      ],
      "observed_signatures": [
        {
          "kind": "effect",
          "keys": [
            "amount",
            "participant"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Decrement an owned resource field of the referenced participant’s configured inventory, subject to debt policy."
    },
    "decision_eligible": {
      "category": "expression",
      "arguments": [
        "decision"
      ],
      "observed_signatures": [
        {
          "kind": "expression",
          "keys": [
            "decision"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Return ordered set of participants authorized by the stored decision scope, excluding eliminated actors."
    },
    "decision_is_open": {
      "category": "expression",
      "arguments": [
        "decision"
      ],
      "observed_signatures": [
        {
          "kind": "expression",
          "keys": [
            "decision"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Read the entity-backed decision status and return true exactly when its status field is open."
    },
    "decision_payload": {
      "category": "expression",
      "arguments": [
        "decision"
      ],
      "observed_signatures": [
        {
          "kind": "expression",
          "keys": [
            "decision"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Reconstruct the type-checked composite record stored on the decision entity from normalized game_composites and game_composite_entries."
    },
    "decision_responses": {
      "category": "expression",
      "arguments": [
        "decision"
      ],
      "observed_signatures": [
        {
          "kind": "expression",
          "keys": [
            "decision"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Return the current committed response records for the referenced decision, ordered by event revision then participant seat."
    },
    "decision_subject": {
      "category": "expression",
      "arguments": [
        "decision"
      ],
      "observed_signatures": [
        {
          "kind": "expression",
          "keys": [
            "decision"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Return the entity reference that the decision is about; the definition must declare one stored subject relation."
    },
    "draw_collection_item": {
      "category": "effect",
      "arguments": [
        "deck"
      ],
      "observed_signatures": [
        {
          "kind": "effect",
          "keys": [
            "deck"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Consume or reveal the next ordered item in a configured collection; bind drawn_card in the effect scope."
    },
    "effect_value": {
      "category": "expression",
      "arguments": [
        "destination",
        "entity",
        "name"
      ],
      "observed_signatures": [
        {
          "kind": "expression",
          "keys": [
            "destination",
            "entity",
            "name"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Construct a typed non-executable hypothetical effect value with validated operation key and arguments."
    },
    "eliminate_participant": {
      "category": "effect",
      "arguments": [
        "participant"
      ],
      "observed_signatures": [
        {
          "kind": "effect",
          "keys": [
            "participant"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Mark a participant ineligible for future turns while preserving history."
    },
    "emit_candidate": {
      "category": "effect",
      "arguments": [
        "destination",
        "entity",
        "path",
        "source"
      ],
      "observed_signatures": [
        {
          "kind": "effect",
          "keys": [
            "destination",
            "source"
          ]
        },
        {
          "kind": "effect",
          "keys": [
            "entity",
            "path"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Append typed candidate command to the proposed candidate set; never mutates game state."
    },
    "emit_event": {
      "category": "effect",
      "arguments": [
        "entity",
        "name"
      ],
      "observed_signatures": [
        {
          "kind": "effect",
          "keys": [
            "entity",
            "name"
          ]
        },
        {
          "kind": "effect",
          "keys": [
            "name"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Append a typed domain event to the proposed event queue; breadth-first hook dispatch is bounded and deterministic."
    },
    "emit_traversal_events": {
      "category": "effect",
      "arguments": [
        "entity",
        "hook",
        "steps"
      ],
      "observed_signatures": [
        {
          "kind": "effect",
          "keys": [
            "entity",
            "hook",
            "steps"
          ]
        }
      ],
      "status": "specified",
      "semantics": "For each traversed location in the committed typed path, enqueue one typed pass event in path order."
    },
    "entities_at": {
      "category": "expression",
      "arguments": [
        "node"
      ],
      "observed_signatures": [
        {
          "kind": "expression",
          "keys": [
            "node"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Return existing entities at a given location in stable identity order."
    },
    "entities_matching": {
      "category": "expression",
      "arguments": [
        "entity_type",
        "owner",
        "state",
        "where"
      ],
      "observed_signatures": [
        {
          "kind": "expression",
          "keys": [
            "entity_type",
            "owner",
            "state"
          ]
        },
        {
          "kind": "expression",
          "keys": [
            "entity_type",
            "where"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Return entities of requested type satisfying a pure typed predicate over an explicitly named lexical variable."
    },
    "entities_of_type": {
      "category": "expression",
      "arguments": [
        "entity_type"
      ],
      "observed_signatures": [
        {
          "kind": "expression",
          "keys": [
            "entity_type"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Return all existing game entities of the declared type in stable identity order."
    },
    "entity_at": {
      "category": "expression",
      "arguments": [
        "entity",
        "participant"
      ],
      "observed_signatures": [
        {
          "kind": "expression",
          "keys": [
            "entity",
            "participant"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Return true precisely if the active participant’s token has the same location reference as the entity argument; reject if no unique token exists."
    },
    "entity_by_seed": {
      "category": "expression",
      "arguments": [
        "key"
      ],
      "observed_signatures": [
        {
          "kind": "expression",
          "keys": [
            "key"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Resolve a unique runtime instance of a declared seed key in the same pinned game, or absence if a conditional seed did not instantiate."
    },
    "entity_location": {
      "category": "expression",
      "arguments": [
        "entity"
      ],
      "observed_signatures": [
        {
          "kind": "expression",
          "keys": [
            "entity"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Return an optional location-entity reference in the selected state."
    },
    "entity_owned_by": {
      "category": "expression",
      "arguments": [
        "entity_type",
        "participant"
      ],
      "observed_signatures": [
        {
          "kind": "expression",
          "keys": [
            "entity_type",
            "participant"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Return the unique extant game entity of the requested type owned by participant, or absence; uniqueness is checked at publication for such calls."
    },
    "eq": {
      "category": "expression",
      "arguments": [
        "a",
        "b"
      ],
      "observed_signatures": [
        {
          "kind": "expression",
          "keys": [
            "a",
            "b"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Structural equality for values of the same validated type, including absence."
    },
    "event_attribute": {
      "category": "expression",
      "arguments": [
        "attribute",
        "event"
      ],
      "observed_signatures": [
        {
          "kind": "expression",
          "keys": [
            "attribute",
            "event"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Read a typed key from the current accepted/proposed domain event."
    },
    "execute_transfer_plan": {
      "category": "effect",
      "arguments": [
        "plan"
      ],
      "observed_signatures": [
        {
          "kind": "effect",
          "keys": [
            "plan"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Apply a previously validated ordered transfer plan to the proposed state, using the same field and ownership effects atomically; any failure discards all changes."
    },
    "field": {
      "category": "expression",
      "arguments": [
        "entity",
        "key"
      ],
      "observed_signatures": [
        {
          "kind": "expression",
          "keys": [
            "entity",
            "key"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Read a declared state field on a typed entity reference in the selected immutable state."
    },
    "filter": {
      "category": "expression",
      "arguments": [
        "condition",
        "items",
        "predicate",
        "variable"
      ],
      "observed_signatures": [
        {
          "kind": "expression",
          "keys": [
            "condition",
            "items",
            "variable"
          ]
        },
        {
          "kind": "expression",
          "keys": [
            "items",
            "predicate",
            "variable"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Bind variable to each item in order and retain items with true predicate; no mutation allowed."
    },
    "finish_game": {
      "category": "effect",
      "arguments": [
        "result"
      ],
      "observed_signatures": [
        {
          "kind": "effect",
          "keys": [
            "result"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Propose a terminal outcome only when no higher-priority conflicting terminal action exists."
    },
    "first": {
      "category": "expression",
      "arguments": [
        "items"
      ],
      "observed_signatures": [
        {
          "kind": "expression",
          "keys": [
            "items"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Return the first item or typed absence."
    },
    "floor_divide": {
      "category": "expression",
      "arguments": [
        "a",
        "b"
      ],
      "observed_signatures": [
        {
          "kind": "expression",
          "keys": [
            "a",
            "b"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Mathematical floor division for signed integers; zero divisor rejects evaluation."
    },
    "get_state": {
      "category": "expression",
      "arguments": [
        "field",
        "state"
      ],
      "observed_signatures": [
        {
          "kind": "expression",
          "keys": [
            "field"
          ]
        },
        {
          "kind": "expression",
          "keys": [
            "field",
            "state"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Read a root entity field in the designated state projection."
    },
    "grid_between": {
      "category": "expression",
      "arguments": [
        "first",
        "last"
      ],
      "observed_signatures": [
        {
          "kind": "expression",
          "keys": [
            "first",
            "last"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Return strictly interior nodes between two collinear grid locations in deterministic traversal order."
    },
    "grid_edge": {
      "category": "expression",
      "arguments": [
        "entity",
        "horizontal"
      ],
      "observed_signatures": [
        {
          "kind": "expression",
          "keys": [
            "entity",
            "horizontal"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Return leftmost or rightmost node in the entity’s grid row; direction is an explicit parameter."
    },
    "grid_offset": {
      "category": "expression",
      "arguments": [
        "column",
        "entity",
        "row"
      ],
      "observed_signatures": [
        {
          "kind": "expression",
          "keys": [
            "column",
            "entity",
            "row"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Return a grid node offset by typed row/column values, or absence when out of bounds."
    },
    "gt": {
      "category": "expression",
      "arguments": [
        "a",
        "b"
      ],
      "observed_signatures": [
        {
          "kind": "expression",
          "keys": [
            "a",
            "b"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Strict comparison of matching ordered numeric, instant or text types."
    },
    "gte": {
      "category": "expression",
      "arguments": [
        "a",
        "b"
      ],
      "observed_signatures": [
        {
          "kind": "expression",
          "keys": [
            "a",
            "b"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Inclusive comparison of matching ordered numeric, instant or text types."
    },
    "has_relation": {
      "category": "expression",
      "arguments": [
        "relation",
        "source",
        "target"
      ],
      "observed_signatures": [
        {
          "kind": "expression",
          "keys": [
            "relation",
            "source",
            "target"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Return whether an explicit relationship with this key exists between two entity references."
    },
    "if": {
      "category": "expression",
      "arguments": [
        "condition",
        "otherwise",
        "then"
      ],
      "observed_signatures": [
        {
          "kind": "expression",
          "keys": [
            "condition",
            "otherwise",
            "then"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Lazy ternary selection; only the selected expression branch is evaluated."
    },
    "increment_field": {
      "category": "effect",
      "arguments": [
        "amount",
        "entity",
        "field"
      ],
      "observed_signatures": [
        {
          "kind": "effect",
          "keys": [
            "amount",
            "entity",
            "field"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Add an exact integer/decimal amount to a declared numeric entity field atomically."
    },
    "is_active": {
      "category": "expression",
      "arguments": [
        "participant"
      ],
      "observed_signatures": [
        {
          "kind": "expression",
          "keys": [
            "participant"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Return whether a participant is currently authorized as an active turn actor."
    },
    "is_present": {
      "category": "expression",
      "arguments": [
        "value"
      ],
      "observed_signatures": [
        {
          "kind": "expression",
          "keys": [
            "value"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Return true precisely when an optional value is present."
    },
    "jump_landing_steps": {
      "category": "expression",
      "arguments": [
        "directions",
        "entity",
        "flying",
        "jumped_occupancy",
        "max_flight",
        "orientation",
        "target_occupancy"
      ],
      "observed_signatures": [
        {
          "kind": "expression",
          "keys": [
            "directions",
            "entity",
            "flying",
            "jumped_occupancy",
            "max_flight",
            "orientation",
            "target_occupancy"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Enumerate generic leap-over steps from a node along supplied vectors, with typed over/landing references, occupancy rules and bounded flight."
    },
    "liquidation_transfer_plan": {
      "category": "expression",
      "arguments": [
        "assets",
        "creditor",
        "debtor",
        "reserve"
      ],
      "observed_signatures": [
        {
          "kind": "expression",
          "keys": [
            "assets",
            "creditor",
            "debtor",
            "reserve"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Construct an ordered transfer plan from all debtor-owned nonexempt assets and positive balance to the configured creditor/system treasury, respecting the definition’s declared priority policy; reject absent liquidation policy rather than inventing game rules."
    },
    "list": {
      "category": "expression",
      "arguments": [
        "values"
      ],
      "observed_signatures": [
        {
          "kind": "expression",
          "keys": [
            "values"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Construct a deterministic ordered immutable list from the evaluated expressions."
    },
    "literal": {
      "category": "expression",
      "arguments": [],
      "observed_signatures": [
        {
          "kind": "expression",
          "keys": []
        }
      ],
      "status": "specified",
      "semantics": "Return the typed literal payload; a null literal has the explicit optional/none type."
    },
    "lt": {
      "category": "expression",
      "arguments": [
        "a",
        "b"
      ],
      "observed_signatures": [
        {
          "kind": "expression",
          "keys": [
            "a",
            "b"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Strict comparison of matching ordered numeric, instant or text types."
    },
    "map": {
      "category": "expression",
      "arguments": [
        "expression",
        "items",
        "variable"
      ],
      "observed_signatures": [
        {
          "kind": "expression",
          "keys": [
            "expression",
            "items",
            "variable"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Bind variable to each item and evaluate expression; preserve collection order."
    },
    "maximum": {
      "category": "expression",
      "arguments": [
        "values"
      ],
      "observed_signatures": [
        {
          "kind": "expression",
          "keys": [
            "values"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Maximum of nonempty bounded ordered numeric collection; empty is an error."
    },
    "maximum_or": {
      "category": "expression",
      "arguments": [
        "default",
        "items"
      ],
      "observed_signatures": [
        {
          "kind": "expression",
          "keys": [
            "default",
            "items"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Compute maximum of nonempty ordered numeric values; return the explicit default for an empty collection."
    },
    "move_entity": {
      "category": "effect",
      "arguments": [
        "destination",
        "entity"
      ],
      "observed_signatures": [
        {
          "kind": "effect",
          "keys": [
            "destination",
            "entity"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Move one entity to a compatible target space entity in proposed state; maintain location/containment invariants."
    },
    "multiply": {
      "category": "expression",
      "arguments": [
        "a",
        "b"
      ],
      "observed_signatures": [
        {
          "kind": "expression",
          "keys": [
            "a",
            "b"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Exact checked integer or decimal multiplication."
    },
    "negate": {
      "category": "expression",
      "arguments": [
        "value"
      ],
      "observed_signatures": [
        {
          "kind": "expression",
          "keys": [
            "value"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Checked numeric negation."
    },
    "next_participant": {
      "category": "expression",
      "arguments": [
        "participant"
      ],
      "observed_signatures": [
        {
          "kind": "expression",
          "keys": [
            "participant"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Select the next eligible participant according to configured seating/active state, wrapping; absence when none remain."
    },
    "no_reachable_terminal": {
      "category": "expression",
      "arguments": [
        "max_states",
        "state",
        "terminal"
      ],
      "observed_signatures": [
        {
          "kind": "expression",
          "keys": [
            "max_states",
            "state",
            "terminal"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Exact generic finite-state reachability proof over complete legal actions and trusted random branches. Breadth-first graph search with canonical rule-state keys returns true only when exhaustive reachable-state exploration finds no state satisfying the configured terminal objective. Exceeding max_states raises ReachabilityLimit, never a false proof. Implemented in engine/reachability.py."
    },
    "none_match": {
      "category": "expression",
      "arguments": [
        "items",
        "predicate",
        "variable"
      ],
      "observed_signatures": [
        {
          "kind": "expression",
          "keys": [
            "items",
            "predicate",
            "variable"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Return true if no item satisfies predicate; short circuit left-to-right."
    },
    "not": {
      "category": "expression",
      "arguments": [
        "value"
      ],
      "observed_signatures": [
        {
          "kind": "expression",
          "keys": [
            "value"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Boolean complement of exactly one Boolean argument."
    },
    "on_board_edge": {
      "category": "expression",
      "arguments": [
        "edge",
        "entity"
      ],
      "observed_signatures": [
        {
          "kind": "expression",
          "keys": [
            "edge",
            "entity"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Compare entity location and role forward_row to the configured minimum/maximum row boundary; no game-name branches."
    },
    "only_path_distance": {
      "category": "expression",
      "arguments": [
        "distance",
        "nodes"
      ],
      "observed_signatures": [
        {
          "kind": "expression",
          "keys": [
            "distance",
            "nodes"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Filter candidate destinations to exactly the specified positive path step count."
    },
    "open_decision": {
      "category": "effect",
      "arguments": [
        "decision",
        "entity"
      ],
      "observed_signatures": [
        {
          "kind": "effect",
          "keys": [
            "decision",
            "entity"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Open an entity-backed bounded decision with eligible actors and resolution policy."
    },
    "opponents": {
      "category": "expression",
      "arguments": [
        "participant"
      ],
      "observed_signatures": [
        {
          "kind": "expression",
          "keys": [
            "participant"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Return non-allied non-eliminated participants from an explicit participant/team relation."
    },
    "or": {
      "category": "expression",
      "arguments": [
        "values"
      ],
      "observed_signatures": [
        {
          "kind": "expression",
          "keys": [
            "values"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Left-to-right short-circuit disjunction over Boolean arguments."
    },
    "owner": {
      "category": "expression",
      "arguments": [
        "entity"
      ],
      "observed_signatures": [
        {
          "kind": "expression",
          "keys": [
            "entity"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Return optional participant identity owning the given game entity."
    },
    "owner_orientation": {
      "category": "expression",
      "arguments": [
        "entity"
      ],
      "observed_signatures": [
        {
          "kind": "expression",
          "keys": [
            "entity"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Return configured role forward_row (−1 or +1); absence is a type error in oriented-grid actions."
    },
    "participant_entities": {
      "category": "expression",
      "arguments": [
        "participant"
      ],
      "observed_signatures": [
        {
          "kind": "expression",
          "keys": [
            "participant"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Return entities owned by participant, sorted by identity."
    },
    "participants": {
      "category": "expression",
      "arguments": [],
      "observed_signatures": [
        {
          "kind": "expression",
          "keys": []
        }
      ],
      "status": "specified",
      "semantics": "Return joined active and eliminated game participants, ordered by configured seat."
    },
    "path_captured_entities": {
      "category": "expression",
      "arguments": [
        "path"
      ],
      "observed_signatures": [
        {
          "kind": "expression",
          "keys": [
            "path"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Return each distinct traversed entity marked as captured in the path in traversal order."
    },
    "path_clear": {
      "category": "expression",
      "arguments": [
        "nodes"
      ],
      "observed_signatures": [
        {
          "kind": "expression",
          "keys": [
            "nodes"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Return whether every specified interior node is unoccupied in selected state."
    },
    "path_last": {
      "category": "expression",
      "arguments": [
        "path"
      ],
      "observed_signatures": [
        {
          "kind": "expression",
          "keys": [
            "path"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Return the terminal node of a nonempty validated path; empty raises evaluation error."
    },
    "phase_is": {
      "category": "expression",
      "arguments": [
        "phase"
      ],
      "observed_signatures": [
        {
          "kind": "expression",
          "keys": [
            "phase"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Compare selected/current phase key to literal phase key."
    },
    "position_occurrences": {
      "category": "expression",
      "arguments": [
        "state"
      ],
      "observed_signatures": [
        {
          "kind": "expression",
          "keys": [
            "state"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Count occurrences of the definition’s declared normalized position identity in committed history."
    },
    "preview": {
      "category": "expression",
      "arguments": [
        "effects",
        "state"
      ],
      "observed_signatures": [
        {
          "kind": "expression",
          "keys": [
            "effects",
            "state"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Apply an ordered list of validated hypothetical effects to an immutable copy of selected state, without I/O or random consumption."
    },
    "reachable_grid_nodes": {
      "category": "expression",
      "arguments": [
        "directions",
        "entity",
        "leap",
        "max_steps",
        "orientation",
        "state",
        "target_occupancy"
      ],
      "observed_signatures": [
        {
          "kind": "expression",
          "keys": [
            "directions",
            "entity",
            "leap",
            "max_steps",
            "orientation",
            "state",
            "target_occupancy"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Enumerate reachable grid nodes using supplied numeric vectors, orientation, range, stop-on-occupancy and target-occupancy rules; never inspect game name."
    },
    "record_decision": {
      "category": "effect",
      "arguments": [
        "actor",
        "amount",
        "entity"
      ],
      "observed_signatures": [
        {
          "kind": "effect",
          "keys": [
            "actor",
            "amount",
            "entity"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Record a participant response to an open entity-backed decision; reject duplicates or ineligible responders."
    },
    "record_field": {
      "category": "expression",
      "arguments": [
        "key",
        "record"
      ],
      "observed_signatures": [
        {
          "kind": "expression",
          "keys": [
            "key",
            "record"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Read a schema-declared field on a typed record value, or report a typed error for a missing required field."
    },
    "remove_entity": {
      "category": "effect",
      "arguments": [
        "entity"
      ],
      "observed_signatures": [
        {
          "kind": "effect",
          "keys": [
            "entity"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Mark an existing entity removed in proposed state, preserving its historical identity for replay."
    },
    "remove_matching_entities": {
      "category": "effect",
      "arguments": [
        "exclude_owner",
        "node"
      ],
      "observed_signatures": [
        {
          "kind": "effect",
          "keys": [
            "exclude_owner",
            "node"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Remove all entities at a location whose owner differs from exclude_owner, sorted and bounded; generic bulk mutation."
    },
    "resolve_decision": {
      "category": "effect",
      "arguments": [
        "entity"
      ],
      "observed_signatures": [
        {
          "kind": "effect",
          "keys": [
            "entity"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Resolve an entity-backed decision using its configured generic aggregation policy."
    },
    "set_field": {
      "category": "effect",
      "arguments": [
        "entity",
        "field",
        "value"
      ],
      "observed_signatures": [
        {
          "kind": "effect",
          "keys": [
            "entity",
            "field",
            "value"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Assign one declared typed state field on an existing entity; value must match field type."
    },
    "set_owner": {
      "category": "effect",
      "arguments": [
        "entity",
        "owner"
      ],
      "observed_signatures": [
        {
          "kind": "effect",
          "keys": [
            "entity",
            "owner"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Assign an entity’s owner to a valid participant or absence, with no cross-game references."
    },
    "set_phase": {
      "category": "effect",
      "arguments": [
        "phase"
      ],
      "observed_signatures": [
        {
          "kind": "effect",
          "keys": [
            "phase"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Set the current phase to a configured phase; events are queued, not synchronously recursively executed."
    },
    "threatened": {
      "category": "expression",
      "arguments": [
        "entity",
        "state"
      ],
      "observed_signatures": [
        {
          "kind": "expression",
          "keys": [
            "entity",
            "state"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Shortcut-free equivalent of attacked_node(entity_location(entity), opponents(owner(entity))) over provided state; may be implemented as a pure shared helper."
    },
    "track_advance": {
      "category": "expression",
      "arguments": [
        "entity",
        "steps"
      ],
      "observed_signatures": [
        {
          "kind": "expression",
          "keys": [
            "entity",
            "steps"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Follow exactly abs(steps) ordered next/previous links in the designated cyclic track, include traversed nodes in a typed path; negative steps traverse inverse links and missing topology rejects."
    },
    "transfer_plan_valid": {
      "category": "expression",
      "arguments": [
        "plan",
        "state"
      ],
      "observed_signatures": [
        {
          "kind": "expression",
          "keys": [
            "plan",
            "state"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Validate a structured list of typed asset and currency transfers: all sources own assets, all referenced actors exist, debits remain permissible after cumulative reservations, no asset transferred twice, no cross-game references."
    },
    "transfer_resource": {
      "category": "effect",
      "arguments": [
        "amount",
        "source",
        "target"
      ],
      "observed_signatures": [
        {
          "kind": "effect",
          "keys": [
            "amount",
            "source",
            "target"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Debit and credit a declared resource field on source and target in one transition, rejecting underflow when prohibited."
    },
    "traverse_paths": {
      "category": "expression",
      "arguments": [
        "captured_blockers",
        "entity",
        "max_depth",
        "no_repeat_capture",
        "step_generator",
        "stop_on_crowning"
      ],
      "observed_signatures": [
        {
          "kind": "expression",
          "keys": [
            "captured_blockers",
            "entity",
            "max_depth",
            "no_repeat_capture",
            "step_generator",
            "stop_on_crowning"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Enumerate complete paths by applying a pure step-generator over temporary occupancy after each step; track visited captures and stop-condition; reject budget overflow, never truncate."
    },
    "trusted_random_int": {
      "category": "effect",
      "arguments": [
        "lower",
        "name",
        "upper"
      ],
      "observed_signatures": [
        {
          "kind": "effect",
          "keys": [
            "lower",
            "name",
            "upper"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Consume the next trusted server-supplied bounded integer and bind it by name; never generate client-provided entropy."
    },
    "vector": {
      "category": "expression",
      "arguments": [
        "column",
        "row"
      ],
      "observed_signatures": [
        {
          "kind": "expression",
          "keys": [
            "column",
            "row"
          ]
        }
      ],
      "status": "specified",
      "semantics": "Construct an immutable two-component signed integer grid direction."
    }
  }
}
```

## 6.5 Conformance gates

The portable definitions, OpenAPI and Mermaid graph must pass structural and cross-reference validation. Game execution, actual Drizzle migrations, deferred SQL constraints and production browser behavior must additionally be tested against real implementations. A definition is not fully conformant while any operator remains unresolved. Source-file nodes and expression nodes are a deterministic architecture/configuration representation, not complete function-body source code; full source generation additionally requires each function's executable algorithm body.
