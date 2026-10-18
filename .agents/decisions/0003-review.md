---
status: accepted
---
# Actual branch and review controls

## Decision

A `develop` branch now exists at the previous `main` commit, preserving the complete working tree and PR ancestry. GitHub still advertises the protected `main` branch as its default; the owner has now directed that `develop` become the default and integration branch, with `main` reserved for reviewed release promotion. This PR records that requested target but does not claim the GitHub setting has already changed. Implementation PRs remain issue-bound and require independent maintainer review and explicit approval of their final revisions. Passing CI is necessary but not sufficient.

## Consequences

The fork-source common ancestor has been verified as `a98e36d098a1ee9aa3e793cfc39040ad6e6d2e4e` and preserved by the `release/fork-base` branch. This repository commit includes a native `main-source` gate that rejects release PRs not originating from the same repository's `develop`; native branch protection must **require** its `main-source` check and enforce approvals to make this effective. An administrator must set GitHub's actual default branch to `develop` as requested. This also keeps default-branch-only issue, schedule, and manually dispatched workflows on the integration branch when the fork-base release `main` is introduced. The release-only policy separately depends on live branch protection and the required `main-source` workflow. Approval of each `develop` → `main` PR is the authorization to trigger the normal main-push release.
