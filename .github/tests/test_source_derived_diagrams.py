"""Source-derived architecture diagrams must reflect the actual current Git tree."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import build_docs


def test_architecture_viewers_are_generated_from_current_python_source(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / "source.py").write_text("class LiveClass:\\n    def run(self):\\n        return 42\\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(tmp_path), "add", "source.py"], check=True)
    pages = build_docs.pages_for(tmp_path)
    by_path = {source: body for source, _, body in pages}
    assert ".agents/architecture/diagrams/ast.mmd" in by_path
    assert ".agents/architecture/diagrams/uml.mmd" in by_path
    assert "source.py" in by_path[".agents/architecture/diagrams/ast.mmd"]
    assert "LiveClass" in by_path[".agents/architecture/diagrams/uml.mmd"]
    assert "diagram-viewer" in by_path[".agents/architecture/diagrams/uml.mmd"]
    assert len(pages) == len(by_path)
