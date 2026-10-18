---
status: active
---
# Versioning, desktop packaging and releases

- `repo.dfconfig` selects DarkFactory PrideVer as the sole release-version authority. The release workflow requests `1.0.0` for the first packaged desktop release through PrideVer; it does not author a second version source or manually create a competing `VERSION` file.
- `.github/workflows/release.yml` verifies the exact live `main` commit, checks Python publication enablement and resolves release metadata before invoking the reusable `.github/workflows/desktop-build.yml`. Its pull-request job validates release policy without publishing.
- `.github/workflows/desktop-build.yml` defines native builds for Windows x64, macOS ARM64 and x64, and Linux x64. `.github/scripts/package_desktop.py` packages desktop source, checks whether the frozen GUI remains running and writes a per-asset SHA256 file. Packaging verifies that every source game resource was copied unchanged into the frozen runtime. Completed platform execution is a separate acceptance result, not implied by the presence of these scripts.
- Publishing depends on every native packaging job. The release workflow verifies all four archives and checksums, confirms the release tag refers to the reviewed commit, and uses a draft release until all required assets have been checked; missing assets fail the workflow. Existing public releases and drafts fail closed; draft cleanup requires explicit review before a retry.
- Python release publication remains disabled in `repo.dfconfig` until the real application and the platform gates have been verified and explicitly enabled.
- `develop` is the protected integration branch and `main` is the intended protected release branch. Only a reviewed same-repository `develop → main` PR can promote a release. The trusted source-policy workflow runs from the default branch; its execution must be verified after installation there. Require the native `main-source` check, quality and issue-binding checks, independent approval and resolved discussions. A checked-in policy or green PR job is not evidence that GitHub has enforced the provider-side settings.
- `.agents/PLAN.md` records the phase-ordered v1.0.0 delivery and required provider setup; `.agents/TODO.md` tracks the active queue. These working records do not claim future features are implemented and must not be duplicated in a roadmap directory.
