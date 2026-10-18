---
status: accepted
---
# Actual branch and review controls

## Decision

GitHub's existing default and integration branch is `main` (as configured in `repo.dfconfig`); no `develop` branch has been established. Implementation PRs remain issue-bound and require independent maintainer review and explicit approval of their final revisions. Passing CI is necessary but not sufficient.

## Consequences

The separate `develop` integration / `main` release-branch migration is owned by the accepted sequencing in [#348](https://github.com/marius-patrik/BoardGamesWithQuests/issues/348): finish and review the existing implementation stack first, verify the fork base and provider protections, and cut over only upon separately authorized maintainer instruction. Do not advertise a non-existent branch or unconfigured source-branch restriction as active.
