---
status: accepted
---
# Documentation, automation and release architecture

## One source per kind of information

The independently authored `.agents/GOAL.md`, `PLAN.md`, `TODO.md` and `SCRATCHPAD.md` contain product outcomes, phase plan, current action queue and temporary investigation notes. They are not generated.

`.github/scripts/generate_documents.py` derives `.agents/README.md` from published `notes/`, `PRD.md` from approved `requests/`, `ARCHITECTURE.md` from accepted `decisions/`, and `AGENTS.md` from active `rules/`, with deterministic ordering/backlinks. GitHub CI checks generated files; root README/CONTRIBUTING are symlinks. `.agents/architecture/diagrams/` contains source-generated Mermaid diagrams; preserved original references live in `.agents/reference/`.

## Native GitHub and DarkFactory ownership

Real root `.github/workflows/`, `scripts/`, `tests/` own Actions, document generation, and all repository tests. `.agents/agents/` and `skills/` define role-specific instructions. `.darkfactory/installation.json` and `repo.dfconfig` record the DarkFactory integration, PrideVer release versioning, and stated branch/release policy.

`develop` is the integration branch, `main` the intended release branch. `main-source.yml` verifies that a PR targeting `main` originated from `develop` in the same repository; actual GitHub native protection requires provider-side enforcement, not merely source configuration.

## Guarded desktop packaging and publication

`desktop-build.yml` defines Windows x64, macOS ARM64/x64, and Linux x64 native jobs. `package_desktop.py` builds a PyInstaller distribution, verifies that a frozen executable remains running for the smoke interval, and archives it with SHA256 sidecars. `release.yml` checks the exact live `main` commit, refuses disabled Python release publication, requests an authoritative PrideVer version, depends on the native matrix and verifies all four assets/checksums before publishing a draft as public.

These are **implemented automation files**, not evidence that a complete GUI application has yet been packaged. Python publication is disabled and source on #414 lacks the Tkinter GUI that #271 must finish.
