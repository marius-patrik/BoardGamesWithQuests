---
status: active
---
# Repository hygiene

- Prefer one durable record per fact; periodically reconcile branches, issues, pull requests and plans against reality.
- Do not delete a branch containing unique commits without explicit approval and a verified recovery path.
- Keep commits, generated files, links and imports free of stale paths or obsolete aliases. Do not commit proposed API DTOs, DSL/SQL target schemas, future game rulebooks or speculative target diagrams; record those designs solely in issues.
- Only create CI workflows or dependencies when they verify real behavior or support required delivery; avoid speculative scaffolding.
- Treat failures, blockers and decisions as durable project records rather than ephemeral chat history.

### BoardGamesWithQuests: Atomic Artifact Alignment
Each pull request updates **every affected artifact and its governance records** together: behavior, public
interfaces, schemas, migrations, game JSON, tests and fixtures, contracts,
decisions, diagrams, generated documentation, examples, CI, deployments,
release metadata and issue/PR acceptance criteria. Delete contradictory
references and unused duplicate implementations; never defer required
synchronization to an unspecified cleanup.

GitHub issues own proposed requirements; the PRD and accepted architecture records describe committed implementation and its real responsibility boundaries;
actual source and independently observed behavior determine implementation
status. No plan, diagram, mock, passing build or hosted placeholder establishes
operational functionality.

### BoardGamesWithQuests: Timeless Repository Artifacts
Tracked files contain only enduring, actually implemented requirements, design decisions,
working implementation descriptions, reproducible source inputs and
actionable unfinished work. Do not keep implementation histories, dated
progress narratives, superseded instructions, transitional comparisons,
obsolete files or phase-relative labels that do not express a stable
functional contract. Describe what components do, without negative inventories of capabilities not implemented. Do not incorporate historical branch renames, PR numbers, incident narratives, migration commentary or repeated "legacy" disclaimers into architecture, requirements or README. Put operational restrictions in rules, and keep pending operations in issues/PRs. Replace material at its source instead
of appending chronicles. Git and issue history retain provenance; source
citations and ordered SQL migrations may carry required date identifiers.
