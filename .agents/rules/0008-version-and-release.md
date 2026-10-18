---
status: active
---
# Verified versioning and release discipline

- The committed `repo.dfconfig` uses DarkFactory PrideVer. Do not introduce another release controller or check in a competing `VERSION` file.
- The tracked release workflow may publish only on explicitly requested workflow dispatch targeting the actual live `main` head. Pull-request validation is read-only; no push event automatically tags or releases. Explicit maintainer authorization is still required for each promotion.
- The configured integration branch remains `main` until the individually reviewed existing PR stack and the independently authorized fork-base cutover are complete under [#348](https://github.com/marius-patrik/BoardGamesWithQuests/issues/348). Do not activate a `develop`-only source gate before the branch exists.
- The declared `main` protection requires an approving review, strict checks, conversation resolution and administrator enforcement. Native GitHub settings must be verified and applied by an authorized administrator before claiming that protection is operational. Never publish tags, releases or deployments without explicit maintainer authorization, an independently reviewed SHA and actual enforced provider protections. Do not move existing tags or use CI success as a substitute for approval.
