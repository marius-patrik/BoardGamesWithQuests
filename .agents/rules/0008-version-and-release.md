---
status: active
---
# Verified versioning and release discipline

- The committed `repo.dfconfig` uses DarkFactory PrideVer. Do not introduce another release controller or check in a competing `VERSION` file.
- The tracked release workflow automatically publishes after an authorized update to protected `main` (including a reviewed `develop` → `main` merge), and supports manual re-dispatch. It verifies the exact live `main` SHA and immutable tag ownership. The merge approval is the authorization; a second release dispatch is not required.
- The `develop` branch has been created at the former main HEAD. The release-branch bootstrap is represented by `release/fork-base`, pinned to the verified fork common ancestor. GitHub still reports `main` as its default branch although the owner has directed `develop` to become the default. Native default-branch configuration must be updated by a repository administrator before claiming the change is active. This keeps default-branch-only issue, schedule and dispatch automation on the integration branch when `main` is reset to the fork base. Until the protected release `main` ref replacement and required checks are applied, **the release-only main policy must not be claimed operational**.
- The declared `main` protection requires an independent review, the `main-source` branch gate, strict checks, conversation resolution and administrator enforcement. GitHub must actually enforce these provider settings. Never move existing tags or treat CI success as approval. Never introduce a parallel release version authority.
