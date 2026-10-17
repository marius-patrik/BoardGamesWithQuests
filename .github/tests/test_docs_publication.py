"""Behavior tests for publishing branch previews independently of main docs."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ASSEMBLER = Path(__file__).resolve().parents[1] / "scripts" / "assemble_docs.py"


def invoke(staging: Path, site: Path, *open_prs: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(ASSEMBLER),
            "--staging",
            str(staging),
            "--site",
            str(site),
            "--open-prs",
            *(str(number) for number in open_prs),
        ],
        capture_output=True,
        text=True,
    )


def test_publishes_pr_even_without_main_site(tmp_path: Path) -> None:
    staging = tmp_path / "staging"
    preview = staging / "pr-328"
    preview.mkdir(parents=True)
    (preview / "index.html").write_text("<h1>Independent PR</h1>", encoding="utf-8")
    (preview / "asset.css").write_text(".root {}", encoding="utf-8")
    (preview / ".preview-head").write_text("a" * 40, encoding="utf-8")
    site = tmp_path / "site"

    result = invoke(staging, site, 328)
    assert result.returncode == 0, result.stderr
    assert (site / "index.html").is_file(), "A missing main build should produce a landing page"
    assert 'href="pr-328/"' in (site / "index.html").read_text()
    assert (site / "pr-328/index.html").read_text() == "<h1>Independent PR</h1>"
    assert (site / "pr-328/asset.css").read_text() == ".root {}"
    assert (site / "pr-328/.preview-head").read_text() == "a" * 40
    assert (site / ".nojekyll").exists()


def test_preserves_last_passing_main_and_filters_closed_previews(tmp_path: Path) -> None:
    staging = tmp_path / "staging"
    staging.mkdir()
    (staging / "index.html").write_text("<h1>Last passing main</h1>", encoding="utf-8")
    (staging / "assets").mkdir()
    (staging / "assets/file.css").write_text("body {}", encoding="utf-8")
    for num in (302, 328, 329):
        (staging / f"pr-{num}").mkdir()
    (staging / "pr-302/index.html").write_text("closed")
    (staging / "pr-328/index.html").write_text("open")
    # PR 329 is open but missing its index, so it must not be advertised.
    site = tmp_path / "site"

    result = invoke(staging, site, 328, 329)
    assert result.returncode == 0, result.stderr
    assert (site / "index.html").read_text() == "<h1>Last passing main</h1>"
    assert (site / "assets/file.css").read_text() == "body {}"
    assert not (site / "pr-302").exists()
    assert (site / "pr-328/index.html").is_file()
    assert not (site / "pr-329").exists()


def test_missing_staging_fails_instead_of_reporting_success(tmp_path: Path) -> None:
    result = invoke(tmp_path / "missing", tmp_path / "site", 328)
    assert result.returncode != 0
    assert "missing" in result.stderr.lower()


def test_rejects_symlink_payload_in_untrusted_artifact(tmp_path: Path) -> None:
    staging = tmp_path / "staging"
    preview = staging / "pr-328"
    preview.mkdir(parents=True)
    (preview / "index.html").symlink_to(tmp_path / "outside")
    site = tmp_path / "site"

    result = invoke(staging, site, 328)
    assert result.returncode != 0
    assert "symlink" in result.stderr.lower()
    assert not site.exists()


def test_replaces_stale_deployed_preview_on_update(tmp_path: Path) -> None:
    staging = tmp_path / "staging"
    preview = staging / "pr-328"
    preview.mkdir(parents=True)
    (preview / "index.html").write_text("new", encoding="utf-8")
    site = tmp_path / "site"
    (site / "pr-328").mkdir(parents=True)
    (site / "pr-328/index.html").write_text("old", encoding="utf-8")

    result = invoke(staging, site, 328)
    assert result.returncode == 0, result.stderr
    assert (site / "pr-328/index.html").read_text() == "new"
