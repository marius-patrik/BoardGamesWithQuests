"""The docs publisher must handle Git's real submodule entry without reading a directory."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import build_docs


def test_gitlink_is_not_exposed_as_a_fake_source_file(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / ".darkfactory").mkdir()
    (tmp_path / ".gitmodules").write_text(
        '[submodule ".darkfactory"]\\n  path = .darkfactory\\n  url = https://github.com/marius-patrik/DarkFactory.git\\n',
        encoding="utf-8",
    )
    (tmp_path / "README.md").write_text("# Actual source\\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(tmp_path), "add", "README.md", ".gitmodules"], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(tmp_path),
            "update-index",
            "--add",
            "--cacheinfo",
            "160000,fc5896c9ffbf9b1ac5762a271ec2b26ee0efafd4,.darkfactory",
        ],
        check=True,
    )
    pages = build_docs.pages_for(tmp_path)
    assert {entry[0] for entry in pages} == {"README.md", ".gitmodules"}
    assert any("Actual source" in page[2] for page in pages)
