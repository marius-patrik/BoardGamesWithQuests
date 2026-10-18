---
name: governed-release
description: Verify branch promotion, PrideVer releases and native GitHub checks against live provider evidence.
---
# Governed Release

## When to use

When validating a release candidate or checking the repository's release and promotion configuration.

## Procedure

1. Check the current `develop` and `main` refs and the target PR's exact head SHA.
2. Read `repo.dfconfig` and `.github/workflows/release.yml` to identify the installed PrideVer version and release mechanism.
3. Inspect GitHub's native protection and required check results for `main` separately from the repository's declared policy; report unavailable provider evidence as a blocker.
4. Confirm the release PR originates from this repository's `develop` branch, passes required checks, and has independent maintainer approval of the final revision.
5. Verify that `main` contains the trusted release workflow before relying on a `push` trigger. A successful check on `develop` is not evidence of an automatic release from `main`.
6. When a release is authorized and published, verify the release tag, version, commit SHA, and any assets on the actual GitHub release.

## Evidence

GitHub PR review, branch protection, workflow run, released commit, version, tag and release asset evidence.
