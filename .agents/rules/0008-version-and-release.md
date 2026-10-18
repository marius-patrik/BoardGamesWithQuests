---
status: active
---
# Verified versioning and release discipline

- The committed `repo.dfconfig` currently uses DarkFactory PrideVer. Do not introduce another release controller or check in a competing `VERSION` file.
- The actual release workflow currently runs on main pushes and manual dispatch; it is **not yet constrained** to explicitly authorized production promotions. Do not claim otherwise.
- [Issue #404](https://github.com/marius-patrik/BoardGamesWithQuests/issues/404) owns proposed `develop` / release-main migration, release-trigger hardening and GitHub-provider enforcement; this change does not perform them.
- Never publish tags, releases or deployments without explicit maintainer authorization, independently reviewed SHA and actually enforced provider protections. Do not move existing tags or use CI success as a substitute for approval.
