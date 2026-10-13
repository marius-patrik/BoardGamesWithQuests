# Development Automation Architecture

DarkFactory supplies the shared agent, review, quality, project-board and release
workflows. This repository owns one DarkFactory settings document,
`repo.dfconfig`, and thin pinned GitHub Actions callers. Python packaging and
specialized documentation tools can retain their own required configuration
inputs without becoming competing DarkFactory settings. Provider secrets stay
in GitHub secrets and are never exposed to generated documentation or browsers.

The source of truth for product behavior is [PRD](PRD.md); sequencing is
[PLAN](PLAN.md); active verification belongs to [SCRATCHPAD](../SCRATCHPAD.md).
Preserve established local and global project boards and the native review gate.
Use a single integration PR with modular source commits. Hosted delivery is
Vercel for frontend/API and Supabase for Auth/Postgres/Realtime.
