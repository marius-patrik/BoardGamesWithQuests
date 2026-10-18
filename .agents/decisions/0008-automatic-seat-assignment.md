---
status: accepted
---
# Automatic game seats and definition-ordered role assignment

## Decision

Accepted C1 option A in #350: **the server assigns every seat and role; the client never chooses either**. On `POST /game`, atomically insert the game and its creator as the **first participant**, with the first canonical seat and an eligible role. The new game remains pending with exactly one member; no game-state seeds, optional-player objects or clocks are initialized until the full creator-selected target count is occupied.

For each valid `POST /game/{gameId}/join`, lock the pending game and assign the **lowest available seat** in canonical seat order. Assign the **first eligible role in the immutable published definition's role-array order** that still permits all remaining unoccupied seats to satisfy every role's minimum and maximum count at the immutable target. This uses a deterministic feasibility check, not a random or game-specific assignment. Infeasible role capacities/target combinations are invalid at validation/publication/creation, not deferred until an impossible final join.

## Consequences

Join requests contain **no** `seat` or `role` selection; an idempotent retry cannot take a second seat. Enforce uniqueness of game/seat and game/user, immutable game/version role scope, serialized concurrent joins, expiry/active rejection and rollback of all partial failures. On the last join, activate/seed the game exactly once within the accepted transaction. The precise seat-index numerical convention, global retry/header/revision syntax and response/status DTOs are still separate #350 design questions. The actual API contract will be emitted by implemented FastAPI/OpenAPI; there is no CI comparison to this design record.
