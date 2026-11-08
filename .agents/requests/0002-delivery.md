---
status: approved
---
# Current repository and delivery requirements

- `.agents/{GOAL,PLAN,TODO,SCRATCHPAD}.md` are independent authored files for goals, execution, action queue and temporary findings; no duplicate roadmap directory.
- Published notes, approved requests, accepted decisions and active rules are the canonical inputs to generated `.agents/{README,PRD,ARCHITECTURE,AGENTS}.md`. Generated files are checked deterministically in CI. Root README/CONTRIBUTING are symlinks.
- `.github/tests/` is the central test/fixture tree. `.agents/architecture/diagrams/` contains source-generated Mermaid AST/UML, distinct from preserved reference diagrams.
- `develop` is the integration branch; `main` is the release branch. `.github/workflows/main-source.yml` checks same-repository `develop → main` PR sources, but native GitHub branch protection must be verified separately.
- DarkFactory PrideVer in `repo.dfconfig` resolves release versions. The release workflow is gated by its exact `main` revision and Python enablement flag; its reusable packaging matrix describes Windows x64, macOS ARM64/x64 and Linux x64 builds and checksum/asset validation.
- Python publication is currently disabled; successful policy tests do not prove complete GUI packages have been built or published.
