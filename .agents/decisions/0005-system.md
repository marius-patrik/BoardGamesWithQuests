---
status: accepted
---
# BoardGamesWithQuests component ownership

## Decision

One deterministic generic Python engine evaluates bounded versioned JSON definitions. FastAPI owns authenticated membership, legal action verification and atomic transactions. Private Supabase PostgreSQL owns all immutable definitions, game state, events, clocks and settlement; React/Wouter and Tauri present viewer-scoped UI only. Prisma describes schema but Python owns runtime DB I/O. Chess and draughts require two seats; MoneyProperty allows 2–8 with activation only at the creator-selected target.

## Consequences

Ratify the API, relational schema, JSON/operator graph, engine and client contracts together in #350. Keep original references, target diagrams and generated actual-code diagrams as different artifacts.

## API contract authority

The **desired API shape** is recorded in GitHub issues, this project's PRD and reference API/DTO diagrams (or a reference-only OpenAPI example). These documents are design proposals, not a running contract. **The sole actual machine-readable API contract is OpenAPI 3.1 emitted by the implemented FastAPI/Pydantic application.** Generate TypeScript client types from that actual OpenAPI. **Manually define and approve the desired operations, request/response DTOs, authorization and errors first, then implement that design in FastAPI. Do not add CI comparisons or automated parity checks between the proposal and generated OpenAPI.** Do not create a parallel hand-maintained executable OpenAPI YAML, synthesize placeholder routes to satisfy a speculative design, or claim passing a structural reference checker proves live HTTP behavior. Endpoint behavior still requires real HTTP/provider tests. The operation inventory remains to be ratified separately.
