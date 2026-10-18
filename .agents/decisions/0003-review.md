---
status: accepted
---
# Actual branch and review controls

## Decision

A `development` branch now exists at the previous `main` commit, preserving the complete working tree and PR ancestry. GitHub still advertises the protected `main` branch as its default until the administrator completes the rename/reset and release-branch protection. The intended model is `development` for integration and `main` for reviewed release promotion. Implementation PRs remain issue-bound and require independent maintainer review and explicit approval of their final revisions. Passing CI is necessary but not sufficient.

## Consequences

The fork-source common ancestor has been verified as `a98e36d098a1ee9aa3e793cfc39040ad6e6d2e4e` and preserved by the `release/fork-base` branch. This repository commit includes a native `main-source` gate that rejects release PRs not originating from the same repository's `development`; native branch protection must **require** its `main-source` check and enforce approvals to make this effective. The administrator must still change the default and replace the protected `main` ref before describing the release-only main policy as live. Approval of each `development` → `main` PR is the authorization to trigger the normal main-push release.
