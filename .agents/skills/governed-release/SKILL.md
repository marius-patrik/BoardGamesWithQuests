---
name: governed-release
description: Validate current review, integration and GitHub release evidence without bypassing native protection.
---
# Governed Release

## When to use

When verifying an approved PR, reviewing the native dependency stack, proposing a release or auditing the installed DarkFactory version authority.

## Procedure

1. Confirm the candidate code, approved scope and current integration branch.
2. Read `repo.dfconfig` and the actual workflow. The installed `pridever` release controller remains authoritative; never run an independent template tag/file publisher until #350 approves a verified migration. Require generated-doc, real behavior and affected package checks.
3. Validate the PR's actual issue binding, reviewer eligibility, dependency branch and required checks. The optional `development`-only main-source policy is pending in #350 and must not be represented as live.
4. Require actual native branch protection/reviewer approval before merge; do not call workflow policy equivalent to protection.
5. After an explicitly approved main promotion, confirm the exact source commit, immutable tag and real release artifacts; reconcile any integration branch only as its verified policy requires.
6. If protection is missing, invoke the admin bootstrap procedure using an authorized account, or report that gate as blocked.

## Evidence of completion

Verified commit SHA, version, tag, release, check results, review state and any remaining administrative blocker.

Follow `.agents/AGENTS.md` and the owning role's boundaries. Adapt commands to the detected toolchain; this file is reusable guidance, not executable automation.
