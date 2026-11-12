---
name: repository-orientation
description: Verify branch state, canonical documents, actual source and deployment workflows before changes.
---
# Repository Orientation

1. Inspect live branch refs, PRs, working tree, CI and outstanding review feedback.
2. Read `.agents/PRD.md` and `.agents/AGENTS.md`; root README and CONTRIBUTING are symlinks to them.
3. Inspect actual `src/` runtime modules and `docs/architecture/` plus `docs/reference/`. The removed `packages/` tree is not part of cleanroom runtime.
4. Inspect relevant GitHub Actions under `.github/workflows/` and avoid treating old branch artifacts as current.
5. Verify source-backed architectural diagrams by regenerating them and inspecting their diff; test real application behavior rather than file-layout assertions.
Report confirmed facts, blockers and the first actionable task. Do not recreate removed governance documents.
