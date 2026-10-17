# Versioned JSON rules and quest contract

## Configuration ownership

Version 2 is a validated JSON envelope. The parser accepts at most
256 KiB and rejects duplicate or unknown top-level fields, invalid clocks,
unknown pieces, overlapping placements and executable extensions.
Nested board, placement, piece, symbol, clock and appearance objects reject
unknown fields. Appearance accepts optional `light_square` and `dark_square`
hex colors. Pieces accept optional `notation`, single-letter `fen`,
`color_relative`, `capture_policy`, `initial_moves` and `promotion`; initial quiet offsets
are available only before the piece moves and mirror by side when configured.
Malformed encodings and excessive nesting produce a configuration error.
The same byte limit applies to directly validated decoded documents.
Validated definitions detach from caller data and recursively freeze objects
and arrays. `freeze_json` protects the same invariant for resolved effect plans;
`thaw_json` creates detached dictionaries/lists for serialization or editing.
A complete document permits 65,536 nodes and 32 levels; expression limits below
remain smaller independently of board size.

Board dimensions, placements, movement vectors, appearance, captures, rules,
quests and clocks are data owned by each game configuration.

The top-level keys are `schema_version`, `name`, `title`, `default`,
`playable`, `board`, `pieces`, `clock`, `exports`, `appearance`,
`rules`, `quests`, with optional `initial_state`, `halfmove_reset`, `starting_side` and
`position_identity`.
`starting_side` is the strict integer 1 or -1 and defaults to 1. It selects the
initial active participant and clock without changing side identities. Explicit
field presence is pinned in the snapshot; omitted defaults preserve replay of
existing snapshots.
The engine never branches on `name` or `piece_type`.
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
Query/effect parameters also accept recursively nested typed
`{"query":"operation","params":{...}}` nodes. Operation names, expression
shapes, references and bounds are checked before evaluation; resolved effect
parameters are checked again. Strings are never interpreted as expressions.

`HookInterpreter` evaluates rules in declared order, creates a typed
`HookEvaluation` and returns an ordered immutable effect plan. Evaluation does
not authorize or mutate a game. Effect parameter keys and types are checked
before evaluation and again after resolving references. Parameters are:

| Effect | Required parameters | Optional parameters |
| --- | --- | --- |
| `permit`, `deny` | none | `reason`, `target` |
| `move_piece` | `start`, `end` | none |
| `offer_move` | `start`, `end` | `hops`, `promotion`, `effects` |
| `capture_piece` | `square` | none |
| `replace_piece` | `square`, `kind` | none |
| `set_state` | `name`, `value` | none |
| `increment_state` | `name`, `amount` | none |
| `record_event` | `name` | `payload` |
| `propose_outcome` | `kind`, `cause`, `winner`, `priority` | none |
| `complete_quest` | `quest`, `player` | none |
| `set_clock` | `player`, `seconds` | none |
| `set_rights` | `name`, `value` | none |
| `set_target` | `name`, `value` (square or null) | none |

Coordinates are integer pairs; participant values are nonempty identities or
explicit side values; clocks, counters and priorities are bounded integers;
rights are booleans. State values and event payloads remain bounded JSON.
Board bounds, membership and transition legality require session validation.
The domain session applies supported transition effects to isolated candidate
state, resolves declared outcomes and publishes only a completely validated
transition. Durable database commits require the server persistence adapter.
No missing query is implicitly false, legal or complete.

## Scoped snapshot queries

`SnapshotQueries` accepts a detached finite JSON snapshot of at most 1 MiB,
with nesting bounded to 64 levels. Each result is a defensive copy. Unknown
fields required by a query, malformed selectors and incorrect types are errors;
missing values never grant permission. JSON equality and membership compare
nested values by exact type, including distinctions between booleans, integers
and floating-point values.

