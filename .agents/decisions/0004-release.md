---
status: accepted
---
# Versioning and release ownership

## Decision

`repo.dfconfig` uses DarkFactory PrideVer; no separate tag-only or `VERSION`-file authority should be installed. The tracked `.github/workflows/release.yml` permits publication only through an explicit `workflow_dispatch` on the exact live `main` head, with a read-only pull-request trigger for verifying the workflow and metadata. It does not publish on branch pushes. DarkFactory remains the only authority for PrideVer resolution.

## Consequences

Production promotion still requires human authorization and provider-side settings that enforce the reviewed branch and approval policy. Declaring `enforce_admins: true` in `repo.dfconfig` alone does not update GitHub's live protection; an authorized administrator must verify and apply it. The `develop` migration is gated on the reviewed existing stack under #348.
