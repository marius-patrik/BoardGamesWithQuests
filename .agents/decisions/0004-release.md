---
status: accepted
---
# One compatible release authority

## Decision

**G2 accepted (#350): Retain the installed DarkFactory PrideVer versioning/release authority** in `repo.dfconfig` (`repo.versioning.mode = pridever`). Do not migrate to template-repo's tags-only or optional `VERSION`-file controllers, do not run a second publisher, and do not silently bump versions for feature PRs.

**G1 remains binding:** Complete the existing #331 → #343 → #271 stack, then perform the separately reviewed #404 cutover to `develop` integration and a fresh fork-base `main`. Ordinary integration PRs and merges into `develop` do not authorize tagging, GitHub Releases, production deployment or promoting `develop` to `main`. The maintainer must separately and explicitly request a reviewed promotion and its release.

## Consequences

The current `.github/workflows/release.yml` has a push-to-`main` publisher that labels releases as development prereleases and also allows manual dispatch. Retaining PrideVer **does not ratify these triggers as safe**: #404 must verify/harden release triggers, permissions, branch ancestry, tags and deployment conditions so the post-cutover release is produced only by a separately authorized promotion, with genuine provider evidence. Before #404, preserve existing functioning workflow configuration rather than changing live release behavior during design-only review. No tracked `VERSION` file or duplicate tag-authoring workflow.
