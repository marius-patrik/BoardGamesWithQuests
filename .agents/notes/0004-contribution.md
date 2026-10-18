---
status: published
---
# Contribution and verification

Every change starts from its tracked issue and is proposed through a focused pull request. Before editing, inspect the actual branch, source files, existing tests and provider status. A successful build or green structural test does not establish gameplay or deployed integration.

Canonical documents are generated from approved `.agents/notes/`, `.agents/requests/`, `.agents/decisions/` and `.agents/rules/` records. Verify these records and projections together:

```bash
python3 .github/scripts/generate_documents.py --write
python3 .github/scripts/generate_documents.py --check
python3 -m unittest discover -s .github/tests -p test_repository_structure.py
python3 -m unittest discover -s .github/tests -p test_apply_branch_protection.py
python3 -m unittest discover -s .github/tests -p test_release_gate.py
```

Behavioral Python tests run with `pytest` after installing the relevant development dependencies. The documentation preview workflow builds the rendered site, exercises `.github/tests/docs_site_acceptance.py` and `.github/tests/test_docs_browser.mjs`, then uploads a source-verified preview artifact for the separate trusted Pages publisher. A successful preview build does not establish public deployment. Claims of real provider readiness require separate live verification.

The project's review branch and release gate are the ones actually configured in GitHub and `repo.dfconfig`. PRs must not merge or release automatically without explicit maintainer authorization; the `.darkfactory/` installation metadata is repository-owned and is not a Git submodule.
