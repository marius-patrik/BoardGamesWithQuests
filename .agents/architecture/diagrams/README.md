# Generated source architecture

The repository documentation builder generates the Mermaid AST and Python implementation UML from the **actual Git-tracked source** at build time. This tracked directory is the real navigation owner; `ast.mmd` and `uml.mmd` are generated website artifacts rather than separately maintained design contracts.

The generator is [`.github/scripts/generate_diagrams.py`](../../../.github/scripts/generate_diagrams.py), integrated by [`.github/scripts/build_docs.py`](../../../.github/scripts/build_docs.py). The views describe code declarations present in the inspected commit, not service health, runtime correctness, or any proposed API/database/game architecture. Proposed implementation designs and acceptance criteria stay in GitHub issues.

The published documentation exposes the generated Mermaid source and interactive diagrams. They are validated through the documentation site's real build and browser tests.
