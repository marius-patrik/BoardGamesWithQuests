"""Build the documentation tree from tracked repository content.

Markdown is published as written. Python packages are rendered with mkdocstrings;
other Python files receive source pages. All paths, titles and navigation are
derived from the checked-out repository, not a curated list of directories.
"""

import ast
import subprocess

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib
from pathlib import Path
from typing import Any

from properdocs.structure.files import File, Files

ROOT = Path(__file__).resolve().parents[2]


def tracked_files(root: Path = ROOT) -> list[Path]:
    """Discover all tracked Python and Markdown files, respecting Git's own index."""
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z", "--cached"],
        check=True,
        capture_output=True,
    )
    files = [root / Path(p.decode("utf-8")) for p in result.stdout.split(b"\0") if p]
    return sorted(
        (p for p in files if p.is_file() and p.suffix.lower() in {".md", ".py"}),
        key=lambda p: p.relative_to(root).as_posix(),
    )


def python_roots(root: Path = ROOT) -> list[Path]:
    """Read the project's Python import roots instead of listing packages by name."""
    project = root / "pyproject.toml"
    roots: list[Path] = []
    if project.exists():
        config = tomllib.loads(project.read_text(encoding="utf-8"))
        candidates = (
            config.get("tool", {}).get("pytest", {}).get("ini_options", {}).get("pythonpath", [])
        )
        if isinstance(candidates, str):
            candidates = candidates.split()
        roots += [root / entry for entry in candidates]
        setuptools = config.get("tool", {}).get("setuptools", {})
        roots += [
            root / entry
            for entry in setuptools.get("packages", {}).get("find", {}).get("where", [])
        ]
    roots.append(root)
    return [p.resolve() for p in dict.fromkeys(p for p in roots if p.is_dir())]


def import_name(path: Path, roots: list[Path]) -> str | None:
    """Return an importable dotted name, or None for standalone Python scripts."""
    sources = [item for item in roots if item != ROOT]
    for base in sources or roots:
        try:
            relative = path.relative_to(base)
        except ValueError:
            continue
        if len(relative.parts) == 1:
            continue
        package_parts = relative.parts[:-1]
        if not all(
            (base.joinpath(*package_parts[:i]) / "__init__.py").exists()
            for i in range(1, len(package_parts) + 1)
        ):
            continue
        tail = () if path.name == "__init__.py" else (path.stem,)
        return ".".join((*package_parts, *tail))
    return None


def display_name(stem: str) -> str:
    """Derive readable labels without a manually maintained title mapping."""
    return stem.replace("_", " ").replace("-", " ").title()


def public_path(path: Path) -> str:
    """Publish hidden tracked directories under ordinary URL-safe names."""
    return "/".join(part.lstrip(".") if part.startswith(".") else part for part in path.parts)


def pages_for(root: Path = ROOT) -> list[tuple[str, str]]:
    """Create virtual pages for every tracked Markdown and Python file."""
    pages: dict[str, str] = {}
    roots = python_roots(root)
    for path in tracked_files(root):
        relative = path.relative_to(root)
        if path.suffix.lower() == ".md":
            dest = (
                "index.md" if relative.as_posix().lower() == "readme.md" else public_path(relative)
            )
            if path.name.lower() == "readme.md" and len(relative.parts) > 1:
                dest = public_path(relative.parent.joinpath("index.md"))
            if dest not in pages or path.name.lower() != "readme.md":
                pages[dest] = path.read_text(encoding="utf-8")
            continue

        dotted = import_name(path, roots)
        if dotted is not None:
            dest = dotted.replace(".", "/") + ("/index.md" if path.name == "__init__.py" else ".md")
            body = f"# {display_name(path.parent.name if path.name == '__init__.py' else path.stem)}\n\n::: {dotted}\n"
        else:
            dest = public_path(relative.with_suffix(".md"))
            source = path.read_text(encoding="utf-8")
            try:
                summary = ast.get_docstring(ast.parse(source)) or ""
            except SyntaxError:
                summary = ""
            body = f"# {display_name(path.stem)}\n\n{summary}\n\n````python\n{source}\n````\n"
        if dest in pages:
            raise ValueError(f"Documentation page collision at {dest}: {relative}")
        pages[dest] = body

    if "index.md" not in pages:
        name = display_name(root.name)
        pages["index.md"] = f"# {name}\n"
    # Every directory receives a generated hub unless a real index or package index exists.
    directories = {Path(name).parent.as_posix() for name in pages}
    directories.discard(".")
    for directory in sorted(directories, key=lambda d: d.count("/"), reverse=True):
        index = f"{directory}/index.md"
        if index in pages:
            continue
        children = sorted(
            key for key in pages if Path(key).parent.as_posix() == directory and key != index
        )
        if children:
            items = "\n".join(
                f"- [{display_name(Path(key).stem)}]({Path(key).name})" for key in children
            )
            pages[index] = f"# {display_name(Path(directory).name)}\n\n{items}\n"
    return sorted(pages.items())


def navigation(pages: list[tuple[str, str]]) -> list[dict[str, Any]]:
    """Derive the exact navigation from the same pages emitted by on_files."""
    tree: dict[str, Any] = {}
    for dest, _ in pages:
        parts = Path(dest).with_suffix("").parts
        cursor = tree
        for part in parts[:-1]:
            cursor = cursor.setdefault(part, {})
        cursor[parts[-1]] = dest

    def render(node: dict[str, Any]) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for key, value in sorted(node.items(), key=lambda item: (item[0] != "index", item[0])):
            result.append({display_name(key): render(value) if isinstance(value, dict) else value})
        return result

    return render(tree)


def build_nav(root: Path = ROOT) -> tuple[list[dict[str, Any]], list[tuple[str, str]]]:
    """Build navigation and content together so their targets cannot diverge."""
    pages = pages_for(root)
    return navigation(pages), pages


def on_config(config: Any) -> Any:
    """Populate navigation from repository content before rendering."""
    config["nav"] = build_nav()[0]
    return config


def on_files(files: Files, config: Any) -> Files:
    """Materialize virtual pages without writing documentation sources to disk."""
    plugins = getattr(config, "plugins", None)
    if plugins is not None and not hasattr(plugins, "_current_plugin"):
        plugins._current_plugin = None
    for dest, body in build_nav()[1]:
        if files.get_file_from_path(dest) is None:
            files.append(File.generated(config, dest, content=body))
    # The actual reference diagram and code-derived architecture diagram are
    # generated on every build, so neither can silently diverge from its source.
    # ProperDocs imports this hook by file path rather than as a package.
    import sys

    scripts = str(Path(__file__).resolve().parent)
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    from generate_architecture_diagrams import generated_assets

    for dest, svg in generated_assets(ROOT).items():
        if files.get_file_from_path(dest) is None:
            files.append(File.generated(config, dest, content=svg))
    return files
