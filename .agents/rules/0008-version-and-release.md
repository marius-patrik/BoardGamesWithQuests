---
status: active
---
# Versioning and release discipline

- The maintainer accepted **DarkFactory PrideVer** as the single versioning/release authority (#350, G2). Retain `repo.dfconfig` mode `pridever`; do not add competing tag-only/file controllers or a tracked `VERSION` file.
- Complete the current #331 → #343 → #271 stack before the separately reviewed #404 cutover. The integration branch will be `develop`, not `development`; the new release `main` begins at the verified fork base.
- Normal dependency-stacked bot-authored PR merges into `develop` must **not** publish tags, releases, GitHub Pages production or Vercel production. A separate explicit maintainer request is required to review and promote `develop → main` for release.
- GitHub Actions `release.yml` presently publishes a development prerelease upon `main` pushes and accepts dispatch. #404 must align these actual triggers and permissions with the explicit-release gate; do not mistake this policy text for live enforcement.
- Publish tags and assets only from a separately approved release commit, never move an existing tag, and verify the actual version, source SHA, artifact hashes and deployment results. Never automatically merge or release on the basis of passing CI alone.
