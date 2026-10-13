# BoardGamesWithQuests — Product Requirements Document

**Status:** Approved target requirements; **not a claim of existing implementation**.  
**Version:** 2.0 — online JSON-driven architecture, 2026-10-13.  
**Execution authority:** [PLAN.md](PLAN.md), [#129](https://github.com/marius-patrik/BoardGamesWithQuests/issues/129). Progress: [SCRATCHPAD.md](../SCRATCHPAD.md). Deviations: [object_model.md](object_model.md). Original diagrams: [reference_diagram.md](reference_diagram.md).

## 1. Product

A configurable online **two-player** board-game app, with Python engine shared by orthodox chess and WCDF English draughts. Players select or create validated JSON variants: board, starting position, piece movements and glyphs, active rules and quests, and clocks. Chess is the preselected shipped game, not an implicit engine constructor default. Checkers demonstrates engine neutrality: no checkers-specific engine branch.

The complete user interface is a **React/Rsbuild** website, publicly hosted on **Vercel**. **Tauri** is a thin desktop wrapper loading that same website. **FastAPI Python Functions on Vercel** run all authoritative game logic. **Supabase** provides persistent game data, Auth (registered and guest identities), and Realtime event updates. Each game has precisely two participant slots; creating/joining a match needs no separate room concept. No leaderboard, tournament or other unrequested features.

## 2. User needs

| Actor | Required outcome |
|---|---|
| Player | Create/join matches, configure variants through forms, see board, legal moves, players, clocks, captures, progress, history and correct result. |
| Guest | Play immediately with an anonymous authenticated identity and nickname, without needing an email account. |
| Registered user | Register/sign in, manage identity and persisted game history, quests and ratings. |
| Teacher/grader | See supplied reference UML preserved and supported by a recorded, explicit set of modern architecture deviations; demo running public game. |
| Maintainer | Behavior verified against requirements, with one documented architecture, single integration PR, honest CI/release statuses. |

## 3. Fixed constraints

- **JSON only for game configuration, including rules/quests/hooks.** No user-authored executable code, custom Python modules, JS snippets, unsafe expressions or code editors.
- Python can implement **trusted generic predicates/effects/operations**, never untrusted user code; the JSON vocabulary and its limits must be validated for all shipped-game requirements.
- No hard-coded game identity, royal king logic, pawn names or default board dimensions in shared engine. Domain-significant values are supplied explicitly.
- No external chess rules library replacing the hand-implemented engine, unless separately approved. Modern approved runtime libraries for web/API/Supabase are allowed.
- All public multiplayer state changes are authenticated, authorized, atomic and durable.
- Existing source/reference UML is preserved as original evidence; intentional divergence is registered in `object_model.md`.
- Permanent tests must assert real gameplay, API, UI and persistence behavior. The retired test suite is not revived; rebuild at #239.

## 4. Configuration and extension model

`packages/chess/config.json` and `packages/checkers/config.json` are immutable shipped definitions. Both use the **same versioned declarative schema**, with board placements, piece declarations, rule/quest hooks/conditions, game outcomes, symbols, clock controls, metadata and applicable export formats. Copying/creating a variant means copying validated **data**, not creating/importing a new Python module. User variants persist in Supabase.

The engine's five conceptual rule hooks are `permits_move`, `available_moves`, `outcome`, `on_move_made`, `status`. The engine implements generic interpreters for typed conditions, logical composition, comparisons, counts, board queries, movement vectors, per-session state and authorized effects. A rule does not commit a move; the game manager owns the final transition. Quests are similarly declarative, report progress and rewards, and are scoped per player. No user-authored rule/quest subclass or executable configuration path.

Forms for Board, Pieces, Rules, Quests and Clocks derive their allowed fields and operations from the shared schema. Config validation must fail closed, without corrupting valid saved state or exposing arbitrary evaluation.

## 5. Naming and source UML

English canonical names are used for shared domain types; the original Czech naming and reference mapping remain in [reference_diagram.md](reference_diagram.md). Where the existing non-UI Python implementation needs Czech aliases, they bind to the same canonical domain class, not a parallel runtime. Canonical chess knight is `Knight`, not `Horse` or `Tower`. Original `GameView`/`PlayerView` are now **React component responsibilities**, not classes to keep inside `engine/view`. See [object_model.md](object_model.md) for rationale and traceability.

## 6. Package boundaries

```text
packages/
  engine/     generic Python board, moves, declarative rule/quest runtime, lifecycle
  chess/      immutable chess config.json and game-owned format writers
  checkers/   immutable WCDF checkers config.json and game-owned format writers
  server/     FastAPI/Vercel, authorization, Supabase transactions and API
  web/        React/TypeScript/Rsbuild/Bun UI, typed API client
  desktop/    Tauri wrapper loading hosted web app
```

Python domain orchestration stays in `engine`. UI/window controllers and Tkinter do not. Supabase Auth owns account credentials; server owns player authorization; engine owns rule/turn legality. Source files held by the historical stack are not automatically delivered by being present in Git history.

## 7. Functional requirements

### 7.1 Game data

| ID | Requirement |
|---|---|
| FR-1 | Board dimensions are configurable in rows and columns. |
| FR-2 | The starting position is either the shipped one or edited square by square. |
| FR-3 | A piece declares a name, a white symbol, a black symbol, movement vectors, attack vectors, a jump flag and a `kind` label. A piece may be added to the palette and placed on the board. |
| FR-4 | Symbols are **unicode chess glyphs declared as data**. The board renderer and the notation writer hold no knowledge of piece types; both read what the piece declares. |
| FR-5 | A piece may additionally declare an optional FEN character. Without one it has no FEN representation. |
| FR-6 | Clocks declare an initial time and an increment. |
| FR-7 | A game runs under exactly one configuration and exactly one board. |

### 7.2 Declarative rules

| ID | Requirement |
|---|---|
| FR-8 | The engine interprets JSON-defined rule instances through five generic hooks: `permits_move`, `available_moves`, `outcome`, `on_move_made`, and `status`. A rule contains declarative configured parameters and isolated per-game state. The hooks are implemented by trusted generic engine operations; users do not write subclasses. |
| FR-9 | `permits_move` and `available_moves` restrict/describe allowed actions, `outcome` proposes a result, `on_move_made` updates configured per-session state, and `status` supplies display information. Side effects are bounded, schema-validated declarative effects, never arbitrary executable code. |
| FR-10 | Rules propose permitted actions, status and outcomes; a single engine coordinator authorizes moves, commits transitions and resolves outcomes. No rule implementation may bypass the central commit boundary. |
| FR-11 | `Result` records kind, winner, reason and precedence. Conflict resolution is deterministic, with appropriate decisive/draw policy and tie order. |
| FR-12 | Configured rule parameters are stored in immutable JSON game-definition snapshots; mutable rule state is isolated by game and must be serialized for serverless restart recovery. A newly created game resets runtime state. |
| FR-13 | A move may consist of **several hops**. A capture chain in checkers is one move the player makes, not several. |
| FR-14 | No piece type is special to the engine. Whether a position has a king is a rule, not a lookup by type name. |
| FR-15 | Board size is not restricted to 8×8. Rank-relative rules are **generalised, not disabled**: the home rank and the castling and knight-forward files are derived from the configured board. |
| FR-16 | The JSON hook vocabulary can express all applicable chess rules from `chess_rules.md`, including castling, en passant, promotion, check, mate, stalemate, draw/repetition, claims and timeout material conditions. |
| FR-17 | Generic predicates, comparisons, counts, state queries, logical composition and bounded effects support all approved customization without game-name-specific engine branches. The system does not promise arbitrary user-written algorithms or executable scripts. |

### 7.3 Declarative quests

| ID | Requirement |
|---|---|
| FR-18 | `Quest` is a data-defined game objective evaluated by the engine through configured hooks and conditions, not a user-authored Python subclass; quest evaluation has the conceptual `validate` result required by the reference. |
| FR-19 | Quest logic is JSON configuration interpreted by trusted generic engine primitives. No separate user-authored condition class, source code module, or Python plugin is required. |
| FR-20 | Quests declare identity, name, description, parameters, timing, progress measurement, completion criteria and reward as schema-validated JSON. |
| FR-21 | A quest declares evaluation timing (`after_move` or `at_game_end`), or another explicitly supported lifecycle trigger defined in the schema. |
| FR-22 | A quest exposes progress as current and target, not only a completion boolean. |
| FR-23 | Configured quests are held per game; their progress and completion are isolated per player; completed achievements are persisted against the user's account. |
| FR-24 | Total experience is **derived** from the quests a user has completed, so the user type gains no new field. |

### 7.4 Game definitions and persistence

| ID | Requirement |
|---|---|
| FR-25 | Shipped `chess` and `checkers` are independently registered Python packages with a root `config.json`; board, pieces, rules, quests and clocks are JSON. The engine owns their schema and generic interpreter, not executable game-authored configuration. |
| FR-26 | The immutable shipped chess definition provides orthodox 8×8 pieces, setup, rules and clocks as JSON. The UI may preselect this definition; constructing a playable engine session always receives its selected configuration explicitly. |
| FR-27 | Shipped default definitions cannot be edited/deleted; a variant begins as a validated copy. |
| FR-28 | Users can create, rename, duplicate, edit and delete user-owned game variants through JSON-backed settings. |
| FR-29 | User variants persist as versioned, validated JSON in Supabase; a running game uses an immutable snapshot and survives serverless restarts. Runtime configuration does not depend on writable package directories. |

### 7.5 Schema-driven settings

| ID | Requirement |
|---|---|
| FR-30 | The Settings interface contains an explicit selector identifying which configuration is being edited. |
| FR-31 | Settings exposes Board, Pieces, Rules, Quests and Clocks as declarative configuration sections. |
| FR-32 | All configurable game data, including rule and quest logic composition, is exposed through schema-driven forms; no source-code editor is required. |
| FR-33 | Rule and Quest sections provide a declarative form/builder for composing supported JSON conditions, hooks, parameters and effects; no Python/JS authoring or execution. |
| FR-34 | The settings editor validates JSON schema, operation references, nesting limits and semantic constraints before saving; invalid configurations never replace valid definitions. |
| FR-35 | Settings supports save, reset, cancel and appropriate variant duplication/edit/delete actions, with persistence affecting subsequent games. |

### 7.6 Browser gameplay

| ID | Requirement |
|---|---|
| FR-36 | The web game-start experience offers a game/configuration selector, Settings action and Start/create/join flow for exactly two players. |
| FR-37 | The React board renders coordinates, declared glyphs, active squares and legal-move highlights; gameplay comes from the authoritative engine. |
| FR-38 | Both player panels show authenticated/guest identity, clock and captured/lost pieces. |
| FR-39 | The active turn is indicated from authoritative game state. |
| FR-40 | Durable game move history is visible in the React UI. |
| FR-41 | Game status and alerts display the actual terminal reason in a footer/status surface. |
| FR-42 | Per-player quests appear as cards showing progress and reward; both players' quest logs are visible. |

### 7.7 Notation and export

| ID | Requirement |
|---|---|
| FR-43 | Export is one class per format, extending a base exporter named `ExportWriter`, living in the configuration that uses it. There is no format switch and no format-name string anywhere in the engine. |
| FR-44 | *Letter* — the move is rendered in algebraic notation with piece letters, capture markers, promotion and castling notation. |
| FR-45 | *PGN* — real PGN: a seven-tag roster **derived from the game** (event, site, date, round, both players, result), and movetext in Standard Algebraic Notation, including piece disambiguation, castling notation, promotion, and check and mate suffixes. |
| FR-46 | *FEN* — all six fields are **computed from the game state**: placement, side to move, castling rights, en passant square, halfmove clock and fullmove number. No field is hard-coded. |
| FR-47 | **WITHDRAWN (2026-10-13):** FEN import/round-trip is not a product requirement; verify accurate FEN export against known positions instead. |
| FR-48 | Game transcript metadata derives from actual event/site/date/players/result state; never hardcode placeholders. |
| FR-49 | Stenographic game transcript export uses a standard or explicitly configured standard-library codec; no user-authored executable compression. |
| FR-50 | An authoritative durable transcript records every move and relevant event separately from export formats. |
| FR-51 | A format that belongs to one game ships with that game. FEN and PGN are chess formats and therefore live in `packages/chess/export/`; a game with no FEN representation has no FEN exporter, because the structure says so rather than a capability check. |
| FR-52 | **WITHDRAWN (2026-10-13):** Do not implement or advertise a FEN reader; only the six-field FEN exporter in FR-46 remains. |

### 7.8 Shipped games

| ID | Requirement |
|---|---|
| FR-53 | `packages/chess/` is a complete, correct orthodox chess configuration. |
| FR-54 | `packages/checkers/` is a complete, correct English draughts configuration: twelve pieces a side, men moving one square forward diagonally, kings moving one square diagonally, **mandatory capture including chains**, promotion to king on reaching the far rank, and a win by immobilisation or by losing all pieces. |
| FR-55 | Adding/checking the checkers JSON definition requires no conditional branch in generic engine behavior; game-specific implementations never leak into the engine. |

### 7.9 Application and runtime

| ID | Requirement |
|---|---|
| FR-56 | Authoritative game logs and history are stored durably in Supabase and exposed through authenticated APIs. A local development log file is optional, not a source of truth. |
| FR-57 | Python engine/server packages are installable and declare FastAPI/Supabase and any real runtime dependencies. Frontend dependencies are managed by Bun; release versions derive from Git tags. |
| FR-58 | A documented public Vercel URL loads the web application and two players can complete a game to a valid outcome against the Python engine. |
| FR-59 | The deployed application has an explicit FastAPI ASGI entry point and a built Rsbuild frontend; Tauri wraps that same hosted frontend. No Python/Tkinter GUI entry point is required. |

### 7.10 Domain model and UI responsibilities

| ID | Requirement |
|---|---|
| FR-60 | Supabase Auth registers, authenticates and identifies persistent and anonymous guests. Profiles have username/display name where applicable and historical rating/quest data; player assignments reference stable identities; duplicate IDs and unauthorized links are rejected. |
| FR-61 | The generic validator exposes candidate/legal moves and state/outcome queries through JSON-configured rules; royal/check semantics are game configuration data, never piece-name tests in engine. |
| FR-62 | One GameManager owns the current board, active player, two positions, move, configured clocks, history, rule/quest state and validator, and serializes a consistent session snapshot for durable storage. |
| FR-63 | Game clocks use explicit time controls and participant IDs, trusted timestamps, invalid-input rejection and recoverable state independent of continuously running functions. |
| FR-64 | A durable append-only game transcript records moves, action types, events and results without accidental truncation; authenticated clients can retrieve it. |
| FR-65 | React UI interaction chooses squares and sends a move intent to FastAPI; the Python engine controller authorizes and commits through its single public domain operation. |
| FR-66 | The React board view subscribes/refetches persisted authoritative state after committed changes, reconnection and missed Realtime messages. |
| FR-67 | The React player panels similarly refresh from authoritative player identity, clock, captures and quest progress. |

### 7.11 Online application, security and delivery

| ID | Requirement |
|---|---|
| FR-68 | Game configuration is only validated JSON. User-provided Python, JavaScript, arbitrary code expressions, dynamic executable imports and runtime eval/exec are prohibited. |
| FR-69 | JSON rule/quest hooks use a typed, bounded, versioned AST with schema-checked operations, nesting, references, effects and complexity limits. |
| FR-70 | The public game API runs Python engine/domain logic in FastAPI hosted as Vercel Python Functions; functions have no required persistent in-memory state. |
| FR-71 | Supabase Postgres stores authoritative game snapshots, revisions, history, users, settings, quest progress and results. Every game is reconstructible after a serverless restart. |
| FR-72 | Move submission verifies Supabase-authenticated identity and game membership, enforces correct turn and rules, and atomically commits a single revision or rejects conflicts/duplicates. |
| FR-73 | Supabase Auth supports registered accounts and anonymous guests with nicknames; RLS and server authorization isolate participants' data. |
| FR-74 | Supabase Realtime notifies authorized participants of committed updates; clients handle reconnect, gaps, duplicate/out-of-order events by fetching authoritative snapshots. |
| FR-75 | The sole GUI is React + TypeScript + Rsbuild + Bun + Tailwind + shadcn/ui + Motion + Lucide/lucide-animated; the server supplies generated typed OpenAPI contracts. |
| FR-76 | The Tauri desktop package loads the **same deployed web UI**, does not maintain another frontend or bundle a Python server, and uses minimal native capabilities. |
| FR-77 | Two Vercel projects deploy the frontend and Python API from compatible reviewed Git revisions; Supabase is the only persistent hosted service. Hosting aims to stay within free tiers, verified before public release. |
| FR-78 | The public application supports exactly two participants per individual game, create/join invitation, separate concurrent games and correct resilience; it has no additional classroom room or leaderboard. |
| FR-79 | The public deployment must be usable for the class presentation: guests on a shared IP, real browsers, concurrent games, match completion, clock correctness and reconnection tested against quotas. |
| FR-80 | The permanent suite is rebuilt from zero against final behavior after integration (#239); no green CI/diagram/build result alone certifies playability. |
| FR-81 | Shipped configurations are immutable; authenticated users can save editable JSON variants, and each game pins an immutable validated config snapshot. |
| FR-82 | Repository and release artifacts have one active plan, correct GPL-3.0 metadata, one `repo.dfconfig`, updated DarkFactory pin, aligned code and accurate diagrams, with explicit approval before merge. |

## 8. Acceptance evidence

Deliver a complete public two-player game from guest sign-in through game creation/joining, alternating legal moves, correct result, persisted history, reconnection and serverless function restart. Exercise real rule/quest JSON customization, saved variants, orthodox chess and WCDF checkers, correct PGN/SAN and FEN export, GUI behavior, account isolation, access policies, atomic double-submit handling, clocks, Tauri wrapper, classrooms on shared network, and verified Vercel/Supabase free-tier quotas. Final permanent behavior suite is #239. **No documentation check or code compilation substitutes for this evidence.**
