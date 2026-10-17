# Implementation evidence

The repository source AST and implementation UML in [diagrams](../diagrams/) are generated from Git-tracked source by `.github/scripts/generate_diagrams.py` and consumed by the single documentation publisher. They show real files, parsed declarations and explicit Python type/inheritance relationships, not inferred runtime behavior. Never edit generated diagrams manually or treat an annotated target architecture as implemented code. API behavior, persistence and authorization are proven only through real actor/provider-facing acceptance.
