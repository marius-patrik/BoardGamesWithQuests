---
name: generated-documents
description: Maintain README, PRD, ARCHITECTURE and AGENTS as deterministic projections of canonical Markdown sources.
---
# Generated Documents

## When to use

After editing published notes, approved requests, accepted decisions or active rules.

## Procedure

1. Edit `.agents/notes/*.md` (front matter `status: published`) for the README overview. Maintain the phase-level execution plan in `.agents/PLAN.md`, the current action queue in `.agents/TODO.md`, and temporary observations in `.agents/SCRATCHPAD.md`. Keep prospective implementation contracts in the owning issues; do not create another roadmap.
2. Edit `.agents/requests/*.md` (approved) for PRD, `.agents/decisions/*.md` (accepted) for ARCHITECTURE, and `.agents/rules/*.md` (active) for AGENTS.
3. Verify `.agents/` and `.github/` are real directories, and verify the tracked `.darkfactory/installation.json` integration metadata.
4. Run `python3 .github/scripts/generate_documents.py --write`.
5. Run `python3 .github/scripts/generate_documents.py --check` and inspect the generated diff.
6. Verify root symlinks: README -> `.agents/README.md`, CONTRIBUTING -> `.agents/AGENTS.md`.
7. Run tests from `.github/tests/`; verify native CI checks in GitHub Actions.
8. Never manually modify projections to silence failing checks.

## Evidence of completion

Deterministically regenerated documents with passing local validation, no stale references and no tests outside `.github/tests/`.

Follow `.agents/AGENTS.md` and the owning role's boundaries. This file is reusable guidance, not executable automation.
