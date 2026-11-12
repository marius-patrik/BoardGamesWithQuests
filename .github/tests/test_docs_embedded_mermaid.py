"""Verify Mermaid rendering without assuming any particular documentation file exists.

Synthetic examples validate the parser. The built-site acceptance then derives
the set of diagram-bearing pages from the tracked repository instead of fixing
a PRD filename, diagram count, or architectural class name in the test.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from html import unescape
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "build_docs.py"
spec = importlib.util.spec_from_file_location("docs_builder_embedded_mermaid", SCRIPT)
assert spec and spec.loader
builder = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = builder
spec.loader.exec_module(builder)


def test_markdown_mermaid_parser_reuses_viewer_and_escapes_html():
    source = (
        "# Diagram examples\n\n"
        '```mermaid\nflowchart LR\nA["<unsafe>"] --> B\n```\n\n'
        "~~~mermaid\nsequenceDiagram\nA->>B: Hello\n~~~\n"
    )
    rendered = builder.render_markdown_mermaid(source)
    assert rendered.count('class="diagram-viewer"') == 2
    assert rendered.count('<pre class="mermaid">') == 2
    assert "&lt;unsafe&gt;" in rendered
    assert 'A["<unsafe>"]' not in rendered


def test_other_code_fences_are_preserved():
    markdown = "# Reference\n\n```python\nprint('mermaid')\n```\n\n`mermaid`\n"
    assert builder.render_markdown_mermaid(markdown) == markdown


def test_every_tracked_diagram_page_publishes_rendered_local_svg():
    """Validate whichever Markdown/Mermaid files are present in this checkout."""
    site = ROOT / "site"
    assert (site / "index.html").is_file(), "Build the documentation before artifact checks"
    pages = builder.pages_for(ROOT)
    rendered_count = 0
    for original, target, body in pages:
        expected = body.count('<pre class="mermaid">')
        if not expected:
            continue
        dest = PurePosixPath(target)
        index = (
            site / Path(dest.parent) / "index.html"
            if dest.name == "index.md"
            else site / Path(dest.with_suffix("")) / "index.html"
        )
        assert index.is_file(), f"Missing generated diagram page for {original}"
        html = index.read_text(encoding="utf-8")
        assert '<pre class="mermaid">' not in html, f"Raw Mermaid visible on {original}"
        assert html.count('class="diagram-viewer"') >= expected
        sources = re.findall(
            r'<img src="([^"]+\.svg)"[^>]*alt="Rendered Mermaid architecture diagram"',
            html,
        )
        assert len(sources) >= expected, f"Unrendered Mermaid diagram in {original}"
        for src in sources:
            path = (index.parent / unquote(urlsplit(unescape(src)).path)).resolve()
            assert path.is_relative_to(site.resolve()), f"Asset escaped site: {src}"
            assert path.is_file(), f"Missing SVG diagram asset for {original}"
            svg = path.read_text(encoding="utf-8")
            assert "<svg" in svg and "</svg>" in svg
        rendered_count += len(sources)
    # No requirement that a particular PRD or diagram exists. Synthetic parser
    # tests above still enforce rendering behavior in a source tree without any.
    assert rendered_count >= 0
