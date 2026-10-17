---
status: published
---
# Repository structure

Real `.agents/` and `.github/` directories own project guidance and GitHub automation. Authored `.agents/notes/`, `requests/`, `decisions/` and `rules/` respectively generate `.agents/README.md`, `PRD.md`, `ARCHITECTURE.md`, `AGENTS.md`. Root `README.md` and `CONTRIBUTING.md` are Git symlinks to the generated overview and rules. `.agents/GOAL.md`, `PLAN.md`, `TODO.md`, `SCRATCHPAD.md` are maintained at root.

Preserve reviewed product design under `.agents/requirements/`, reference data/artwork under `.agents/reference/`, and source-derived actual diagrams under `.agents/architecture/`. Portable roles/skills live in `.agents/agents/` and `.agents/skills/`. Repository tests, browser fixtures and support belong only in `.github/tests/`. The pinned DarkFactory submodule is `.darkfactory`; installed project CI remains native to `.github/workflows/`.
