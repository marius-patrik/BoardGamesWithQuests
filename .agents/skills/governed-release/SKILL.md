---
name: governed-release
description: Validate current review, integration and GitHub release evidence without bypassing native protection.
---
# Governed Release

## When to use

When verifying an approved PR, reviewing the native dependency stack, proposing a release or auditing the installed DarkFactory version authority.

## Procedure

1. Confirm the candidate code, approved scope and current integration branch.
2. Read `repo.dfconfig` and the actual release workflow to determine the single installed versioning authority. Do not install template tag/file release publishers alongside DarkFactory PrideVer, and do not claim manual release enforcement until the live trigger and provider settings have been verified. Require generated-doc, behavioral and affected-package verification.
3. Resolve PR dependencies and branch refs directly through GitHub. The `develop` branch has been created at the old main HEAD, and `release/fork-base` pins the verified fork source. The GitHub default can remain `main` but its protected release ref and native rules have not yet been changed; `main` is not yet enforceably release-only.
4. Require actual native branch protection/reviewer approval before merge; do not call workflow policy equivalent to protection.
5. Require maintainer approval of the `develop` → `main` merge. The tracked `release.yml` automatically publishes the resulting `main` push (and supports manual dispatch), verifies the live main HEAD and refuses to reuse a tag assigned to another SHA. Verify actual provider settings, commit, tag and published artifacts; merely checking the workflow source is not proof of a real release.
6. If protection is missing, invoke the admin bootstrap procedure using an authorized account, or report that gate as blocked.

## Evidence of completion

Verified commit SHA, version, tag, release, check results, review state and any remaining administrative blocker.

Follow `.agents/AGENTS.md` and the owning role's boundaries. Adapt commands to the detected toolchain; this file is reusable guidance, not executable automation.
