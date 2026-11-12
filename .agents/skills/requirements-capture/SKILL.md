---
name: requirements-capture
description: Keep proposed changes in GitHub issues and actual supported product behavior in the canonical PRD.
---
# Requirements Capture

1. Read actual `src/` implementation, `.agents/PRD.md` and related issues.
2. Record proposed features, acceptance cases and outstanding choices in the owning issue rather than creating parallel plans.
3. After implementation and verified behavior, update the affected portion of `.agents/PRD.md`, `.agents/AGENTS.md` progress, and `docs/architecture/` diagrams as needed.
4. Validate the source tree and diagrams, execute the relevant GUI/rule/persistence tests, and record exact evidence.
Do not derive the PRD from superseded historical request records, or recreate generated governance files.
