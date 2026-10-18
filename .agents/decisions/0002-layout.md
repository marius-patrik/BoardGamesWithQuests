---
status: accepted
---
# Native directories and repository-owned tests

## Decision

Keep independent physical `.github/` and `.agents/` directories, the repository's entire test suite under `.github/tests/`, roles and skills in `.agents/agents/` and `.agents/skills/`, and a pinned upstream `.darkfactory` submodule. Distinguish historical assignment references from diagrams generated from actual source. Proposed implementation diagrams live in issues, not in `.agents/requirements/`.

## Consequences

GitHub Actions remains natively discoverable; there is no mirrored test, workflow, DarkFactory source or speculative API/SQL/JSON authority.
