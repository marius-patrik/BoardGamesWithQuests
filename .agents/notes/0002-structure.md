---
status: published
---
# Tracked repository structure

Physical `.agents/` and `.github/` directories own documentation, governance and automation. The `.agents/{notes,requests,decisions,rules}/` source records generate `.agents/{README,PRD,ARCHITECTURE,AGENTS}.md`, and root `README.md` / `CONTRIBUTING.md` are symlinks. `.agents/{GOAL,PLAN,TODO,SCRATCHPAD}.md` are concise maintenance records.

Documentation builds create virtual Mermaid AST/UML viewers at `.agents/architecture/diagrams/` from the exact tracked source; no stale generated diagram snapshots are committed; `.agents/reference/` contains the original assignment artwork and reference diagrams, not current implementation contracts. The `.agents/agents/` and `.agents/skills/` trees are portable agent guidance; tests and fixtures are under `.github/tests/`. DarkFactory is pinned as the `.darkfactory` submodule. Contribution policy lives in the [generated rules](../AGENTS.md), not this overview.
