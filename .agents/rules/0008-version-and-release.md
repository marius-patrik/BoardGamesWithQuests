---
status: active
---
# Versioning and releases

- `repo.dfconfig` selects DarkFactory PrideVer as the versioning authority. A release version or tag must not be authored by a competing independent source.
- `.github/workflows/release.yml` configures automatic release publishing for `push` events on `main`, and manual dispatch explicitly targeting `main`. Its pull-request job validates the release policy without publishing.
- The release job checks that the workflow revision and checkout identify the live `main` commit and rejects reuse of a tag pointing to a different commit.
- Release promotion from `develop` to `main` requires a reviewed PR and verified native protection, including the same-repository source-branch policy and required checks. Workflow contents and checked-in configuration alone do not establish that GitHub enforces a protection setting.
