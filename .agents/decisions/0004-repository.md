---
status: accepted
---
# Documentation, CI and desktop release architecture

`.agents/GOAL.md`, `PLAN.md`, `TODO.md` and `SCRATCHPAD.md` are authored records. `.github/scripts/generate_documents.py` builds README, PRD, ARCHITECTURE and AGENTS from the source-owned notes, approved requests, accepted decisions and active rules; the root README and CONTRIBUTING are symlinks. `.agents/architecture/diagrams/` contains source-derived Mermaid diagrams.

`.github/tests/` owns all repository tests and fixtures. `desktop-gameplay.yml` runs the production local-session contract on Python 3.10–3.13 and runs real Tkinter tests under Xvfb. The GUI acceptance module is explicitly selected in that workflow because the default Python matrix is headless. `desktop-native-acceptance.yml` builds frozen Windows x64, macOS ARM64/x64 and Linux x64 archives on PRs without publishing.

`desktop-build.yml` delegates packaging to `package_desktop.py`, which verifies copied game assets, a frozen `--check` real action/idempotency/replay diagnostic, GUI process startup and SHA256 sidecars. `release.yml` checks PrideVer, exact main source and complete platform assets before publication. Python publication remains disabled until reviewed end-to-end gameplay and platform acceptance.
