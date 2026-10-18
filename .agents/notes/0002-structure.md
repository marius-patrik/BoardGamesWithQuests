---
status: published
---
# Tracked repository structure

Physical `.agents/` and `.github/` directories own documentation, governance and automation. The `.agents/{notes,requests,decisions,rules}/` source records generate `.agents/{README,PRD,ARCHITECTURE,AGENTS}.md`, and root `README.md` / `CONTRIBUTING.md` are symlinks. `.agents/{GOAL,PLAN,TODO,SCRATCHPAD}.md` are concise maintenance records.

`.agents/architecture/diagrams/` contains source-derived actual-code diagrams; `.agents/reference/` contains the original assignment artwork and reference diagrams, not current implementation contracts. The `.agents/agents/` and `.agents/skills/` trees are portable agent guidance; tests and fixtures are under `.github/tests/`. DarkFactory integration is configured by the existing tracked `.darkfactory/installation.json` file; this repository does not have a root Git submodule. Contribution policy lives in the [generated rules](../AGENTS.md), not this overview.
