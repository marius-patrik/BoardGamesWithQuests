---
status: accepted
---
# Actual branch and review controls

## Decision

The repository's integration and release controls are the ones actually enforced by GitHub. Implementation PRs remain issue-bound and require independent maintainer review and explicit approval of their final revisions. Passing CI is necessary but not sufficient.

## Consequences

Any alternative branch topology or release policy remains issue-only until its implementation and native GitHub enforcement are verified. Do not describe an unconfigured branch policy as active.
