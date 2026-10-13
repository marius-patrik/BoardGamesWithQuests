"""Verify source-authored documentation through real strict MkDocs HTML builds."""

from html.parser import HTMLParser
from pathlib import Path
import shutil
import subprocess
import sys
from urllib.parse import unquote, urlsplit

import pytest

ROOT = Path(__file__).resolve().parents[1]


class RenderedPage(HTMLParser):
    """Collect observable HTML text, navigation links and API anchors."""

    def __init__(self, path: Path) -> None:
        """Read an actual generated HTML page for consumer-level assertions."""
        super().__init__()
        self.text: list[str] = []
        self.links: list[str] = []
        self.identifiers: set[str] = set()
        self.signatures: dict[str, list[str]] = {}
        self._heading: str | None = None
        self.feed(path.read_text(encoding="utf-8"))

    def handle_data(self, data: str) -> None:
        """Preserve rendered text in display order."""
        self.text.append(data)
        if self._heading is not None:
            self.signatures[self._heading].append(data)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Observe link destinations and stable API anchor identifiers."""
        attributes = dict(attrs)
        if tag == "a" and attributes.get("href"):
            self.links.append(attributes["href"])
        if attributes.get("id"):
            self.identifiers.add(attributes["id"])
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"} and "doc-heading" in attributes.get(
            "class", ""
        ):
            self._heading = attributes["id"]
            self.signatures[self._heading] = []

    def handle_endtag(self, tag: str) -> None:
        """Separate rendered API headings from printed source-code blocks."""
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self._heading = None

    @property
    def content(self) -> str:
        """Return readable rendered text without depending on theme whitespace."""
        return " ".join(" ".join(self.text).split())


def command(repo: Path, *args: str) -> subprocess.CompletedProcess:
    """Run Git only inside a disposable documentation fixture."""
    return subprocess.run(
        ["git", "-C", str(repo), *args], check=True, capture_output=True, text=True
    )


@pytest.fixture
def documented_repository(tmp_path: Path) -> Path:
    """Create real tracked Python source and retained non-page specifications."""
    repo = tmp_path / "repository"
    repo.mkdir()
    (repo / ".gitignore").write_text("__pycache__/\n*.pyc\nsite/\n", encoding="utf-8")
    shutil.copytree(
        ROOT / ".github" / "scripts",
        repo / ".github" / "scripts",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    shutil.copytree(ROOT / ".github" / "docs-ui", repo / ".github" / "docs-ui")
    shutil.copy(ROOT / "mkdocs.yml", repo / "mkdocs.yml")
    (repo / "pyproject.toml").write_text(
        '[tool.setuptools.packages.find]\nwhere = ["packages"]\n', encoding="utf-8"
    )
    package = repo / "packages" / "fixture_api"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text(
        '"""Fixture engine operations authored in Python."""\n', encoding="utf-8"
    )
    (package / "rules.py").write_text(
        '''"""Participant authorization from an explicit revision."""


def authorize(side: int, revision: int) -> bool:
    """Authorize a participant against a nonnegative revision.

    Args:
        side: Canonical participant side, one or negative one.
        revision: Revision supplied by the external caller.

    Returns:
        Whether the participant may submit an action.

    Raises:
        ValueError: The participant side is invalid.
    """
    if side not in (-1, 1):
        raise ValueError("unknown side")
    return revision >= 0


class Authority:
    """A source-defined authority used by the live architecture diagram."""
''',
        encoding="utf-8",
    )
    notes = repo / ".agents" / "notes"
    notes.mkdir(parents=True)
    (notes / "PRD.md").write_text(
        "# Retained specification\nMANUAL_PAGE_MUST_NOT_BE_PUBLISHED\n", encoding="utf-8"
    )
    (repo / "README.md").write_text(
        "# Static manual index\nMANUAL_PAGE_MUST_NOT_BE_PUBLISHED\n", encoding="utf-8"
    )
    command(repo, "init", "--quiet")
    command(repo, "add", ".")
    command(
        repo,
        "-c",
        "user.name=Documentation test",
        "-c",
        "user.email=docs@example.invalid",
        "commit",
        "--quiet",
        "-m",
        "test(docs): define source fixture",
    )
    return repo


def build(repo: Path, site: Path) -> subprocess.CompletedProcess:
    """Execute the supported strict build boundary with a separate output path."""
    return subprocess.run(
        [
            sys.executable,
            str(ROOT / ".github" / "scripts" / "build_docs.py"),
            "--repo",
            str(repo),
            "--site",
            str(site),
        ],
        capture_output=True,
        text=True,
    )


def test_strict_build_renders_source_signatures_google_docs_and_valid_navigation(
    documented_repository: Path, tmp_path: Path
) -> None:
    """FR-82: a reader can follow generated navigation to accurate source APIs."""
    site = tmp_path / "site"
    result = build(documented_repository, site)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "WARNING" not in result.stderr and "ERROR" not in result.stderr
    api = RenderedPage(site / "fixture_api" / "rules" / "index.html")
    assert "fixture_api.rules.authorize" in api.identifiers
    signature = " ".join("".join(api.signatures["fixture_api.rules.authorize"]).split())
    assert "authorize(side: int, revision: int) -> bool" in signature
    assert "authorize" in api.content and "side" in api.content and "revision" in api.content
    assert "int" in api.content and "bool" in api.content
    assert "Canonical participant side, one or negative one." in api.content
    assert "Whether the participant may submit an action." in api.content
    assert "The participant side is invalid." in api.content
    assert "Parameters:" in api.content and "Returns:" in api.content and "Raises:" in api.content
    home = RenderedPage(site / "index.html")
    assert "Fixture engine operations authored in Python." in home.content
    assert any("fixture_api" in link for link in home.links)
    assert any(link.endswith("implementation-classes.svg") for link in home.links)
    assert any("rules" in link for link in api.links)
    for path in site.rglob("*.html"):
        page = RenderedPage(path)
        assert "MANUAL_PAGE_MUST_NOT_BE_PUBLISHED" not in page.content
        for href in page.links:
            destination = urlsplit(href)
            if destination.scheme or destination.netloc or destination.path.startswith("/"):
                continue
            target = (
                (path.parent / unquote(destination.path)).resolve() if destination.path else path
            )
            if target.is_dir():
                target /= "index.html"
            assert target.exists(), f"{path.relative_to(site)} links to absent {href}"
            if destination.fragment and target.suffix == ".html":
                assert unquote(destination.fragment) in RenderedPage(target).identifiers, href
    assert not (site / "agents" / "notes" / "PRD" / "index.html").exists()
    source_revision = command(documented_repository, "rev-parse", "HEAD").stdout.strip()
    assert any(f"/blob/{source_revision}/.agents/notes/PRD.md" in link for link in home.links)
    assert (
        site / "agents" / "notes" / "diagrams" / "implementation-classes.svg"
    ).stat().st_size > 0
    assert not any(
        (documented_repository / name).exists() for name in ("docs", ".docs", ".agents/docs")
    )
    assert command(documented_repository, "status", "--porcelain").stdout == ""


def test_new_source_module_appears_without_manual_pages_or_navigation(
    documented_repository: Path, tmp_path: Path
) -> None:
    """FR-82: tracked source changes propagate into generated API and navigation."""
    source = documented_repository / "packages" / "fixture_api" / "recovery.py"
    source.write_text(
        '''"""Recover a participant session from source-defined history."""


def recover(identity: str) -> str:
    """Return the participant identifier used for recovery.

    Args:
        identity: Verified participant identifier.

    Returns:
        Identifier selected for authoritative recovery.
    """
    return identity
''',
        encoding="utf-8",
    )
    command(documented_repository, "add", str(source))
    site = tmp_path / "site"
    result = subprocess.run(
        [sys.executable, "-m", "mkdocs", "build", "--strict", "--site-dir", str(site)],
        cwd=documented_repository,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    api = RenderedPage(site / "fixture_api" / "recovery" / "index.html")
    assert "fixture_api.recovery.recover" in api.identifiers
    assert "Identifier selected for authoritative recovery." in api.content
    assert any("recovery" in link for link in RenderedPage(site / "index.html").links)
    assert not (site / "main.html").exists()
    assert not (site / "partials").exists()
    assert command(documented_repository, "diff", "--name-only").stdout == ""


@pytest.mark.parametrize(
    "source",
    [
        '"""Malformed source must fail strict documentation."""\ndef invalid(:\n',
        '"""See [missing API][fixture_api.does_not_exist]."""\n',
    ],
)
def test_invalid_source_or_unresolved_docstring_reference_blocks_strict_build(
    documented_repository: Path, tmp_path: Path, source: str
) -> None:
    """FR-82: broken source/API references cannot produce an accepted site."""
    path = documented_repository / "packages" / "fixture_api" / "broken.py"
    path.write_text(source, encoding="utf-8")
    command(documented_repository, "add", str(path))
    result = build(documented_repository, tmp_path / "site")
    assert result.returncode != 0, result.stdout + result.stderr
    assert "SyntaxError" in result.stderr or "fixture_api.does_not_exist" in result.stderr
