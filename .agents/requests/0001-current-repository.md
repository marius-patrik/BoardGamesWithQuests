---
status: approved
---
# Supported repository scope

## Committed source

The repository includes the Python engine, controller, models, and piece modules under `packages/engine/`, plus chess and checkers JSON configuration assets. It includes native GitHub automation, source-derived ProperDocs publication, pinned DarkFactory integration, and this governed documentation system. Source presence is not gameplay acceptance.

The reviewed governance sources and original assignment references are part of the repository. Source-derived Mermaid architecture reflects *actual tracked code*, not a proposed implementation. The repository does **not** currently establish a working multiplayer FastAPI application, React/Tauri client, Supabase application database, or four playable game definitions.

## Governance contract

The four generated `.agents/{README,PRD,ARCHITECTURE,AGENTS}.md` documents must be produced from reviewed `notes/`, `requests/`, `decisions/`, and `rules/` respectively. Root README and CONTRIBUTING are symbolic links; source files live in real `.agents/` and `.github/` directories. All repository tests and fixtures belong to `.github/tests/`, and `.darkfactory/installation.json` remains an ordinary tracked integration configuration file.

**Desired implementation contracts belong exclusively in GitHub issues**, with [#348](https://github.com/marius-patrik/BoardGamesWithQuests/issues/348) as the program tracker and [#350](https://github.com/marius-patrik/BoardGamesWithQuests/issues/350) as the contract review. Never check in a prospective target API, DB, DSL, game configuration, future file-tree contract, mockup or executable-looking placeholder as if the repository supports it.

**Every PR must update all affected authored governance records and regenerate their derived documents alongside the actual code change.** No issue approval or passing structural check alone makes unfinished functionality an implemented capability.
