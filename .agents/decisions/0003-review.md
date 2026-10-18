---
status: accepted
---
# Actual branch and review controls

## Decision

The repository presently uses `main`, with PRs #331 → #343 → #271 in a GitHub-native dependency stack. Every merge needs independent maintainer review and explicit approval on the final commit. CI is necessary but not sufficient.

## Consequences

The requested future `develop` integration and protected release-only `main` branch migration have **not occurred**. The intended cutover, exact fork-base verification, protected-branch changes and release approval policy are held as unexecuted work in [master issue #348](https://github.com/marius-patrik/BoardGamesWithQuests/issues/348). Do not represent that target topology as a current GitHub setting.
