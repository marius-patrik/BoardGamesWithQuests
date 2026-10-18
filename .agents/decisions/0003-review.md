---
status: accepted
---
# Actual branch and review controls

## Decision

The repository's integration and release controls are the ones actually enforced by GitHub. Implementation PRs remain issue-bound and require independent maintainer review and explicit approval of their final revisions. Passing CI is necessary but not sufficient.

## Consequences

The requested future `develop` integration and protected release-only `main` branch migration have **not occurred**. The intended cutover, exact fork-base verification, protected-branch changes and release approval policy are tracked in [issue #404](https://github.com/marius-patrik/BoardGamesWithQuests/issues/404). Do not represent that target topology as a current GitHub setting.
