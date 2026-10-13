# Object Model — Approved Architectural Deviations

**Status:** Target architecture approved 2026-10-13, not an inventory of working code. Product behavior is specified by [PRD.md](PRD.md), execution by [PLAN.md](PLAN.md), current implementation status by [SCRATCHPAD.md](../SCRATCHPAD.md). The [original Czech UML transcription and images](reference_diagram.md) are preserved unchanged.

## Deliberate deviations and decisions

| Area | Approved final design | Why / distinction from original diagram |
|---|---|---|
| Language and names | English domain names remain canonical; retain appropriate Czech reference aliases for Python domain types where required. | The Czech class captions are source-reference names, not a mandate to duplicate implementation. |
| Deployment boundary | Game engine is a headless Python package; FastAPI API on Vercel Functions, Supabase persistence/realtime/Auth, React web UI and a Tauri wrapper loading **the identical hosted web app**. | Original diagram described one local Python/Tkinter MVC application. Explicit approval 2026-10-13 replaces Tkinter and local-only runtime. |
| Package layout | `packages/engine`, independent `packages/chess`, `packages/english_draughts` and `packages/international_checkers`, plus `packages/server`, `packages/web`, `packages/desktop`; no `src/games` and no `engine/view` production UI. | Shared reusable model and game-specific declarations; original Python view responsibilities map to React. |
| Configurations | Shipped game definitions are immutable `config.json` files. User variants are validated JSON stored in Supabase and frozen for each game. Engine/session constructors receive selected configuration explicitly. | Replaces historical all-Python runtime configs and mutable local configuration directories. |
| Rule extensions | All **user-authored and shipped game behavior is declarative JSON**, interpreted by trusted generic Python hook operations (`permits_move`, `available_moves`, `outcome`, `on_move_made`, `status`). | User approved complete removal of executable Python rule/quest authoring; former Python Rule subclasses as an extension surface are superseded. |
| Hooks and effects | Bounded versioned typed JSON condition/effect AST, deterministic composition, schema-validated inputs and safe evaluator. Rules only propose; game manager alone authorizes and commits a move. | Arbitrary extension algorithms cannot be promised by JSON; approved rules and customization must fit the generic vocabulary. |
| Quests | JSON definitions, timing, progress, conditions and rewards; per-player per-game progress, user-level achievement persistence, XP derived from rewards. | Supersedes user-authored Python Quest subclasses and global shared completion. |
| Board and pieces | Generic geometry/capabilities only; all starting setup, piece types, symbols, movement and royal behavior come from JSON. No engine `king`/`pawn` hardcodes or implicit 8×8. | Avoids chess coupling and enables independent English and international draughts. |
| Moves and rule authority | Ordered multi-hop moves, single engine legal-commit boundary, deterministic outcome precedence; no user-manager direct execution. | Draughts chains and secure online play require authoritative transitions. |
| Clock | Explicit control and per-player state with trusted timestamps, persisted for serverless restart; no implicit time or invalid-ID fallback. | Original sketch lacked increments and hosted timestamp model. |
| User | Supabase Auth identities, registered and anonymous guests, server-side membership/authorization, persistent history and ratings. | Original `UserManager` is not an auth provider and cannot authorize gameplay. |
| Settings | React schema-driven forms for Board, Pieces, Rules, Quests, Clocks; **no Python/JS code editor**. | The original sketch did not depict extensible validated settings or web GUI. |
| Presentation | Original GameView/PlayerView responsibilities remain but are React components; no duplicate Python view types are required solely to mirror the diagram. | Approved browser/Tauri platform change. |
| Exporters | One trusted game-owned class per format extending a generic single-format interface; accurate PGN/SAN and six-field FEN **export only**. | No engine format switch. FEN import approved earlier is explicitly **withdrawn 2026-10-13**. |
| Persistence/realtime | Atomic versioned persisted game state, moves and per-user progress in Supabase; authorized Realtime notifications with snapshot reconciliation. | No durable shared process memory in serverless runtime. |

## Original reference ambiguities

- The original diagram writes `GameVeiw`; it is a spelling error, not a separate runtime component. Reference names remain archived in [reference_diagram.md](reference_diagram.md).
- One reference page uses `List(Hrac)`, another `List(Uzivatele)`. Distinct users and participants are intentionally linked rather than conflated.
- Only `Kůň` has a clearly depicted inheritance edge among the chess-piece boxes; other relationships were not proven by that sketch.
- The free-standing `Extends` mark does not establish an export-writer inheritance chain; game-owned format classes are a deliberate deviation.
- `ChessNotationWriter` is the original reference's feature inventory, not a mandatory single class or multi-format dispatcher.

## Evidence boundary

Code-generated implementation UML shows only what is currently checked out, not the final approved architecture or behavior. It must not be confused with the original fixed reference drawings. Final implementation graph and red/green comparison SVG require visual review. The initial consolidated branch retains corrected #218 code and selected historical game-owned source **candidates**, plus all older commits in git ancestry; that does **not** establish that Python JSON hooks or online play are already implemented.

See [PLAN.md](PLAN.md) for implementation gates and [SCRATCHPAD.md](../SCRATCHPAD.md) for verified progress.