`active` and `opponent` identify the evaluating participant and their opponent;
they do not change the canonical `turn` query. `turn` reports the participant
side whose move is due in the evaluated game state. Named lookups use
`{"name":"identifier"}` for `rule_state`, `special_rights`,
`temporary_target` and `move_attribute`. Captures use an explicit
`capture_paths` object with exactly `active` and `opponent` arrays. Each route
contains `start` and nonempty ordered `steps`, with `landing` and `captured`
coordinates per step; repeated captures of one square are rejected.

| Query | Parameters | Snapshot field and result |
| --- | --- | --- |
| `capture_paths` | `side` | Whether the selected complete route array is nonempty |
| `capture_count` | `scope: candidate` or `maximum` | Candidate capture count or maximum evaluating-participant route length |
| `promotion_options` | `side` | Explicit side-indexed configured piece-kind list |
| `clock_remaining` | `side` | Explicit side-indexed nonnegative seconds |
| `legal_move_count` | `side` | Explicit side-indexed computed legal count |
| `participant` | `side` | Stable `id` and integer `side` from participants |
| `quest_progress` | `side`, `name` | Participant quest's `active`, `target`, `completed` |
| `repetition_count` | `scope: position` | Exact observed-position key occurrences in position history |
| `halfmove_count` | none | Explicit nonnegative halfmove count |
| `history_count` | none | Number of committed event records |
| `last_action` | none | Last action object or explicit null |
| `position` | none | Explicit canonical position data object |

These queries read authoritative inputs; supplying a count or key does not
prove that its producing algorithm implements a shipped game's rules.

## Declarative special movement and lifecycle

`available_moves` emits only `offer_move` effects. Each resolved offer has an
owned in-bounds `start` and `end`, optional ordered `hops` ending at `end`, an
optional configured promotion choice and at most 32 validated auxiliary effects.
Auxiliary operations are `move_piece`, `capture_piece`, `replace_piece`,
`set_state`, `increment_state`, `set_rights`, `set_target` and `record_event`.
The engine derives the moving participant and actual occupied captures. Clients
submit the same three-field intent and cannot assert auxiliary movement or
captured pieces. Duplicate offers for one intent are ambiguous and fail closed,
even when their effect plans are identical. Matching offers own their candidate;
invalid auxiliary effects cannot fall back to ordinary geometry.

Before publication the session prepares the isolated board, captures, automatic
or selected promotion, auxiliary effects and `on_move_made` effects exactly once.
It evaluates `permits_move` against the observed snapshot with access to that
fully projected board. An explicit permit is required and any denial wins in
all rule orders. Legal previews and replay use the same preparation boundary.
`available_moves` cannot request recursive legal counts or an unavailable
projected board; those queries produce a resolution error.

Geometric board queries accept optional `phase: before` or `after`.
`pieces_safe` requires explicit `kind`, `side` and `phase`, and checks all pieces
with that configured role against opposing geometric attacks. A missing role
returns false. The phase selects the pre-transition or fully prepared board, including
auxiliary captures and movement; no royal type is hard-coded. `turn` remains the
canonical snapshot turn and does not accept a board-phase selector. All attack
traversal shares the aggregate operation work budget.

| Value query | Exact parameters | Result and failure policy |
| --- | --- | --- |
| `integer` | `operation`, `left`, `right` | Signed int64 `add`, `subtract` or `floor_divide`; booleans, invalid operations, zero divisors and overflow are errors |
| `square_offset` | `square`, `offset` | In-bounds source translated by an integer pair bounded to ±255; out-of-board result is null, malformed operands are errors |
| `json_value` | `value`, `path` | One to four string keys or integer indices 0–127, with explicit -1 selecting the last array element; missing entries/container mismatch return null, malformed paths are errors |

A null value is data, never an implicit permission. Conditions must explicitly
match their intended non-null facts before an offer or permit can be emitted.
These bounded operations derive coordinates and last-action facts from JSON;
they provide no executable expressions, imports, arbitrary attributes or loops.

