---
status: accepted
---
# Implemented source boundaries

## Decision

The checked-in legacy Python source under `packages/engine/` owns its app entry point, controller and models; chess and checkers JSON assets live under their respective `packages/` directories. Documentation building and GitHub workflow automation live in `.github/`. Source-derived Mermaid diagrams represent those tracked source declarations.

## Consequences

No client app, FastAPI multiplayer lifecycle, Supabase schema, declarative engine contract, or native distribution is implemented by this governance PR. Proposed application architecture and acceptance criteria are tracked solely in [master issue #348](https://github.com/marius-patrik/BoardGamesWithQuests/issues/348), to be documented in-repo only when corresponding code lands.
