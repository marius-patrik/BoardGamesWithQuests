"""Source-level regression for rendering Mermaid diagrams embedded in Markdown."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "build_docs.py"
spec = importlib.util.spec_from_file_location("docs_builder_embedded_mermaid", SCRIPT)
assert spec and spec.loader
builder = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = builder
spec.loader.exec_module(builder)


def test_fenced_mermaid_uses_existing_diagram_viewer_and_escapes_source():
    markdown = (
        "# Document\n\nBefore\n\n"
        '```mermaid\nflowchart LR\nA["<unsafe>"] --> B\n```\n\n'
        "Between\n\n~~~mermaid\nsequenceDiagram\nA->>B: Hello\n~~~\n\nAfter\n"
    )
    result = builder.render_markdown_mermaid(markdown)
    assert result.count('class="diagram-viewer"') == 2
    assert result.count('<pre class="mermaid">') == 2
    assert "&lt;unsafe&gt;" in result
    assert 'A["<unsafe>"]' not in result
    assert "Before" in result and "Between" in result and "After" in result


def test_non_mermaid_code_and_inline_examples_remain_unchanged():
    markdown = "# Reference\n\n```python\nprint('mermaid')\n```\n\n`mermaid`\n"
    assert builder.render_markdown_mermaid(markdown) == markdown


def test_canonical_prd_contains_multiple_embedded_mermaid_diagrams():
    source = (SCRIPT.parents[2] / ".agents" / "PRD.md").read_text(encoding="utf-8")
    result = builder.render_markdown_mermaid(source)
    assert result.count('class="diagram-viewer"') >= 3
    assert result.count('<pre class="mermaid">') >= 3
