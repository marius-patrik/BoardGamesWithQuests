"""Regression: tracked files named index.html cannot break diagram rendering."""

import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "build_docs.py"


def test_diagram_renderer_ignores_index_html_named_directories(tmp_path: Path) -> None:
    # A tracked packages/client/index.html source page generates this directory.
    nested = tmp_path / "repository-files" / "packages" / "client" / "index.html"
    nested.mkdir(parents=True)
    (nested / "index.html").write_text("<html>source page</html>", encoding="utf-8")
    (tmp_path / "index.html").write_text("<html>site root</html>", encoding="utf-8")

    spec = importlib.util.spec_from_file_location("_bgwq_build_docs_regression", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    module.render_published_mermaid(tmp_path)

    assert (tmp_path / "index.html").read_text(encoding="utf-8") == "<html>site root</html>"
    assert (nested / "index.html").is_file()
