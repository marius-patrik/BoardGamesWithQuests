---
status: accepted
---
# Current version and release implementation

## Decision

`repo.dfconfig` uses DarkFactory PrideVer; no separate tag-only or `VERSION`-file authority should be installed. The committed release workflow currently accepts main pushes and manual dispatch, and can publish development prereleases.

## Consequences

Those current triggers are **not yet compliant** with the separately requested production-promotion policy in [issue #404](https://github.com/marius-patrik/BoardGamesWithQuests/issues/404). Their security, branch settings and external side effects must be fixed and verified before cutover. Documentation cannot enforce a policy not yet backed by GitHub/provider configuration.
