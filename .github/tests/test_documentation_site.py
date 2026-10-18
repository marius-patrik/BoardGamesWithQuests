"""Acceptance tests for the actual published documentation artifact."""
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "site"


def tracked_paths() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z", "--cached"], cwd=ROOT,
        capture_output=True, check=True,
    )
    return [
        Path(value.decode("utf-8", "surrogateescape"))
        for value in result.stdout.split(b"\0") if value
    ]


def public_path(path: Path) -> Path:
    return Path(*(segment.lstrip(".") if segment.startswith(".") else segment for segment in path.parts))


def test_every_tracked_file_has_a_published_navigation_page() -> None:
    assert (SITE / "index.html").is_file(), "Documentation root was not built"
    paths = tracked_paths()
    assert paths, "Git source inventory is empty"
    for source in paths:
        published = public_path(source)
        if source.suffix.lower() == ".md":
            if source.name.lower() == "readme.md":
                target = SITE / published.parent / "index.html"
            else:
                target = SITE / published.with_suffix("") / "index.html"
        else:
            target = SITE / "repository-files" / published / "index.html"
        assert target.is_file(), f"Missing published page for {source}: {target}"


def test_original_assignment_image_is_visible_and_unchanged() -> None:
    source = ROOT / ".agents/reference/images/GUI_mockup.svg"
    assert source.is_file(), "The original assignment image must be retained"
    page = SITE / "repository-files/agents/reference/images/GUI_mockup.svg/index.html"
    assert page.is_file(), "The original image needs a navigable viewer"
    html = page.read_text(encoding="utf-8")
    assert 'class="diagram-viewer"' in html
    assert "<img" in html
    image = SITE / "agents/reference/images/GUI_mockup.svg"
    assert image.is_file(), "The original image must be deployed"
    assert image.read_bytes() == source.read_bytes(), "Published artwork differs from original"


def test_actual_code_diagrams_are_available_from_the_built_site() -> None:
    for name in ("ast", "uml"):
        source = SITE / f"agents/architecture/diagrams/{name}.mmd"
        page = SITE / f"repository-files/agents/architecture/diagrams/{name}.mmd/index.html"
        assert source.is_file(), f"Missing generated Mermaid source: {name}"
        assert source.read_text(encoding="utf-8").startswith(("classDiagram", "flowchart"))
        assert page.is_file(), f"Missing diagram viewer: {name}"
        assert "diagram-viewer" in page.read_text(encoding="utf-8")
