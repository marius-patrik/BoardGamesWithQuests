# API, engine and persistence authority

This document fixes ownership and response behavior where a type schema alone cannot specify a transaction. The OpenAPI [single source](API.md), [Prisma schema](../../../packages/server/supabase/schema.prisma), [PostgreSQL constraints](../../../packages/server/supabase/integrity.sql), [engine UML](../diagrams/engine_uml.mmd) and [client UML](../diagrams/client_uml.mmd) must be reviewed together. No game-specific code paths are allowed in the interpreter.

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

## Global invariants

- `Version.minimumParticipants` and `maximumParticipants` are definition constraints, **not** a fixed two-seat engine. `Participant.seat` is unique by game, and no unoccupied seat receives entities, wallets, active-turn rights or settlements.
- Runtime identifiers are always scoped by game; definition identifiers by immutable version. SQL composite foreign keys must reject cross-game and cross-version references.
- Client action arguments are untrusted. Evaluated conditions do no I/O; typed effects update a proposed state only. A committed event records server time and randomness, ensuring replay does not re-roll or recompute clocks.
- Read operations must never use a service role to bypass participant filtering without an explicit membership gate. Schema-only checks cannot certify these security obligations.
- Failure at any point before COMMIT leaves revision, game state, events, outcomes and awards unchanged; concurrently submitted actions cannot both accept an identical expected revision.

## Acceptance before implementation approval

Static validation must parse the canonical OpenAPI document, follow all schema references, validate all portable game JSON against the canonical JSON Schema, enforce a one-owner API operation map and check Prisma/SQL target relationships. The database baseline must additionally be applied from empty PostgreSQL/Supabase and tested with real Auth principals, RLS checks, conflicting actions, idempotent retries, disconnect/reconnect, and restart/replay. A blocked provider acceptance is **BLOCKED**, never reported as green.
