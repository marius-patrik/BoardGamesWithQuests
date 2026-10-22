---
status: accepted
---
# Documentation, CI and desktop release architecture

`.agents/GOAL.md`, `PLAN.md`, `TODO.md` and `SCRATCHPAD.md` are authored working records. `.github/scripts/generate_documents.py` produces README, PRD, ARCHITECTURE and AGENTS from approved source directories; the root README and CONTRIBUTING are symlinks. `.agents/architecture/diagrams/` contains source-derived Mermaid diagrams.

`.github/tests/` owns all repository test resources. `desktop-gameplay.yml` verifies actual local-session gameplay on Python 3.10–3.13 and a real Tkinter user path on Xvfb. Other CI workflows enforce source quality, documentation, governance, release metadata and native package infrastructure. `develop` is the integration branch; `main` the protected release branch.

`desktop-build.yml` defines Windows x64, macOS ARM64/x64 and Linux x64 packaging. `package_desktop.py` produces artifacts and checksums. `release.yml` requires verified version/source identity and all expected platform assets. Python release publication remains disabled in `repo.dfconfig` until complete application and frozen-platform acceptance are verified.
