---
status: accepted
---
# One compatible release authority

## Decision

Preserve the installed DarkFactory release workflow and `repo.dfconfig` `pridever` mode until a #350 decision validates migration to template-repo's default `tags` or opt-in `file` mode. Do not maintain two tag/version controllers or introduce a VERSION file during this governance-only change.

## Consequences

Existing CI, release metadata and provider gates remain authoritative until verified replacement; never assume config declarations enforce live branch protection.
