---
status: approved
---
# Current repository, documentation and release implementation

- `.agents/{GOAL,PLAN,TODO,SCRATCHPAD}.md` are authored outcome, execution, action and evidence records. Published notes, approved requests, accepted decisions and active rules generate `.agents/{README,PRD,ARCHITECTURE,AGENTS}.md` deterministically.
- `.github/tests/` owns all repository fixtures and application tests. GitHub Actions and DarkFactory own Python CI, Docs Pages builds, source diagrams, governance and release policy checks.
- `develop` is the protected integration branch, `main` the protected release target. `main-source` admits same-repository `develop` promotion proposals; GitHub native protection must be confirmed directly.
- `pyproject.toml` explicitly includes the shipped `games.chess` and `games.checkers` JSON resources as Python package data; executable resource acceptance is still pending.
- The `desktop-build.yml` matrix defines Windows x64, macOS ARM64/x64 and Linux x64 executable packaging. `package_desktop.py` expects the `src/` application and bundled `src/games/` assets. `release.yml` guards the exact release SHA and PrideVer metadata, requires all four artifacts/checksums, and rejects existing public/draft releases. The full packaged GUI behavior has not been verified and Python release publication remains disabled in `repo.dfconfig`.
