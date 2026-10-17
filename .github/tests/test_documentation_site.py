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


def test_source_generated_diagrams_work_in_documentation():
    """Generated implementation diagrams must open from their actual repository paths."""
    import re
    from html import unescape
    from urllib.parse import urlsplit

    for category, stem in (("architecture", "ast"), ("architecture", "uml")):
        raw = SITE / "agents" / "architecture" / "diagrams" / (stem + ".mmd")
        page = SITE / "repository-files" / "agents" / "architecture" / "diagrams" / (stem + ".mmd") / "index.html"
        assert raw.is_file(), f"Generated diagram source is missing: {category}/{stem}"
        assert raw.read_text(encoding="utf-8").startswith(("classDiagram", "flowchart"))
        assert page.is_file(), f"Rendered diagram page is missing: {category}/{stem}"
        html = page.read_text(encoding="utf-8")
        assert 'class="diagram-viewer"' in html and "assets/diagrams.js" in html
        rendered = re.search(r'<img src="([^"]+\.svg)"', html)
        assert rendered, f"Mermaid was not rendered: {category}/{stem}"
        relative = urlsplit(unescape(rendered.group(1))).path
        image = (page.parent / relative).resolve()
        assert image.is_relative_to(SITE.resolve()) and image.is_file()
        assert "<svg" in image.read_text(encoding="utf-8")
        assert 'class="mermaid"' not in html


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
        if name.startswith(".agents/") and "/diagrams/" in name and name.endswith((".svg", ".dot", ".gv"))
    ]
    assert not incompatible, f"Committed diagram sources must be Mermaid: {incompatible}"

    for category, name in (
        ("architecture", "ast"),
        ("architecture", "uml"),
        ("reference", "mvc"),
        ("reference", "uml"),
        ("requirements", "engine_uml"),
        ("requirements", "client_uml"),
    ):
        source = ROOT / ".agents" / category / "diagrams" / (name + ".mmd")
        assert source.is_file() and len(source.read_text(encoding="utf-8").splitlines()) > 12
        page = SITE / "repository-files" / "agents" / category / "diagrams" / (name + ".mmd") / "index.html"
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
        if (category, name) == ("architecture", "uml"):
            assert (
                "GameController" in svg and "GameManager" in svg
            ), "Rendered UML must have real classes"


def test_diagrams_are_owned_by_reference_requirements_and_implementation():
    """Diagrams must be in exactly the three requested source-owner areas."""
    from html import unescape
    import re

    expected = {
        ".agents/architecture/diagrams/ast.mmd",
        ".agents/architecture/diagrams/uml.mmd",
        ".agents/reference/diagrams/mvc.mmd",
        ".agents/reference/diagrams/uml.mmd",
        ".agents/requirements/diagrams/engine_uml.mmd",
        ".agents/requirements/diagrams/client_uml.mmd",
    }
    actual = {p.relative_to(ROOT).as_posix() for p in (ROOT / ".agents").rglob("*.mmd")}
    assert actual == expected, f"Mermaid owner drift: {actual ^ expected}"
    document = (SITE / "index.html").read_text(encoding="utf-8")
    sidebar = document.split('<aside class="sidebar"', 1)[1].split("</aside>", 1)[0]
    sections = {unescape(x) for x in re.findall(r'data-nav-section="([^"]+)"', sidebar)}
    for name in ("architecture/diagrams", "reference/diagrams", "requirements/diagrams"):
        assert "/.agents/" + name in sections


