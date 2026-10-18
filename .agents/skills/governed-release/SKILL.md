---
name: governed-release
description: Validate current review, integration and GitHub release evidence without bypassing native protection.
---
# Governed Release

## When to use

When verifying an approved PR, reviewing the native dependency stack, proposing a release or auditing the installed DarkFactory version authority.

## Procedure

1. Confirm the candidate code, approved scope and current integration branch.
2. Read `repo.dfconfig` and the actual workflow. G2 in #350 explicitly ratifies DarkFactory `pridever` as the **single** version/release authority; do not introduce a template tag/file publisher or `VERSION` file. Review actual release workflow triggering as part of #404 before asserting manual-release enforcement. Require generated-doc, real behavior and affected package checks.
3. Resolve the actual PR dependencies and branch refs through GitHub. Only validate work against branches that exist and are configured; [#404](https://github.com/marius-patrik/BoardGamesWithQuests/issues/404) tracks the proposed integration/release migration, which must not be assumed deployed.
4. Require actual native branch protection/reviewer approval before merge; do not call workflow policy equivalent to protection.
5. The maintainer must separately and explicitly request any release-branch promotion. The existing `release.yml` has an automatic `main`-push development-prerelease trigger; resolving its permissions/triggers is tracked in #404. Ordinary integration merges, passing checks or closing an issue do not authorize a production release. After promotion, confirm the exact commit, tag and actual deployed release artifacts.
6. If protection is missing, invoke the admin bootstrap procedure using an authorized account, or report that gate as blocked.

## Evidence of completion

Verified commit SHA, version, tag, release, check results, review state and any remaining administrative blocker.

Follow `.agents/AGENTS.md` and the owning role's boundaries. Adapt commands to the detected toolchain; this file is reusable guidance, not executable automation.
