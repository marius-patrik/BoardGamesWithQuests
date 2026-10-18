---
status: accepted
---
# Issue-bound delivery and branch decision

## Decision

Finish the existing GitHub-native #331 → #343 → #271 stack first with independent maintainer review and explicit approval for every merge to the existing `main`.

After that stack is merged, carry out separately tracked issue #404: rename the accumulated existing `main` to `develop`, and create a new `main` at the verified repository fork-base commit. The exact fork-base ref and SHA must be confirmed before the cutover. Do not call this branch `development`.

Remaining implementation uses dependency-ordered, bot-authored stacked PRs whose accepted changes merge into `develop` with the maintainer's review. Promotion from `develop` to `main` happens only on a separate explicit maintainer request. Never auto-merge or automatically publish the application from a routine integration merge.

## Consequences

Recording G1 in #350 does not perform or authorize the disruptive cutover before its prerequisites are complete. Issue #404 owns verification of SHAs, recovery references, GitHub protection and default-branch changes, DarkFactory and workflow configurations, docs and deployment behavior. Versioning/release-controller choice G2 remains open.