def test_original_gui_mockup_is_an_image_and_ships_unchanged():
    """The authored Excalidraw mockup must survive the docs build byte-for-byte."""
    import re
    from html import unescape
    from urllib.parse import urlsplit

    relative = Path(".agents/reference/images/GUI_mockup.svg")
    source = ROOT / relative
    assert source.is_file(), "The original SVG artwork must exist under images/"
    assert b"svg-source:excalidraw" in source.read_bytes()
    original_blob = subprocess.run(
        ["git", "hash-object", str(source)], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()
    assert (
        original_blob == "b693531ab78f3e07c1f6ff1452f59aa45d773a7d"
    ), "The original GUI mockup image was altered"

    page = (
        SITE / "repository-files" / "agents" / "reference" / "images" / "GUI_mockup.svg" / "index.html"
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
        ROOT / ".agents/requirements/diagrams/gui-mockup.mmd"
    ).exists(), "Do not replace the GUI image with a conceptual Mermaid diagram"


def test_published_docs_use_full_viewport_layout_with_operable_navigation_and_fullscreen():
    """Verify the shipped reader's real HTML, CSS and JavaScript contracts."""
    index = (SITE / "index.html").read_text(encoding="utf-8")
    css = (SITE / "assets" / "theme.css").read_text(encoding="utf-8")
    js = (SITE / "assets" / "theme.js").read_text(encoding="utf-8")

    assert "data-docs-layout" in index
    assert 'id="docs-navigation"' in index
    assert "data-nav-toggle" in index
    assert 'aria-controls="docs-navigation"' in index
    assert "data-fullscreen-toggle" in index
    assert 'aria-pressed="false"' in index

    assert 'html[data-layout="centered"] .layout' in css, "Centered mode must be available"
    assert "--content-max" not in css, "Main document must use the remaining viewport width"
    assert "grid-template-columns: var(--sidebar-width) minmax(0, 1fr) var(--toc-width)" in css
    assert 'html[data-nav-collapsed="true"] .layout' in css
    assert "max-width: none" in css
    assert "requestFullscreen()" in js and "exitFullscreen()" in js
    assert "fullscreenchange" in js
    assert "data-nav-collapsed" in js
    assert 'sidebar.classList.toggle("is-open")' in js
    assert 'navToggle.setAttribute("aria-expanded"' in js
    assert 'event.key === "Escape"' in js


def test_reading_width_and_independent_fullscreen_buttons():
    """The published browser app must offer distinct layout and fullscreen actions."""
    page = (SITE / "index.html").read_text(encoding="utf-8")
    stylesheet = (SITE / "assets/theme.css").read_text(encoding="utf-8")
    script = (SITE / "assets/theme.js").read_text(encoding="utf-8")
    assert page.count("data-layout-toggle") == 1
    assert page.count("data-fullscreen-toggle") == 1
    assert 'data-layout="centered"' in page
    assert 'aria-label="Use full-width layout"' in page
    assert "docs-layout" in page
    assert 'html[data-layout="centered"] .layout' in stylesheet
    assert 'html[data-layout="wide"] .icon-layout-centered' in stylesheet
    assert "requestFullscreen()" in script and "exitFullscreen()" in script
    assert 'localStorage.setItem("docs-layout"' in script
    assert 'root.setAttribute("data-layout"' in script


def test_navigation_sections_are_natively_collapsible_and_preserve_active_page():
    """Published navigation must expose working disclosure controls at every depth."""
    page = (SITE / "index.html").read_text(encoding="utf-8")
    css = (SITE / "assets/theme.css").read_text(encoding="utf-8")
    script = (SITE / "assets/theme.js").read_text(encoding="utf-8")
    assert 'class="nav__group"' in page
    assert "data-nav-section=" in page
    assert '<summary class="nav__label">' in page
    assert "nav__group[open]" in css
    assert "docs-sidebar-sections" in script
    assert "group.querySelector" in script
    assert 'group.addEventListener("toggle"' in script
    assert 'aria-current="page"' in page


def test_image_and_diagram_viewers_offer_an_accessible_modal():
    """Every graphic uses the same zoomable viewer with modal expansion."""
    css = (SITE / "assets/theme.css").read_text(encoding="utf-8")
    script = (SITE / "assets/diagrams.js").read_text(encoding="utf-8")
    index = (
        SITE / "repository-files" / "agents" / "reference" / "images" / "GUI_mockup.svg" / "index.html"
    )
    assert index.is_file()
    html = index.read_text(encoding="utf-8")
    assert 'class="diagram-viewer"' in html
    assert "assets/diagrams.js" in html
    assert '"Expand image in modal"' in script
    assert "dialog.showModal()" in script
    assert 'dialog.addEventListener("close"' in script
    assert 'dialog.setAttribute("aria-label", "Expanded image viewer")' in script
    assert "marker.replaceWith(root)" in script
    assert ".diagram-modal::backdrop" in css
    assert ".diagram-modal .diagram-viewer__viewport" in css
