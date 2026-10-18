---
status: active
---
# No prospective implementation contracts in tracked documentation

- Describe only **implemented source, observed behavior and actually configured governance controls**. A class or configuration file does not establish a working product.
- Maintain desired API shapes, DTO proposals, schema/DSL/operator registries, target class diagrams, target file trees and game-rule drafts **exclusively in GitHub issues**. Do not copy them into `.agents/requests/`, `.agents/decisions/`, `.agents/architecture/`, generated documentation or executable-looking placeholders before implementation.
- **Every pull request updates all affected source records, generated governance documents, actual-code diagrams, docs, tests, examples and CI alongside the actual changes**, never in a promised cleanup PR. Regenerate `.agents/{README,PRD,ARCHITECTURE,AGENTS}.md` and run `.github/scripts/generate_documents.py --check`.
- When code implements a reviewed issue, describe precisely which boundary works and which remains BLOCKED. Actual FastAPI OpenAPI derives from implemented Pydantic routes, not a hand-maintained proposed contract. No desired-vs-actual spec CI comparison is required.
- Do not remove original assignment references merely because they are not current code; label them explicitly as reference inputs. Source-derived architecture is evidence of tracked declarations only, not successful external behavior.
- Never merge, tag, deploy or weaken checks without the required independent maintainer review and provider verification.