`initial_state` contains exactly `rule_state`, `special_rights` and
`temporary_targets` objects. State values are bounded JSON; rights are booleans;
targets are in-bounds squares or null. They are frozen in the selected definition
and initialize independent session state. Existing targets expire to null on
an accepted move before configured auxiliary/post-move `set_target` effects
create replacements. A rejected transition does not expire or replace targets.

Optional `halfmove_reset` supplies an additional condition evaluated against
the pre-transition board and snapshot, with server-derived base and offered captures,
before post-move hooks. Any capture resets the counter; the condition can reset
it for another configured movement. Post-move capture effects also reset it.
Otherwise an accepted move increments the counter once.

Per-piece `promotion` declares exactly `rank: far`, `options`, `mode` and
`stop_capture`. Options name existing configured kinds. Piece identifiers and
move promotion choices share a maximum of 128 characters; longer identifiers
are rejected before any transition. Mode `choice` requires
an explicit offered choice on the final far-rank landing; legal enumeration
includes each choice. Mode `automatic` requires one option and accepts no client
promotion choice. Side 1 reaches row 0; side -1 reaches `rows - 1`, matching the
configured board convention. When `stop_capture` is true, capture enumeration
ends at the first far-rank landing and crowns there. When false, the moving
piece continues its complete chain and crowns only if its final landing reaches
the far rank. Crossing that rank and finishing elsewhere does not crown.

## Authoritative domain session

`GameManager(definition, game_id, participant_ids, started_at_ms)` requires
an explicitly validated definition containing a `permits_move` hook and exactly
two distinct participant identities. A synthetic test definition can exercise
the session while shipped configurations remain non-playable. No constructor
selects an implicit game, board or clock.

A move intent serializes as exactly `start`, `hops`, and `promotion`.
`hops` is the nonempty ordered landing sequence; its final element defines the
destination. Coordinates are nonnegative integer pairs, consecutive empty hops
are invalid, and the caller cannot assert captures or carry mutable piece
objects. A capture-policy move must match one complete server-enumerated route.
The session derives captures from board state, applies them as one action and
marks the moving piece as moved. Quiet candidates use declared movement and
initial vectors. Authorization requires an explicit `permit`; any `deny`
rejects the candidate. Geometric availability alone never authorizes a move.
Legal enumeration prepares the same isolated movement, clock, post-move effects
and quest evaluation used by submission; candidates with failing transition
effects are excluded without changing the observed session. Outcome arbitration
runs after preparation and cannot substitute for complete rulebook legality.

`submit_action(actor_id, expected_revision, action_id, action, now_ms)` is the
single action boundary. The host supplies verified identity and trusted integer
milliseconds. Actions are closed objects with exactly these fields:

| Type | Required fields |
| --- | --- |
| `move` | `type`, `move` (the three-field move intent) |
| `resign` | `type` |
| `claim_draw` | `type`, `claim` (configured outcome-rule ID), `intended_move` (move intent or null) |
| `timeout` | `type` |

Unknown actions, missing/extra fields and client assertions of winners, elapsed
time or expired side are rejected. `submit(..., move, ...)` delegates to the
same boundary. Membership, revision, terminal state and request identity apply
to every action. Moves require the active participant before clock expiry.
Resignation may be submitted by either participant; timeout may be reported by
either participant at or after the active clock deadline. Draw claims require
the active participant before expiry and exactly one named outcome rule whose
condition matches and proposes a draw with no winner. Claim IDs retain the
configuration's nonempty string contract, bounded by 256 KiB of UTF-8 rather
than the shorter session/action identifier limit. All matching outcome rules
still participate in arbitration; an overriding decisive result rejects a claim.

