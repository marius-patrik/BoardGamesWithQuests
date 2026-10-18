---
status: accepted
---
# Documentation, CI and desktop release architecture

`.agents/GOAL.md`, `PLAN.md`, `TODO.md` and `SCRATCHPAD.md` are authored records. `.github/scripts/generate_documents.py` derives generated README from published notes, PRD from approved requests, ARCHITECTURE from accepted decisions, and AGENTS from active rules. Root README/CONTRIBUTING are symlinks. `.agents/architecture/diagrams/` derives Mermaid syntax graphs from tracked files and the actual production Python source.

`.github/` owns source checks, central tests, docs preview/publishing, DarkFactory integration and trusted release controls. `develop` is the integration branch; `main` is the protected release branch. The current `src/` Python package is the only desktop application on this PR; `packages/server/`, `packages/client/` and `packages/native/` belong to #422.

The native `desktop-build.yml` workflow builds four platform artifacts using `package_desktop.py`, verifying copied game resources and frozen process startup. `release.yml` checks the live `main` SHA, resolves PrideVer metadata and checks required binaries/checksums before publication. Python release publication remains disabled until actual platform application acceptance is completed. No released binary is claimed by these source definitions.
