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


def test_sidebar_sections_exactly_match_git_tracked_directories():
    """Reject invented navigation categories, including virtual architecture roots."""
    import re
    from html import unescape

    tracked = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "-z", "--cached"],
        check=True,
        capture_output=True,
    ).stdout
    paths = [Path(name.decode("utf-8", "surrogateescape")) for name in tracked.split(b"\0") if name]
    # Git does not track empty folders, so only file ancestors may be sections.
    expected = {
        "/" + "/".join(path.parts[:depth]) for path in paths for depth in range(1, len(path.parts))
    }
    document = (SITE / "index.html").read_text(encoding="utf-8")
    sidebar = document.split('<aside class="sidebar"', 1)[1].split("</aside>", 1)[0]
    actual = {unescape(name) for name in re.findall(r'data-nav-section="([^"]+)"', sidebar)}
    assert actual == expected, (
        "Sidebar entries must correspond exactly to Git-tracked folders: "
        f"unexpected={sorted(actual - expected)}; missing={sorted(expected - actual)}"
    )


def test_mermaid_only_diagram_sources_are_rendered_as_nonempty_images():
    """Assert the actual deployment pages contain visible graphics, not source dumps."""
    import re
    from html import unescape
    from urllib.parse import urlsplit

    tracked = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "-z", "--cached"],
        capture_output=True,
        check=True,
    ).stdout
    names = [part.decode("utf-8", "surrogateescape") for part in tracked.split(b"\0") if part]
    incompatible = [
        name
        for name in names
        if name.startswith("docs/architecture/diagrams/") and name.endswith((".svg", ".dot", ".gv"))
    ]
    assert not incompatible, f"Committed diagram sources must be Mermaid: {incompatible}"

    for category, name in (
        ("implementation", "ast"),
        ("implementation", "uml"),
        ("reference", "mvc"),
        ("reference", "uml"),
    ):
        source = (
            ROOT
            / "docs"
            / ("architecture" if category == "implementation" else "reference")
            / "diagrams"
            / (name + ".mmd")
        )
        assert source.is_file() and len(source.read_text(encoding="utf-8").splitlines()) > 12
        page = (
            SITE
            / "repository-files"
            / "docs"
            / ("architecture" if category == "implementation" else "reference")
            / "diagrams"
            / (name + ".mmd")
            / "index.html"
        )
        assert page.is_file(), f"Missing interactive diagram page: {category}/{name}"
        html = page.read_text(encoding="utf-8")
        assert 'class="diagram-viewer"' in html
        assert 'class="mermaid"' not in html
        assert "assets/diagrams.js" in html
        match = re.search(r'<img src="([^"]+\.svg)"', html)
        assert match, f"No rendered SVG image for {category}/{name}"
        path = (page.parent / urlsplit(unescape(match.group(1))).path).resolve()
        assert path.is_relative_to(SITE.resolve()) and path.is_file()
        svg = path.read_text(encoding="utf-8")
        assert "<svg " in svg and "</svg>" in svg
        opening = re.search(r"<svg[^>]*>", svg)
        assert opening and re.search(r'width="[1-9][0-9]*"', opening.group(0))
        assert re.search(r'height="[1-9][0-9]*"', opening.group(0))
        if (category, name) == ("implementation", "uml"):
            assert (
                "GameManagerController" in svg and "GameManager" in svg
            ), "Rendered UML must have real classes"


def test_original_gui_mockup_is_an_image_and_ships_unchanged():
    """The authored Excalidraw mockup must survive the docs build byte-for-byte."""
    import re
    from html import unescape
    from urllib.parse import urlsplit

    relative = Path("docs/reference/images/GUI_mockup.svg")
    source = ROOT / relative
    assert source.is_file(), "The original SVG artwork must exist under images/"
    assert b"svg-source:excalidraw" in source.read_bytes()
    original_blob = subprocess.run(
        ["git", "hash-object", str(source)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert (
        original_blob == "b693531ab78f3e07c1f6ff1452f59aa45d773a7d"
    ), "The original GUI mockup image was altered"

    page = (
        SITE
        / "repository-files"
        / "docs"
        / "reference"
        / "images"
        / "GUI_mockup.svg"
        / "index.html"
    )
    assert page.is_file(), "The original image must have a navigable documentation page"
    html = page.read_text(encoding="utf-8")
    assert 'class="diagram-viewer"' in html
    assert "assets/diagrams.js" in html
    match = re.search(r'<img src="([^"]+)"', html)
    assert match, "The image must render visually rather than as SVG source text"
    url = urlsplit(unescape(match.group(1))).path
    published = (page.parent / url).resolve()
    assert published.is_relative_to(SITE.resolve())
    assert published.is_file(), "Published original image cannot be loaded"
    assert (
        published.read_bytes() == source.read_bytes()
    ), "Published image is not the source artwork"
    assert not (
        ROOT / "docs/reference/diagrams/gui-mockup.mmd"
    ).exists(), "Do not replace the GUI image with a conceptual Mermaid diagram"


def test_embedded_markdown_mermaid_is_rendered_in_the_published_prd():
    """Mermaid fenced inside the real PRD is a visible, zoomable SVG, not code."""
    import re
    from html import unescape
    from urllib.parse import urlsplit

    page = SITE / "agents" / "PRD" / "index.html"
    assert page.is_file(), "The canonical PRD should have a published Markdown page"
    markup = page.read_text(encoding="utf-8")
    assert markup.count('class="diagram-viewer"') >= 3
    assert "assets/diagrams.js" in markup
    assert '<pre class="mermaid">' not in markup
    assert "language-mermaid" not in markup
    sources = re.findall(
        r'<img src="([^"]+\.svg)"[^>]*alt="Rendered Mermaid architecture diagram"', markup
    )
    assert len(sources) >= 3, "Every PRD Mermaid fence should compile to a real image"
    for source in sources:
        image = (page.parent / urlsplit(unescape(source)).path).resolve()
        assert image.is_relative_to(SITE.resolve()) and image.is_file()
        assert "<svg" in image.read_text(encoding="utf-8")
