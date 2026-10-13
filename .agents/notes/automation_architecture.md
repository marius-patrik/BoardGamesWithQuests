# Development Automation Architecture

DarkFactory supplies the shared agent, review, quality, project-board and release
workflows. This repository owns one DarkFactory settings document,
`repo.dfconfig`, and thin pinned GitHub Actions callers. Python packaging and
specialized documentation tools can retain their own required configuration
inputs without becoming competing DarkFactory settings. Provider secrets stay
in GitHub secrets and are never exposed to generated documentation or browsers.

Native `mkdocs.yml` owns documentation site metadata. MkDocs, Material and
mkdocstrings generate pages and navigation from tracked Python source/docstrings.
Strict builds publish live implementation diagrams and required reference assets;
authoritative specifications are linked to their checked-out Git revision.
GitHub Pages deployment runs from reviewed `main` through Actions.

Pinned DarkFactory quality discovery must include Python 3.10–3.13 behavior
tests, Black, Rust tests/lint/formatting and web types/lint/formatting. The local
acceptance adapter validates discovery and same-run execution artifacts before
publishing protected status contexts. Missing, skipped, cancelled, failed or
unsupported mandatory checks fail the aggregate. Public bootstrap availability
is supplemental evidence and cannot certify gameplay or external integrations.

The source of truth for product behavior is [PRD](PRD.md); sequencing is
[PLAN](PLAN.md); active verification belongs to [SCRATCHPAD](../SCRATCHPAD.md).
Preserve established local and global project boards and the native review gate.
Use a single integration PR with modular source commits. Hosted delivery is
Vercel for frontend/API and Supabase for Auth/Postgres/Realtime.
