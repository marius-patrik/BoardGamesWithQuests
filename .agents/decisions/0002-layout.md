---
status: accepted
---
# Native directories and exclusive test ownership

## Decision

Keep real GitHub-discoverable `.github/` and independent `.agents/` directories. All repository-owned tests, fixtures, snapshots and harnesses live in `.github/tests/`. Roles and portable skills live in `.agents/agents/` and `.agents/skills/`. Preserve requirement and assignment sources separately from generated actual architecture diagrams. A pinned `.darkfactory` submodule references the reviewed upstream DarkFactory commit; local installation metadata is held outside it.

## Consequences

No duplicate test trees, speculative CI, symlinked GitHub workflows or copied DarkFactory runtimes. Confirm installer compatibility before claiming installed workflows have migrated.
