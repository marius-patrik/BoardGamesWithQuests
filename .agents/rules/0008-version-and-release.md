---
status: active
---
# Verified versioning and release discipline

- The committed `repo.dfconfig` uses DarkFactory PrideVer. Do not introduce another release controller or check in a competing `VERSION` file.
- The tracked release workflow runs on main pushes and manual dispatch. Authorization of a specific production promotion requires separate verification, not an assertion in documentation.
- A GitHub issue owns each proposed branch-topology or release-policy change until the associated reviewed implementation and actual provider configuration are verified.
- Never publish tags, releases or deployments without explicit maintainer authorization, independently reviewed SHA and actually enforced provider protections. Do not move existing tags or use CI success as a substitute for approval.
