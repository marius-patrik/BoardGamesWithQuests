"""Generate MkDocs pages and navigation exclusively from Python source docstrings.

Authoritative Markdown specifications remain repository source references. The site
renders importable package APIs and source-derived diagrams without copying Markdown
or creating a committed documentation source directory.
"""

from __future__ import annotations

import ast
import subprocess
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

from mkdocs.structure.files import File, Files
from mkdocs.plugins import event_priority

ROOT = Path(__file__).resolve().parents[2]


def tracked_files(root: Path = ROOT) -> list[Path]:
    """Discover tracked Python files from the repository index.

    Args:
        root: Repository whose source documents the application.

    Returns:
        Existing Python files in stable source-path order.
    """
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z", "--cached"],
        check=True,
        capture_output=True,
    )
    files = [root / Path(item.decode("utf-8")) for item in result.stdout.split(b"\0") if item]
    return sorted(
        (
            path
            for path in files
            if path.is_file() and not path.is_symlink() and path.suffix == ".py"
        ),
        key=lambda path: path.relative_to(root).as_posix(),
    )


def python_roots(root: Path = ROOT) -> list[Path]:
    """Derive import roots from native Python build metadata.

    Args:
        root: Repository containing pyproject.toml.

    Returns:
        Distinct existing package directories followed by the repository root.
    """
    config = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    setuptools = config.get("tool", {}).get("setuptools", {})
    sources = setuptools.get("packages", {}).get("find", {}).get("where", [])
    roots = [root / entry for entry in sources]
    roots.append(root)
    return list(dict.fromkeys(path.resolve() for path in roots if path.is_dir()))


def import_name(path: Path, roots: list[Path]) -> str | None:
    """Identify Python package modules without a manually curated package list.

    Args:
        path: Tracked Python source file.
        roots: Package discovery roots.

    Returns:
        Dotted import identifier, or None for standalone scripts and tests.
    """
    for base in roots:
        try:
            relative = path.relative_to(base)
        except ValueError:
            continue
        if len(relative.parts) < 2:
            continue
        packages = relative.parts[:-1]
        if not all(
            (base.joinpath(*packages[:index]) / "__init__.py").is_file()
            for index in range(1, len(packages) + 1)
        ):
            continue
        tail = () if path.name == "__init__.py" else (path.stem,)
        return ".".join((*packages, *tail))
    return None


def display_name(stem: str) -> str:
    """Derive a navigation label from a source module or package name.

    Args:
        stem: Python identifier.

    Returns:
        Readable source-derived label.
    """
    return stem.replace("_", " ").title()


def pages_for(root: Path = ROOT) -> list[tuple[str, str]]:
    """Create API and homepage content from package source and its docstrings.

    Args:
        root: Source repository to document.

    Returns:
        Virtual Markdown paths and generated content with no static page inputs.

    Raises:
        SyntaxError: A Python module cannot be parsed.
        ValueError: No importable Python source or colliding page paths are found.
    """
    pages: dict[str, str] = {}
    packages: list[tuple[str, str]] = []
    roots = python_roots(root)
    for path in tracked_files(root):
        dotted = import_name(path, roots)
        if dotted is None:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        summary = ast.get_docstring(tree) or dotted
        destination = dotted.replace(".", "/") + (
            "/index.md" if path.name == "__init__.py" else ".md"
        )
        if destination in pages:
            raise ValueError(f"Documentation page collision: {destination}")
        pages[destination] = f"# {summary.splitlines()[0]}\n\n::: {dotted}\n"
        if "." not in dotted:
            packages.append((destination, summary))
    if not pages:
        raise ValueError("Documentation requires importable Python package source")
    home = []
    for destination, summary in sorted(packages):
        home.append(f"## [{summary.splitlines()[0]}]({destination})\n\n{summary}\n")
    if not home:
        destination = min(pages)
        home.append(f"[{destination}]({destination})")
    pages["index.md"] = "\n".join(home)
    return sorted(pages.items())


def navigation(pages: list[tuple[str, str]]) -> list[dict[str, Any]]:
    """Generate hierarchical navigation from the emitted module paths.

    Args:
        pages: Generated page path/content pairs.

    Returns:
        MkDocs navigation entries resolving to the same generated files.
    """
    tree: dict[str, Any] = {}
    for destination, _ in pages:
        parts = Path(destination).with_suffix("").parts
        cursor = tree
        for part in parts[:-1]:
            cursor = cursor.setdefault(part, {})
        cursor[parts[-1]] = destination

    def render(node: dict[str, Any]) -> list[dict[str, Any]]:
        return [
            {display_name(key): render(value) if isinstance(value, dict) else value}
            for key, value in sorted(node.items(), key=lambda item: (item[0] != "index", item[0]))
        ]

    return render(tree)


@event_priority(100)
def on_config(config: Any) -> Any:
    """Bind navigation and repository reference links to the checked-out source.

    Args:
        config: MkDocs configuration under construction.

    Returns:
        Configuration with generated navigation and immutable source references.
    """
    handlers = config.plugins["mkdocstrings"].config.handlers
    handlers.setdefault("python", {})["paths"] = [str(path) for path in python_roots()]
    config["nav"] = navigation(pages_for())
    revision = subprocess.check_output(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True
    ).strip()
    base = config["repo_url"].rstrip("/") + "/blob/" + revision + "/"
    config["extra"]["source_references"] = [
        {"name": display_name(path.stem), "url": base + path.relative_to(ROOT).as_posix()}
        for path in sorted((ROOT / ".agents" / "notes").glob("*.md"))
    ]
    return config


def on_files(files: Files, config: Any) -> Files:
    """Supply virtual source API pages, theme assets and live architecture SVGs.

    Args:
        files: Files collected by MkDocs.
        config: Resolved MkDocs configuration.

    Returns:
        File collection containing only generated documentation pages and assets.
    """
    for collected in list(files):
        files.remove(collected)
    for destination, body in pages_for():
        files.append(File.generated(config, destination, content=body))
    import sys

    scripts = str(Path(__file__).resolve().parent)
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    from generate_architecture_diagrams import generated_assets

    diagrams: list[dict[str, str]] = []
    for destination, svg in generated_assets(ROOT).items():
        files.append(File.generated(config, destination, content=svg))
        diagrams.append({"name": display_name(Path(destination).stem), "path": destination})
    references = ROOT / ".agents" / "notes" / "diagrams"
    for source in sorted(references.glob("reference-*.svg")):
        destination = "agents/notes/diagrams/" + source.name
        files.append(
            File.generated(
                config,
                destination,
                content=source.read_text(encoding="utf-8"),
            )
        )
        diagrams.append({"name": display_name(source.stem), "path": destination})
    config["extra"]["diagram_assets"] = diagrams
    for source in sorted((ROOT / ".github" / "docs-ui" / "assets").iterdir()):
        if source.is_file():
            files.append(
                File.generated(
                    config, "assets/" + source.name, content=source.read_text(encoding="utf-8")
                )
            )
    return files
