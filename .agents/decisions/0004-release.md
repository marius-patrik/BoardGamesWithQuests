---
status: accepted
---
# Versioning and release ownership

## Decision

`repo.dfconfig` uses DarkFactory PrideVer; no separate tag-only or `VERSION`-file authority should be installed. The tracked `.github/workflows/release.yml` automatically publishes the DarkFactory PrideVer GitHub Release when the protected `main` branch advances, including after a reviewed merge from `development`. It also permits explicit manual dispatch on `main`. Read-only pull-request validation does not release. Publication checks the exact live main HEAD and rejects tag reuse across different commits.

## Consequences

The approved `development` → `main` merge supplies the release authorization; no second manual release command is required. Main protection must include the `main-source` status check, independent approval, strict up-to-date checking, required conversation resolution and administrator enforcement. Declaring these rules in `repo.dfconfig` alone does not change GitHub's provider state; the release topology becomes enforceable only after the pending admin cutover and protection application.
