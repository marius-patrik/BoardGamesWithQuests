---
status: accepted
---
# Singular API URIs and game-ID invitations

## Decision

Accepted C1 decisions in #350:

1. **All FastAPI application resource URI path segments use singular nouns:** `/game`, `/definition`, `/asset`, `/version`, `/event`, `/me/game`, `/me/award`, `/me/rating`, and action subresources such as `/join`, `/invite`, `/available-action`, `/realtime-grant`. Collection GETs and POSTs also use singular paths. No plural aliases. OperationId verbs may remain semantically plural (e.g. `listMyGames`).
2. **Invite option B:** The cryptographically random UUIDv4 **game ID is the invite capability**. No secondary invitation token, secret hash, separate invite entity, or revocation machinery. The frontend share link is `/game/{gameId}/invite`; FastAPI `GET /game/{gameId}/invite` exposes only non-sensitive pending lobby metadata to holders of that ID, and `POST /game/{gameId}/join` requires a valid Supabase JWT and eligibility. The invite automatically ceases to allow joins when a 24-hour pending lobby expires or when the game activates. Private state/actions/history/Realtimes require actual membership, not just the game ID.

## Consequences

Maintain meaningful checks against identifier guessing, CORS, cache/referrer/analytics/log leaks, authenticated membership, game state and revision races. An invitation ID has no independent revocation switch; do not promise one. The **desired** 27-operation API paths are recorded in the canonical approved request source and API graph for manual contract ratification. **Actual** OpenAPI 3.1 comes exclusively from implemented FastAPI/Pydantic, with no automated desired-vs-implementation parity gate. Seat/role assignment and detailed request/error DTOs still await maintainer review.
