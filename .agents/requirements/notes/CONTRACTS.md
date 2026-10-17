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

## Complete HTTP operation ownership (33 operations)

Every `operationId` in [API.md](API.md) has exactly one service transaction or query owner. Paths and verb definitions come only from the embedded OpenAPI contract; the table describes the intended persistence and failure boundary. The slash-separated Python files denote a call relationship, **not** duplicate service authorities.

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
| `createGame` | api/services.py + repository.py | games(creator_id,creation_key) pinned versions | 201 pending game; exact retry stable |
| `getGame` | api/services.py + engine projection | games participants and viewer-redacted state | 401/404 unauthorized; latest revision |
| `getInvitation` | api/services.py + security.py | pending games and opaque invitation token | bounded pending eligibility; no private leak |
| `joinGame` | api/services.py + repository.py | locked game participant seat and role | join once, 409 occupied/stale; activation once |
| `availableActions` | api/services.py + engine/runtime.py | pinned state plus authorized candidate enumeration | 200 legal viewer-scoped actions only |
| `submitAction` | api/services.py + engine/runtime.py | locked games state events mutations outcomes awards | atomic revision, idempotency, rollback |
| `getEvents` | api/services.py + repository.py | append-only events plus authorized redacted values | cursor/revision stable replay-safe history |
| `realtimeGrant` | api/realtime.py + security.py | membership gate and private Broadcast topic | short-lived participant-only grant |

## Global invariants

- `Version.minimumParticipants` and `maximumParticipants` are definition constraints, **not** a fixed two-seat engine. `Participant.seat` is unique by game, and no unoccupied seat receives entities, wallets, active-turn rights or settlements.
- Runtime identifiers are always scoped by game; definition identifiers by immutable version. SQL composite foreign keys must reject cross-game and cross-version references.
- Client action arguments are untrusted. Evaluated conditions do no I/O; typed effects update a proposed state only. A committed event records server time and randomness, ensuring replay does not re-roll or recompute clocks.
- Read operations must never use a service role to bypass participant filtering without an explicit membership gate. Schema-only checks cannot certify these security obligations.
- Failure at any point before COMMIT leaves revision, game state, events, outcomes and awards unchanged; concurrently submitted actions cannot both accept an identical expected revision.

## Acceptance before implementation approval

Static validation must parse the canonical OpenAPI document, follow all schema references, validate all portable game JSON against the canonical JSON Schema, enforce a one-owner API operation map and check Prisma/SQL target relationships. The database baseline must additionally be applied from empty PostgreSQL/Supabase and tested with real Auth principals, RLS checks, conflicting actions, idempotent retries, disconnect/reconnect, and restart/replay. A blocked provider acceptance is **BLOCKED**, never reported as green.
