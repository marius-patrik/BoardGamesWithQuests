"""Observable CLI acceptance tests for published documentation version manifests.

These invoke the actual source generator in a new process against real temporary
site trees. Missing HTML pages must never be advertised as deployed builds.
"""

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / ".github" / "scripts" / "docs_manifest.py"


def generate_manifest(site: Path) -> dict:
    """Execute the shipped manifest CLI and load its on-disk output."""
    subprocess.run(
        [sys.executable, str(CLI), "--site", str(site)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads((site / "versions.json").read_text(encoding="utf-8"))


def add_page(site: Path, relative: str) -> None:
    path = site / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("<!doctype html><title>published</title>", encoding="utf-8")


def test_manifest_advertises_only_available_html_roots(tmp_path: Path) -> None:
    site = tmp_path / "site"
    add_page(site, "index.html")
    add_page(site, "pr-9/index.html")
    add_page(site, "pr-100/index.html")
    add_page(site, "branch/topic/index.html")
    (site / "pr-101").mkdir()
    (site / "branch" / "unused").mkdir()
    add_page(site, "pr-invalid/index.html")

    result = generate_manifest(site)
    assert result["versions"] == [
        {"name": "main", "path": ""},
        {"name": "topic", "path": "branch/topic"},
        {"name": "PR #100", "path": "pr-100"},
        {"name": "PR #9", "path": "pr-9"},
    ]


def test_manifest_reflects_removed_preview_after_regeneration(tmp_path: Path) -> None:
    site = tmp_path / "site"
    add_page(site, "index.html")
    add_page(site, "pr-73/index.html")
    initial = generate_manifest(site)
    assert {"name": "PR #73", "path": "pr-73"} in initial["versions"]

    (site / "pr-73" / "index.html").unlink()
    rebuilt = generate_manifest(site)
    assert rebuilt["versions"] == [{"name": "main", "path": ""}]


def test_manifest_is_deterministic_and_projects_are_from_configuration(tmp_path: Path) -> None:
    site = tmp_path / "site"
    add_page(site, "index.html")
    add_page(site, "branch/zeta/index.html")
    add_page(site, "branch/alpha/index.html")
    first = generate_manifest(site)
    first_bytes = (site / "versions.json").read_bytes()
    second = generate_manifest(site)
    assert (site / "versions.json").read_bytes() == first_bytes
    assert first == second
    assert [x["path"] for x in first["versions"]] == ["", "branch/alpha", "branch/zeta"]

    settings = json.loads((ROOT / ".github" / "darkfactory.json").read_text(encoding="utf-8"))
    expected = [
        {"name": item["name"], "url": item["url"]}
        for item in settings.get("documentation", {}).get("projects", [])
        if isinstance(item, dict) and item.get("name") and item.get("url")
    ]
    assert first["projects"] == expected
