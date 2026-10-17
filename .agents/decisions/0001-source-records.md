---
status: accepted
---
# Canonical generated governance documents

## Decision

Use the template's statuses and source-record tree. Published `.agents/notes/*.md` generate `.agents/README.md`; approved `.agents/requests/*.md` generate `.agents/PRD.md`; accepted `.agents/decisions/*.md` generate `.agents/ARCHITECTURE.md`; active `.agents/rules/*.md` generate `.agents/AGENTS.md`. Keep the complete existing product contract as **one source record**, retaining its content for subsequent ratification rather than silently changing it.

## Consequences

The generated Markdown is committed and regenerated deterministically. Never edit generated outputs as competing sources. Root README and CONTRIBUTING are Git symlinks to overview and rules.
