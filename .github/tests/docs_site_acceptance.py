"""Black-box checks against a *built* ProperDocs artifact.

Explicitly invoked by documentation workflows after the site build; deliberately
excluded from normal Python test discovery, which runs before documentation builds.
"""

from __future__ import annotations

import re
import subprocess
from html import unescape
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "site"


def tracked() -> list[Path]:
    raw = subprocess.run(
        ["git", "ls-files", "--cached", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout
    return [Path(item.decode("utf-8", "surrogateescape")) for item in raw.split(b"\0") if item]


def page_for(path: str) -> Path:
    """Mirror the build's actual source-file page namespace."""
    return SITE / "repository-files" / path.removeprefix(".") / "index.html"


def rendered_svg(page: Path) -> str:
    html = page.read_text(encoding="utf-8")
    assert 'class="diagram-viewer"' in html
    assert 'class="mermaid"' not in html
    match = re.search(r'<img src="([^"]+\.svg)"', html)
    assert match, f"Mermaid image missing: {page}"
    image = (page.parent / urlsplit(unescape(match.group(1))).path).resolve()
    assert image.is_relative_to(SITE.resolve()) and image.is_file()
    result = image.read_text(encoding="utf-8")
    assert "<svg" in result and "</svg>" in result
    return result


def test_tracked_files_are_published_and_gitlinks_are_not_read_as_files():
    assert (SITE / "index.html").is_file()
    names = tracked()
    assert names
    for path in names:
        if path.as_posix() == ".darkfactory":  # This is a Git submodule, not a file.
            continue
        public = "/".join(part.lstrip(".") for part in path.parts)
        if path.suffix.lower() == ".md":
            dest = (
                SITE.joinpath(*public.split("/")[:-1], "index.html")
                if path.name.lower() == "readme.md"
                else SITE / (public.removesuffix(".md") + "/index.html")
            )
        else:
            dest = SITE / "repository-files" / public / "index.html"
        assert dest.is_file(), f"No navigable page for tracked source {path}"


def test_navigation_matches_tracked_folders_plus_generated_real_code_diagrams():
    names = tracked()
    expected = {"/" + "/".join(p.parts[:n]) for p in names for n in range(1, len(p.parts))}
    # Generated code-viewer pages live only inside a folder with a real tracked
    # README. No generated page may invent a new sidebar directory.
    assert (ROOT / ".agents/architecture/diagrams/README.md").is_file()
    document = (SITE / "index.html").read_text(encoding="utf-8")
    sidebar = document.split('<aside class="sidebar"', 1)[1].split("</aside>", 1)[0]
    actual = {unescape(p) for p in re.findall(r'data-nav-section="([^"]+)"', sidebar)}
    assert (
        actual == expected
    ), f"Invented/missing sidebar groups: extra={actual-expected}; missing={expected-actual}"


def test_generated_code_diagrams_and_preserved_reference_sources_render():
    for group, names in (
        ("architecture", ("ast", "uml")),
        ("reference", ("mvc", "uml")),
    ):
        for stem in names:
            path = f"agents/{group}/diagrams/{stem}.mmd"
            raw = SITE / path
            assert raw.is_file(), path
            assert raw.read_text(encoding="utf-8").startswith(
                ("flowchart", "classDiagram", "erDiagram")
            )
            svg = rendered_svg(SITE / "repository-files" / path / "index.html")
            if group == "architecture" and stem == "uml":
                assert "GameController" in svg, "Actual Python controller was omitted"
    assert not (ROOT / ".agents/requirements").exists()
    assert not list((ROOT / ".agents/architecture/diagrams").glob("*.mmd"))
    assert {p.name for p in (ROOT / ".agents/reference/diagrams").glob("*.mmd")} == {
        "mvc.mmd",
        "uml.mmd",
    }


def test_original_gui_artwork_is_unchanged_and_visually_published():
    source = ROOT / ".agents/reference/images/GUI_mockup.svg"
    assert source.is_file()
    assert b"svg-source:excalidraw" in source.read_bytes()
    checksum = subprocess.run(
        ["git", "hash-object", str(source)],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    ).stdout.strip()
    assert checksum == "b693531ab78f3e07c1f6ff1452f59aa45d773a7d"
    page = SITE / "repository-files/agents/reference/images/GUI_mockup.svg/index.html"
    html = page.read_text(encoding="utf-8")
    assert 'class="diagram-viewer"' in html
    image = re.search(r'<img src="([^"]+)"', html)
    assert image
    dest = (page.parent / urlsplit(unescape(image.group(1))).path).resolve()
    assert dest.is_relative_to(SITE.resolve()) and dest.read_bytes() == source.read_bytes()


def test_layout_controls_and_nested_nav_are_shipped():
    html = (SITE / "index.html").read_text(encoding="utf-8")
    css = (SITE / "assets/theme.css").read_text(encoding="utf-8")
    js = (SITE / "assets/theme.js").read_text(encoding="utf-8")
    assert 'id="docs-navigation"' in html
    assert "data-nav-toggle" in html
    assert html.count("data-fullscreen-toggle") == 1
    assert html.count("data-layout-toggle") == 1
    assert 'class="nav__group"' in html
    assert '<summary class="nav__label">' in html
    assert 'aria-current="page"' in html
    assert 'html[data-layout="centered"] .layout' in css
    assert "grid-template-columns: var(--sidebar-width) minmax(0, 1fr) var(--toc-width)" in css
    assert "nav__group[open]" in css
    assert "requestFullscreen()" in js and "exitFullscreen()" in js
    assert "docs-sidebar-sections" in js
    assert 'localStorage.setItem("docs-layout"' in js


def test_image_viewer_modal_is_wired_in_published_assets():
    css = (SITE / "assets/theme.css").read_text(encoding="utf-8")
    js = (SITE / "assets/diagrams.js").read_text(encoding="utf-8")
    assert '"Expand image in modal"' in js
    assert "dialog.showModal()" in js
    assert 'dialog.addEventListener("close"' in js
    assert "marker.replaceWith(root)" in js
    assert ".diagram-modal::backdrop" in css
