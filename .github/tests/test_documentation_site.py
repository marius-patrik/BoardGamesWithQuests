"""Black-box verification of the actual generated ProperDocs deployment artifact."""

from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "site"


def test_repository_navigation_and_every_file_page():
    assert (SITE / "index.html").is_file()
    tracked = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "-z", "--cached"],
        check=True,
        capture_output=True,
    ).stdout
    names = [p.decode("utf-8", "surrogateescape") for p in tracked.split(b"\0") if p]
    assert names, "No tracked files were discovered"
    for name in names:
        path = Path(name)
        source = "/".join(part.lstrip(".") if part.startswith(".") else part for part in path.parts)
        if path.suffix.lower() == ".md":
            if path.name.lower() == "readme.md":
                target = SITE / ("/".join(source.split("/")[:-1])) / "index.html"
            else:
                target = SITE / source.removesuffix(".md") / "index.html"
        else:
            target = SITE / "repository-files" / (source + "/index.html")
        assert target.is_file(), f"Missing published navigation page for {name}: {target}"


def test_source_generated_diagrams_work_in_documentation():
    for stem in ("repository-ast", "implementation-uml"):
        raw = SITE / "agents" / "notes" / "diagrams" / (stem + ".mmd")
        page = SITE / "architecture" / "diagrams" / stem / "index.html"
        assert raw.is_file(), f"Generated source is missing: {stem}"
        source = raw.read_text(encoding="utf-8")
        assert source.startswith(("classDiagram", "flowchart")), stem
        assert page.is_file(), f"Interactive page is missing: {stem}"
        html = page.read_text(encoding="utf-8")
        assert 'class="mermaid"' in html and "mermaid.esm.min.mjs" in html
        assert ("classDiagram" if stem == "implementation-uml" else "flowchart") in html


def test_tracked_mermaid_and_svg_pages_render_graphics_instead_of_source_text():
    """A real generated source-tree entry must open a rendered graphic, not XML/flowchart code."""
    cases = (
        ("repository-ast.mmd", 'class="mermaid"'),
        ("reference-page1.svg", "<img "),
    )
    for name, marker in cases:
        page = SITE / "repository-files" / "agents" / "notes" / "diagrams" / name / "index.html"
        assert page.is_file(), f"No diagram viewer for {name}"
        html = page.read_text(encoding="utf-8")
        assert 'class="diagram-viewer"' in html
        assert marker in html, f"Diagram rendered as source text: {name}"
        assert "assets/diagrams.js" in html, f"Interactive diagram script absent: {name}"

    source_page = (
        SITE
        / "repository-files"
        / "agents"
        / "notes"
        / "diagrams"
        / "reference-page1.svg"
        / "index.html"
    )
    html = source_page.read_text(encoding="utf-8")
    import re
    from html import unescape
    from urllib.parse import urlsplit

    match = re.search(r'<img src="([^"]+)"', html)
    assert match, "Reference SVG must be embedded as a real image"
    relative = urlsplit(unescape(match.group(1))).path
    assert (
        (source_page.parent / relative).resolve().is_file()
    ), "Referenced SVG asset must actually ship"
