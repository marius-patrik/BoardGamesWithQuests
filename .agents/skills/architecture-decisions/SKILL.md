---
name: architecture-decisions
description: Reconcile implemented architecture with source code, GitHub issues and docs diagrams.
---
# Architecture Decisions

When changing implementation ownership or interfaces, inspect the current code and record proposed choices in the owning GitHub issue. After implementation, update the authoritative product specification in `.agents/PRD.md` when product behavior changes and the diagrams under `docs/architecture/diagrams/` when source structure changes. Run `python .github/scripts/generate_diagrams.py` and verify against actual code. Do not recreate `.agents/decisions/` or `.agents/ARCHITECTURE.md`. Review and verification are separate from merge approval.
