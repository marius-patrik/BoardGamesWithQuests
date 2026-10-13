# Development Automation Architecture

**Status:** Durable operational design, not the current implementation/CI result. Runtime rules live in [AGENTS.md](../AGENTS.md), the delivery plan in [PLAN.md](PLAN.md), progress in [SCRATCHPAD.md](../SCRATCHPAD.md).

## DarkFactory

DarkFactory owns the shared GitHub Actions/agent pipeline. This repository owns thin installed callers, narrowly scoped project-specific workflows and **one configuration document: `repo.dfconfig`**. There is no active `.github/darkfactory.json` configuration after migration. Upstream is pinned to a verified immutable release commit, updated through the supported installation/update mechanism. Do not vendor a second orchestration runner.

The approved workflow model includes issue/PR triage, review-gated draft PRs, CI, docs, updates and release; rejection of issues #124, #126, #167 and PR #170 means **do not remove** these services. Provider adapters and fallback behavior belong to shared DarkFactory, not the game engine. Credentials are only GitHub secrets and never exposed in client code or generated docs.

## Integration and deployment

The repository has one current implementation branch/PR; modular agent work may execute in isolated worktrees but integrates only after shared contracts are reconciled. The GitHub issue and review history remain auditable without maintaining active competing PR stacks. Public delivery uses Vercel web/API projects and Supabase; build/test/release gates require actual end-to-end evidence, not only successful documentation.

Do not duplicate the current plan, transient status, or release numbers here.