Terminal hooks receive `event.type`, `event.claim` (null outside claims),
`event.actor` and authoritative `event.expired_side` (null before expiry).
For terminal evaluation, participant selectors bind to the submitting actor;
canonical turn remains the observed turn, or the projected next turn for an
intended-move claim. Resignation/timeout require a configured outcome, including
any material conditions; the engine does not invent a result. An intended move
is fully prepared and authorized in isolation for claim evaluation. Its outcome
proposals participate in arbitration with the outcome hook; a decisive result
rejects the draw claim without publishing the projection. Accepting
the claim leaves the board, captures, rights, targets, canonical turn, halfmove
count, position history and quests unchanged. Terminal actions charge only the
running clock, anchor it at the trusted timestamp and award no increment.
They do not run post-move hooks or quests.

An exact retry with identical actor, action ID, expected revision and canonical
action returns the accepted event without charging clocks or appending history.
Conflicting identifiers, rejected requests and failing effects publish no state.
The in-process lock protects one manager instance; database compare-and-swap is
required across instances. Agreed draw offer/acceptance is a separate required
handshake and is not an accepted action type.

The snapshot version is `1`. Fields are `game_id`, pinned `config`,
`participants` keyed by `1` and `-1`, `started_at_ms`, `active_side`, `board`,
`captured`, `rule_state`, `special_rights`, `temporary_targets`, `clocks`,
`quest_progress`, `outcome`, `revision`, `halfmove_count`, `events` and
`position_history`, alongside `version`. Board records carry square, configured
kind, side and moved flag. Clocks store per-side `remaining_ms`, `anchor_ms`
and `increment_ms`; timestamps and elapsed time use trusted integer milliseconds.
Quest progress is keyed by stable participant identity. Snapshots are detached
JSON, bounded to 4 MiB and the immutable document limits; event histories are
bounded to 4,096 accepted actions.

Each accepted action advances one revision and appends one event containing
`revision`, `expected_revision`, `actor`, `action_id`, `at_ms`, `move`,
`captured`, emitted `effects` and `outcome` (a resolved result or null).
Move events retain this exact version-1 envelope, without an `action` field.
Terminal events additionally contain the canonical `action`, with `move: null`,
empty `captured` and `effects`, and the resolved `outcome`. Replay and retries
interpret events without `action` as moves. Private SQL validates both envelopes;
authenticated HTTP and hosted terminal acceptance gate remote exposure.
Post-move rules and quests inspect the accepted
revision, appended action, updated halfmove count and next canonical turn.
Post-move rules and quests bind `active` to the mover and `opponent` to the
other participant. Outcome evaluation binds `active` to the participant whose
turn follows the move and `opponent` to the mover. Position history records the
fully effected position before quest and outcome evaluation.
Ordered transition effects operate on isolated state. A `move_piece` effect
requires an empty destination; effects capturing an occupied square must first
use `capture_piece`, so capture records cannot be lost through overwriting.
Capture effects append the captured square to the accepted event, preserve the
captured kind/side in the session and reset the halfmove count.
Clock and quest effects accept a stable participant identity or explicit side
`1`/`-1`, resolved to that session's participant identity.
Outcome hooks only propose results, with participant-bound winner identities
and deterministic priority/conflict handling.

`get_state()` returns a detached snapshot. `from_snapshot()` creates an
independent session from the pinned configuration and initial identities,
replays accepted intents using recorded timestamps, and rejects any supplied
state that differs from deterministic replay. This proves domain reconstruction;
it does not certify Supabase persistence or remote concurrency. Snapshot version 1
preserves whether optional policy fields were explicitly declared: omitted fields
remain omitted, while explicitly declared defaults remain pinned. Frozen parser
metadata tracks presence and is never a game-authored or serialized config field.

