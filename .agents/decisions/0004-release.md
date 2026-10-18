---
status: accepted
---
# Versioning and release ownership

## Decision

`repo.dfconfig` uses DarkFactory PrideVer; no separate tag-only or `VERSION`-file authority should be installed. The tracked `.github/workflows/release.yml` accepts main pushes and manual dispatch, and can publish development prereleases.

## Consequences

Any change to release authorization, branch topology or provider enforcement must be captured in its owning issue and implemented together with tested GitHub settings. Source policy by itself does not prove provider enforcement.
