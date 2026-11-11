---
name: governed-release
description: Verify the current Windows build and maintainer-approved release gates from GitHub evidence.
---
# Governed Release

Check the actual `v1-cleanroom`, `develop`, and `main` refs and exact PR head. The cleanroom product is **Windows-only for required distribution**. `.github/workflows/native-windows-acceptance.yml` builds a PyInstaller executable and drives an external Windows GUI acceptance process. It uploads evidence and the executable; it does not publish a GitHub Release.

Confirm the Python version matrix, real GUI verification, Windows frozen executable evidence, and artifacts on the final commit. A successful build or artifact upload does not authorize a merge or release. Check branch protection and the existing `develop` → `main` promotion policy separately, and require maintainer approval for publication. Do not infer a release mechanism from the retired legacy multi-platform packaging workflow.