Optional `position_identity` is null or an exact object with `moved_kinds`,
`rule_state`, `rights` and `targets`. The first three are unique lists of at most
64 declared piece kinds or initialized state/right names. Targets are at most
32 unique initialized target selections, each exactly `{name, legal_capture}`
with a boolean eligibility flag. Identity always includes board occupancy,
kinds, sides and canonical turn. It includes movement flags only for selected
kinds and only selected rule values, rights and targets. With `legal_capture`
true, a non-null target contributes only if a complete configured legal capture
ends there; otherwise it normalizes to null. The built-in action-clock deadline
does not affect this positional probe; configured authorization, capture effects
and projected safety still apply. Probes share the operation budget,
cannot recursively derive identity, and never publish moves. Missing/null policy
preserves raw identity including all movement flags, rights and targets.
The initial position and each fully effected move contribute to history;
terminal actions do not add positions. Policy selection and full shipped-game
repetition correctness still require rulebook verification.

Status-hook consumption, at-game-end quest timing and configured progress
measurements remain required extensions listed in the actionable workspace. The session does
not certify any complete FIDE or draughts rulebook.

## Aggregate evaluation ceilings

Each locked legal-move read or submission shares one trusted ceiling of
250,000 deterministic work units across candidate enumeration, capture search,
JSON/state copying, rule/query evaluation, effects, quests and outcome phases.
Every replayed action retains the same 250,000-unit child ceiling and fresh
operation-local cache. Children charge a monotonic shared parent, whose bound
is derived as `MAX_EVENTS × MAX_EVALUATION_WORK + MAX_REPLAY_INITIAL_WORK`.
The initial allowance covers twice the 65,536 snapshot value-node limit plus
4 MiB of text in 64-character blocks. Consequently every accepted history
within the supported event limit retains a sufficient aggregate replay budget;
replay cannot use that parent allowance to bypass an action's own ceiling.
Reservations check every counter before consuming any, so a failed parent or
child reservation changes neither counter. Units reserve traversed cells,
nodes, rays, candidate creation and copy work, with text cost in 64-character
blocks. These ceilings are engine security constants, not game-authored JSON
settings. Piece-owned `max_nodes` independently bounds each capture search.

Capture routes are memoized only within the locked operation, keyed by exact
board dimensions, side and every occupied square's kind, side and movement
flag. The immutable configuration is pinned to the session. Cache storage is
bounded to 256 entries and returned routes are detached copies; changing board
state cannot reuse another position's routes. Resources clear after success,
retry or failure and do not enter serialized snapshots.

Capture exploration shares its aggregate budget across pieces, ray traversal,
search nodes and position copies, with complete chains bounded to 128 hops.
Candidate capacity is checked incrementally before retaining more than 4,096
intents. Exhaustion raises `EvaluationBudgetExceeded`, a query-resolution
error; other search/result limits likewise fail closed. No search returns a
truncated route set or legal-move prefix, and preview enumeration does not
silently skip aggregate-budget failures. Rejected operations publish no state.
Snapshot recovery reports resource exhaustion as a typed transition error.

A structurally valid definition can exceed its action execution ceiling and is
rejected without accepting an unrecoverable transition. Reconstruction validates
each action under its submission ceiling, including hostile supplied histories.
Replay performance and verified checkpointing or efficient reconstruction remain
classroom-release gates before exposing arbitrary snapshot recovery through an
external API. These optimizations must preserve accepted-state recoverability,
exact retries, corruption detection and the per-action hostile-input ceiling.

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
FIDE legal move enumeration/check safety, castling, en-passant execution,
all promotions and draws, international capture edge cases, complete clock
adjudication and game outcomes must pass G2/G3 behavior and G6 independent tests before any
game's `playable` flag becomes true. No production path falls back to
geometric pseudo-moves when rules are absent.

## Supabase persistence boundary

The `bgwq` schema is private. Browser `anon` and `authenticated` roles have no
schema, table or function privileges; both game tables enable RLS. The trusted
server verifies the Supabase identity and runs the engine before invoking
`SECURITY INVOKER` functions with server-only database credentials. Foreign keys
from participant and event-actor columns reference `auth.users(id)` with
restrictive deletion. They require no service-role Auth table read grant and
never modify Auth identities or protected unrelated records.

