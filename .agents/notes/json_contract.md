# Versioned JSON rules and quest contract

## Configuration ownership

Version 2 is a validated JSON envelope. The parser accepts at most
256 KiB and rejects duplicate or unknown top-level fields, invalid clocks,
unknown pieces, overlapping placements and executable extensions.
Board dimensions, placements, movement vectors, appearance, captures, rules,
quests and clocks are data owned by each game configuration.

The top-level keys are `schema_version`, `name`, `title`, `default`,
`playable`, `board`, `pieces`, `clock`, `exports`, `appearance`,
`rules`, `quests`. The engine never branches on `name` or `piece_type`.
Games remain marked non-playable until their complete G3 rulebooks are verified.

## Hooks, conditions and effects

The five hooks are `available_moves`, `permits_move`, `on_move_made`,
`outcome` and `status`. A rule has the fields `id`, `hook`, `when`,
`effects`. A quest has `id`, `description`, `when`, `reward`.

Conditions are tagged typed AST nodes `true`, `false`, `all`, `any`,
`not`, `test` and `compare`. Comparisons support `eq`, `ne`,
`lt`, `lte`, `gt`, `gte` and membership `in`. Queries and effects
must belong to the static whitelists in `schema.py`. Expressions are at most
12 levels deep and 256 nodes, with at most 128 rules and quests each, and at
most 32 effects per rule. All game-authored values must be finite JSON;
no Python or JavaScript, evaluation of text, imports or dynamic plugin code.

Parameters and comparison values can be literals, bounded query expressions or
typed references `{"ref":"move.start"}`, `{"ref":"move.end"}`, etc.
References may enter only a recognized trusted context root:
`move`, `player`, `clock`, `board`, `game`, `quest`, `event`,
`rule`; identifiers must be safe, at most four path components, and refer
to actually bound values. Unbound/unknown references fail closed. All references
are resolved into copied JSON values, not Python attributes or executable code.

`HookInterpreter` evaluates rules in declared order, creates a typed
`HookEvaluation` and returns an ordered immutable effect plan. Evaluation does
not authorize or mutate a game. Applying effects, deterministic conflict/
outcome priority, event persistence and atomic gameplay commits are separate
G2 requirements. No missing query is implicitly false, legal or complete.

## Game-neutral primitive expressiveness

The rule vocabulary supports direct board occupancy, geometric attack and path
queries; scoped rule state, move and history attributes, temporary targets,
special rights, promotion choices, canonical repetition, clocks, capture chains
and outcomes. A capture policy is declared per piece in game-owned JSON as
`{flying, land_anywhere, deferred_removal, max_nodes}`.

The generic `CaptureEnumerator` implements bounded short capture chains and
ray captures with configurable landing range. Deferred removal leaves captured
pieces as blockers while prohibiting recapture of the same piece. This is
required to represent international draughts independently of English draughts.
The engine itself does not know a game's identity.

The executable primitives in `scripts/probe_g1_semantics.py` demonstrate:

| Rule family | Proven primitive and data-level expressiveness |
| --- | --- |
| Chess | Geometric attacked transit square, explicitly stored castling rights, en-passant target, promotion option membership, canonical-position repetition and dynamic move references |
| English draughts | Two-hop capture discovery, mandatory-capture denial, short king landing behavior |
| International draughts | 10×10 flying king paths, backward man capture, deferred capture blocking and maximum-piece capture comparison |

These are **primitive/design proofs**, not complete rulebook conformance:
FIDE legal move enumeration/check safety, castling move effects, en-passant
execution, all promotions and draws, international capture edge cases, clocks
and outcomes must pass full G2/G3 behavior and G6 independent tests before any
game's `playable` flag becomes true. No production path falls back to
geometric pseudo-moves when rules are absent.

## Supabase persistence boundary

The deployed `bgwq` schema is private and not intended for direct browser
access. Its `games` table owns the immutable configuration snapshot, two
distinct participants, game JSON state and optimistic revision; `events`
records one immutable event for each committed revision. Both enable RLS,
and neither anonymous nor authenticated client roles have direct schema, table
or function access. The private `commit_revision` function accepts a verified
actor, expected revision and already validated new state, atomically updates
the revision and appends one event. It rejects an outsider and stale retries.

**The function does not validate chess or draughts moves.** The authoritative
server must verify the Supabase JWT identity, game participation and full
configuration legality before invoking it; only trusted server-side credentials
may call it. This boundary is not a direct client RPC.

The canonical migration is
`supabase/migrations/20261013145509_private_game_persistence.sql`.
The reproducible SQL transaction/security probe is
`scripts/fixtures/g1_supabase_atomicity.sql`.

## Deployment and capacity boundaries

Vercel serves the single Rsbuild web bundle and the FastAPI app as separate
projects. The public health/catalog routes are explicitly non-playable.
Future API requests must use serverless-safe database connections and a
revision-checked authoritative session; never rely on process-local memory.

Supabase supports anonymous sign-ins but anonymous users have the
`authenticated` Postgres role. JWT membership must use `auth.uid()`
or independently verified identity, never user-editable metadata.
The documented shared-IP anonymous signup allowance is a classroom capacity
risk (normally 30/hour/IP). Validate the actual project's settings and a
classroom-size signup rehearsal before claiming free-tier capacity in G7.
Unauthenticated/public game APIs and sign-in are not provided until G4.
