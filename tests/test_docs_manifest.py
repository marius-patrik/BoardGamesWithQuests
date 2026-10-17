"""Verify the documentation publisher's externally visible manifest contract.

Uses the same command that CI executes after staging real preview output, with
a temporary deployable site to ensure published selectors never advertise
unpublished builds.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLISHER = ROOT / ".github/scripts/build_docs.py"


def publish(site: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(PUBLISHER), "--manifest", "--site", str(site)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_published_manifest_lists_only_real_deployable_builds(tmp_path: Path) -> None:
    (tmp_path / "index.html").write_text("<!doctype html><title>Main</title>", encoding="utf-8")
    (tmp_path / "pr-328").mkdir()
    (tmp_path / "pr-328/index.html").write_text(
        "<!doctype html><title>PR</title>", encoding="utf-8"
    )
    (tmp_path / "pr-999").mkdir()
    (tmp_path / "pr-999/README.txt").write_text("not deployed", encoding="utf-8")
    (tmp_path / "branch/review").mkdir(parents=True)
    (tmp_path / "branch/review/index.html").write_text("<!doctype html>", encoding="utf-8")
    (tmp_path / "branch/unbuilt").mkdir()
    (tmp_path / "unrelated").mkdir()

    result = publish(tmp_path)
    assert result.returncode == 0, result.stderr
    output = json.loads((tmp_path / "versions.json").read_text(encoding="utf-8"))
    config = json.loads((ROOT / "repo.dfconfig").read_text(encoding="utf-8"))
    identity = config["repo"]["identity"]
    versions = output["versions"]
    assert versions == [
        {"name": identity["default_branch"], "path": ""},
        {"name": "review", "path": "branch/review"},
        {"name": "PR #328", "path": "pr-328"},
    ]
    assert output["projects"] == [
        {"name": item["name"].strip(), "url": item["url"].rstrip("/") + "/"}
        for item in config["repo"].get("documentation", {}).get("projects", [])
    ]
    assert all(
        entry["path"] == "" or (tmp_path / entry["path"] / "index.html").is_file()
        for entry in versions
    )


def test_missing_documentation_root_fails_without_publishing(tmp_path: Path) -> None:
    (tmp_path / "pr-328").mkdir()
    (tmp_path / "pr-328/index.html").write_text("<!doctype html>", encoding="utf-8")
    result = publish(tmp_path)
    assert result.returncode != 0
    assert not (tmp_path / "versions.json").exists()
