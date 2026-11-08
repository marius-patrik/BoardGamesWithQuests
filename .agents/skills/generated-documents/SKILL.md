---
name: generated-documents
description: Verify authored PRD and AGENTS plus source-generated diagrams without overwriting authored documents.
---
# Documentation and Diagrams

The authoritative documents are `.agents/PRD.md` (root `README.md`) and `.agents/AGENTS.md` (root `CONTRIBUTING.md`). They are authored, **not** generated from note, decision, rule or request records.

Reference diagrams and the original GUI mockup live under `docs/reference/`. Actual-source architecture diagrams live under `docs/architecture/diagrams/`; regenerate them with `python .github/scripts/generate_diagrams.py`.

For every documentation change: update the affected canonical document and diagrams, run `python .github/scripts/validate_repository.py --check`, then build the documentation site with `python .github/scripts/build_docs.py`. Preserve original reference assets and root symlinks. Never recreate the deleted `.agents/{notes,decisions,rules}/` directories or `.agents/{README,ARCHITECTURE,GOAL,PLAN,TODO,SCRATCHPAD}.md` files.
