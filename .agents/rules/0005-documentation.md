---
status: active
---
# Documentation as part of the change

- Edit the canonical source records before regenerating projections: published `.agents/notes/*.md` own README; approved `.agents/requests/*.md` own PRD; accepted `.agents/decisions/*.md` own ARCHITECTURE; active `.agents/rules/*.md` own AGENTS.
- Never maintain root `README.md`, root `CONTRIBUTING.md`, `.agents/README.md`, `.agents/AGENTS.md`, `.agents/PRD.md` or `.agents/ARCHITECTURE.md` as competing independent copies.
- Run `python3 .github/scripts/generate_documents.py --write` after changing any source record, and `--check` before submission.
- Keep `.agents/GOAL.md` focused on the product goal; `.agents/PLAN.md` and `.agents/TODO.md` are optional empty working files, not copies of issue trackers. Proposed implementation contracts, target diagrams, future schemas and acceptance criteria live in GitHub issues only.
- Update every affected governance source record, generated projection, actual-code diagram, README/help/example and externally observable acceptance check **in the same PR** that introduces the corresponding behavior. Do not document features before implementation or defer documentation until another PR.
- Describe implemented components and observed behavior in repository documents. Use issues and PR discussions for proposed behavior, historical migrations and provider setup still pending. Keep generated documentation and release artifacts pinned to the actual source revision.
- Write code, public identifiers, comments and repository documentation in English unless approved requirements mandate another language.

### BoardGamesWithQuests: Generated Documentation and References
Documentation and navigation are generated from tracked repository source,
typed Google-style docstrings and the supported build tooling. Generated
documentation output is never edited as its own authority. Strict documentation
builds and source-derived architecture diagrams must succeed; supplied
reference diagrams are immutable input assets, not mandatory duplicate runtime
classes. Every affected link, example and diagram must remain correct.

### BoardGamesWithQuests: Language Consistency
English is canonical for all code, method names, variables, comments, docstrings, commit messages and documentation. Existing approved Czech compatibility aliases may remain additional bindings to canonical English classes; do not invent further non-English identifiers.
