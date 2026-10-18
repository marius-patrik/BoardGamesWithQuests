"""The generated docs renderer must handle tracked files literally named index.html."""

from pathlib import Path
import sys

SCRIPTS = Path(__file__).resolve().parents[1] / ".github/scripts"
sys.path.insert(0, str(SCRIPTS))
from build_docs import render_published_mermaid


def test_file_named_index_html_does_not_crash_renderer(tmp_path: Path):
    source_page_directory = tmp_path / "repository-files/packages/client/index.html"
    source_page_directory.mkdir(parents=True)
    (source_page_directory / "index.html").write_text("<html><body>Source viewer</body></html>", encoding="utf-8")
    (tmp_path / "index.html").write_text("<html><body>Site root</body></html>", encoding="utf-8")
    render_published_mermaid(tmp_path)
    assert (tmp_path / "index.html").is_file()
    assert (source_page_directory / "index.html").is_file()
