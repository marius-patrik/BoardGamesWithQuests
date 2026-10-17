---
status: accepted
---
# Issue-bound delivery and branch decision

## Decision

Use focused issue-bound bot-authored PRs, independent code/security/behavior review and explicit maintainer approval; no auto-merge or production promotion. Preserve the existing native #331 → #343 → #271 stack and protected main. Template-repo's strict `development → main` source-branch rule is an unresolved architecture/governance option to be ratified in #350, not yet installed.

## Consequences

Do not add a workflow that unconditionally rejects the existing stack. Any subsequent branch migration must update issue mapping, target refs, DarkFactory configuration and live GitHub settings together.
