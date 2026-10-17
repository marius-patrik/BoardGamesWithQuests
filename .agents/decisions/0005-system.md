---
status: accepted
---
# BoardGamesWithQuests component ownership

## Decision

One deterministic generic Python engine evaluates bounded versioned JSON definitions. FastAPI owns authenticated membership, legal action verification and atomic transactions. Private Supabase PostgreSQL owns all immutable definitions, game state, events, clocks and settlement; React/Wouter and Tauri present viewer-scoped UI only. Prisma describes schema but Python owns runtime DB I/O. Chess and draughts require two seats; MoneyProperty allows 2–8 with activation only at the creator-selected target.

## Consequences

Ratify the API, relational schema, JSON/operator graph, engine and client contracts together in #350. Keep original references, target diagrams and generated actual-code diagrams as different artifacts.
