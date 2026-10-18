---
status: published
---
# Source and documentation layout

- `packages/engine/` contains the Python application entry point, controller and model packages.
- `packages/chess/` and `packages/checkers/` contain JSON configuration assets.
- `.agents/notes/`, `.agents/requests/`, `.agents/decisions/` and `.agents/rules/` generate the README, PRD, architecture and contributor-rules documents.
- `.agents/architecture/diagrams/` contains source-derived Mermaid diagrams; `.agents/reference/` contains reference drawings and artwork.
- `.agents/agents/` and `.agents/skills/` contain reusable guidance for development tasks.
- `.github/scripts/`, `.github/workflows/` and `.github/tests/` contain documentation tooling, automation and tests.
- Root `README.md` and `CONTRIBUTING.md` link to the generated documentation. `.darkfactory/installation.json` records the DarkFactory integration.