`create_game(game_uuid, actor_uuid, action_id, config_json)` returns the game UUID.
The creator occupies side `1`; `player_two` is null, lifecycle is `pending`,
revision is `0` and state is `{}`. Configuration and creation metadata are
immutable. The creator/action key identifies one creation request across games;
an exact retry requires the same UUID and configuration. A server adapter must
recover that UUID from the creator's persisted request before assigning another
UUID on a retry.

`activate_game(game_uuid, actor_uuid, action_id, state_json)` locks the pending
game and fills side `-1` once with a distinct existing Auth identity. Its state
must be a complete canonical version-1 engine snapshot with revision `0`, empty
domain events, the pinned `starting_side` (default `1` when omitted), no result
and clocks matching the declared controls.
The database appends an activation event at revision `0`; the engine's move
history remains empty. Activation retries require the stored genesis state
and key, including its recorded timestamp. Additional joiners cannot change an
activated game's participants, configuration or lifecycle.

`commit_revision(game_uuid, actor_uuid, expected_revision, state_json,
event_json)` retains its five-argument signature and returns the committed
revision. It locks the row, requires participant membership and action-specific
authorization, and checks expected revision, immutable identity/configuration,
canonical metadata, clock timestamp and exactly one appended domain event.
Moves retain exactly nine keys: `action_id`, `actor`, `at_ms`, `captured`,
`effects`, `expected_revision`, `move`, `outcome`, `revision`. Terminal events
have exactly those keys plus `action`, with `move:null`, `captured:[]` and
`effects:[]`; snapshot version remains `1`. The closed action is `{type:resign}`,
`{type:timeout}` or `{type:claim_draw,claim:<configured outcome rule ID>,
intended_move:<closed move DTO or null>}`. No winner, clock or other assertion
is accepted in the action. Claim IDs are nonempty UTF-8 strings bounded by
262144 bytes; intended move coordinates and promotions use the move contract.

Moves require the active participant and alternate the side. Either participant
may resign. Claims require the active participant strictly before the running
clock expires. Either participant may request timeout at or after expiry.
Terminal commits preserve active side, board, captured pieces, rule state,
special rights, temporary targets, quest progress, halfmove count and position
history. Only the active clock is charged by `at_ms-anchor_ms`, clamped at zero;
the anchor becomes `at_ms`, the inactive clock and increment remain unchanged,
and no increment is credited. Timestamps are strict nonnegative safe integers
and cannot precede the authoritative anchor. The trusted server supplies time.

Terminal result and snapshot must agree exactly. Results have exactly `kind`,
`cause`, `winner`, `priority`; winner is null or a participant UUID and priority
is an integer in [-1000,1000]. Metadata must match a configured outcome proposal;
literal side winners and direct player identity references are bound to session
participants. Engine evaluation remains authoritative for dynamic expressions,
predicates, claim eligibility, projected-move legality and proposal arbitration.
Claims require a configured outcome rule and a draw with null winner. SQL never
executes the rule interpreter or persists the projected claim position. Updating the
snapshot and inserting the event occur in one transaction. A rejected call or
failed event insertion leaves both unchanged. The database does not evaluate
movement vectors, game rules or rewards; the server must supply an engine-
validated transition.

Creation, activation and domain actions have separate idempotency scopes.
`events.action_scope` is `activation` or `domain`, with unique
`(game_id, action_scope, action_id)`. The domain scope covers moves and the three closed terminal commands. Reusing a textual
creation or activation key as a move key is valid. Reusing a key for different data within its scope is rejected.
Each keyed event stores a SHA-256 fingerprint of its resulting canonical JSONB
snapshot. A low-level exact commit retry supplies the accepted event and
resulting snapshot and returns its accepted revision, including after later
revisions and a terminal result. Exact retry detection precedes stale-revision
and terminal-result rejection; conflicting key reuse is rejected. Records without a keyed genesis fail closed.

