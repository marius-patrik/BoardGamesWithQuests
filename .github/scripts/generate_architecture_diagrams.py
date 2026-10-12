"""Build connected diagrams for the implemented codebase from its Python AST.

The assignment's original two-page reference is stored externally at the
linked diagrams.net document. Its exported reference SVGs are tracked as static
visual evidence; the .drawio source is intentionally not committed.
"""

from pathlib import Path

from render_implementation_uml import render_class_diagram, render_component_diagram


def generated_assets(root: Path) -> dict[str, str]:
    """Produce live, code-derived UML assets for strict documentation builds."""
    return {
        "agents/notes/diagrams/implementation.svg": render_component_diagram(root),
        "agents/notes/diagrams/implementation-classes.svg": render_class_diagram(root),
    }


if __name__ == "__main__":
    repository = Path(__file__).resolve().parents[2]
    for destination, svg in generated_assets(repository).items():
        target = repository / (
            "." + destination if destination.startswith("agents/") else destination
        )
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(svg, encoding="utf-8")
        print(destination)