A reconstructed engine's exact retry returns its accepted event at the requested revision while
`get_state()` returns the loaded authoritative snapshot. If that validated
event's revision is at most the loaded revision, the durable adapter returns the
accepted event and authoritative state without another commit. Passing the
latest snapshot with an accepted event at the requested revision is a conflicting low-level request.
This adapter flow requires genuine authenticated HTTP/database integration;
the SQL consumer scenario alone does not certify the public adapter.

The forward lifecycle migration is
`supabase/migrations/20261015082152_private_session_lifecycle.sql`.
Terminal compatibility is defined by
`supabase/migrations/20261016091616_terminal_action_compatibility.sql` and
`tests/test_terminal_transactions.py`, which consumes actual engine outputs for
resignation, timeout and ordinary/projected claims. The terminal suite covers
both opening sides, authorization, strict clocks, immutable state, malformed
assertions, restart, exact retries after a terminal result, rollback and
concurrent terminal/move submissions.
`tests/test_private_transactions.py` executes real isolated PostgreSQL
transactions, concurrent connections and faults through the private functions.
Snapshot validation enforces the engine recovery envelope of 65,536 JSON nodes
and 32 levels. The isolated suite applies the complete migration sequence and
verifies preserved unrelated records and browser-role denial.
Docker/PostgreSQL unavailability fails the gate without a skip. Its local Auth
fixture supplies referential identities, not provider authentication evidence.
The hosted provider transaction/privilege probe is
`scripts/fixtures/provider_session_atomicity.sql`; it references three existing
Auth identities and rolls back its private test rows.
`scripts/fixtures/provider_terminal_atomicity.sql` exercises resignation,
timeout and claims against the same private boundary, including an event-insert
fault, exact retries and rollback of all fresh game rows.
Provider execution, verified JWT/gameplay HTTP access, Realtime and classroom
capacity remain distinct acceptance gates.

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

## Internal durable game store

`server.persistence.GameStore` is the internal async lifecycle adapter. Its
trusted inputs are verified canonical UUID identities, bounded action IDs,
validated definitions, expected revisions, immutable moves and server timestamps.
It uses operation-local psycopg connections, parameterized private SQL functions,
verified TLS with GSS encryption disabled, disabled prepared statements and
bounded connection and statement execution plus an active-operation deadline. It never reads Auth tables or retains authoritative state in memory.
Creation recovers its UUID before allocation; activation recovers the stored
genesis snapshot and persisted start time; accepted moves return their event
with authoritative state without recommitting. New moves reconstruct GameManager and
commit exactly one loaded revision by CAS, returning typed conflicts on races.
Exactly two pure engine worker slots bound execution without a waiting queue.
All engine construction, replay and JSON serialization are off the event loop.
The ten-second active-operation deadline includes creation canonicalization.
Cancellation drains the pinned driver cancellation bounds (five seconds to send
and five seconds for query termination), then permits three seconds for rollback
before forcing connection closure. This cleanup can extend response time.
An unknown commit acknowledgement requires authoritative refetch or the exact
same key and request; a new key or blind replay is unsafe. Cancelled or timed-out
workers cannot use SQL or publish their output; occupied slots remain reserved
until computation finishes. Active reads and activation recovery check canonical
replay against row identity, pinned configuration, revision and genesis start time.
DSNs require one explicit network host and verify-full TLS; sockets, hostaddr,
multihost and service/options overrides are rejected. Disabled TLS is confined to
explicit loopback-only test DSNs.
Participant isolation occurs before engine reconstruction or private reads are
returned. Database diagnostics and credentials never enter public exceptions.

`tests/test_persistence_adapter.py` is the genuine Docker/PostgreSQL gate with
actual service-role connections on a loopback ephemeral port. Dependency or
Docker failure blocks acceptance. The read-only `python -m server.persistence
--verify-provider` probe requires explicit credentials and an existing participant
game; missing credentials fail explicitly. Neither probe certifies playable HTTP,
Realtime or complete game rules. Catalog/gameplay readiness remains false.
