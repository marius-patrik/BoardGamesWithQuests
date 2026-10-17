<<<<<<< HEAD
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
||||||| 07086322
"""Dynamic MkDocs hook for generating virtual documentation pages from Python docstrings."""
=======
"""Documentation hooks that generate the entire site tree from the repository layout.

Nothing about the documentation is stored. ``properdocs.yml`` points ``docs_dir`` at a
placeholder child directory and every page - the overview, the architecture notes and one
page per Python module - is emitted here as a virtual file.

The navigation is built by the same walk that emits the pages, so the two cannot drift:
adding, renaming or deleting a module needs no configuration edit, and a navigation entry
can never point at a page that does not exist. That is what `--strict` would otherwise
turn into a build failure.
"""
>>>>>>> tmp155

<<<<<<< HEAD
from mkdocs.structure.files import File, Files
from mkdocs.plugins import event_priority

ROOT = Path(__file__).resolve().parents[2]
||||||| 07086322
import os
import shutil
from typing import Any, List, Optional, Tuple, Union, MutableMapping
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.structure.files import File, Files
=======
import os
import shutil
from typing import Any, Dict, List, Optional, Tuple, Union

from properdocs.structure.files import File, Files

#: Importable packages, as (directory below the repository root, documentation path) pairs,
#: in navigation order. The packages live under ``src/``, so the directory and the
#: documentation path differ: the walk reads ``src/model`` but the emitted page is
#: ``model/game/board.md`` and its mkdocstrings directive resolves ``model.game.board``.
SOURCE_ROOTS: Tuple[Tuple[str, str], ...] = (
    ("src/model", "model"),
    ("src/controller", "controller"),
    ("src/view", "view"),
    ("src/games", "games"),
)

#: Navigation section label for each documentation path root.
SECTION_LABELS: Dict[str, str] = {
    "model": "Model",
    "controller": "Controllers",
    "view": "View",
    "games": "Games",
}

#: A generated page: its documentation path, its navigation label and its Markdown body.
Page = Tuple[str, str, str]
>>>>>>> tmp155


<<<<<<< HEAD
def tracked_files(root: Path = ROOT) -> list[Path]:
    """Discover tracked Python files from the repository index.

||||||| 07086322
def _get_repo_root(config: Any) -> str:
    """Resolve the repository root directory from configuration.

    Prioritizes config.config_file_path and __file__, falling back to docs_dir.

=======
def _get_repo_root(config: Any) -> str:
    """Resolve the repository root directory from configuration.

>>>>>>> tmp155
    Args:
<<<<<<< HEAD
        root: Repository whose source documents the application.
||||||| 07086322
        config (Any): The MkDocs configuration object or dictionary.
=======
        config: The documentation configuration object or dictionary.
>>>>>>> tmp155

    Returns:
<<<<<<< HEAD
        Existing Python files in stable source-path order.
||||||| 07086322
        str: Absolute path to the repository root directory.
=======
        Absolute path to the repository root directory.
>>>>>>> tmp155
    """
<<<<<<< HEAD
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
||||||| 07086322
    if hasattr(config, "config_file_path") and config.config_file_path:
        return os.path.dirname(os.path.abspath(config.config_file_path))
    if isinstance(config, dict) and config.get("config_file_path"):
        return os.path.dirname(os.path.abspath(config["config_file_path"]))

    docs_dir = (
        config.get("docs_dir") if hasattr(config, "get") else getattr(config, "docs_dir", None)
=======
    config_file = (
        config.get("config_file_path")
        if hasattr(config, "get")
        else getattr(config, "config_file_path", None)
    )
    if config_file:
        return os.path.dirname(os.path.abspath(config_file))

    docs_dir = (
        config.get("docs_dir") if hasattr(config, "get") else getattr(config, "docs_dir", None)
>>>>>>> tmp155
    )
<<<<<<< HEAD


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
<<<<<<< HEAD
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
||||||| b45d2e0f
        title = os.path.splitext(name)[0].replace("_", " ").title()
        pages.append((f"notes/{name}", title, content))
||||||| 07086322
    hook_repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    if docs_dir:
        docs_parent = os.path.abspath(os.path.join(docs_dir, ".."))
        try:
            if os.path.commonpath([docs_parent, hook_repo_root]) != hook_repo_root:
                return docs_parent
        except ValueError:
            return docs_parent
=======
    if docs_dir:
        return os.path.dirname(os.path.abspath(docs_dir))
>>>>>>> tmp155

<<<<<<< HEAD
    index_path = os.path.join(notes_dir, "index.md")
    if os.path.isfile(index_path):
        try:
            with open(index_path, "r", encoding="utf-8") as handle:
                pages.append(("notes/index.md", "Overview", handle.read()))
        except (OSError, UnicodeDecodeError) as error:
            print(f"Warning: Failed to read notes index {index_path}: {error}")
    if pages:
        hub_content = ["# Architecture & Design Notes", ""]
        for doc_path, label, _ in pages:
            if doc_path == "notes/index.md":
                continue
            hub_content.append(f"- [{label}]({os.path.basename(doc_path)})")
        if not any(doc_path == "notes/index.md" for doc_path, _, _ in pages):
            pages.append(("notes/index.md", "Overview", "\n".join(hub_content) + "\n"))
    return pages
=======
        title = os.path.splitext(name)[0].replace("_", " ").title()
        pages.append((f"notes/{name}", title, content))

    index_path = os.path.join(notes_dir, "index.md")
    if os.path.isfile(index_path):
        try:
            with open(index_path, "r", encoding="utf-8") as handle:
                pages.append(("notes/index.md", "Overview", handle.read() + "\n"))
        except (OSError, UnicodeDecodeError) as error:
            print(f"Warning: Failed to read notes index {index_path}: {error}")
    if pages:
        hub_content = ["# Architecture & Design Notes", ""]
        for doc_path, label, _ in pages:
            if doc_path == "notes/index.md":
                continue
            hub_content.append(f"- [{label}]({os.path.basename(doc_path)})")
        if not any(doc_path == "notes/index.md" for doc_path, _, _ in pages):
            pages.append(("notes/index.md", "Overview", "\n".join(hub_content) + "\n"))
    return pages
>>>>>>> fix/independent-review-findings
||||||| 07086322
    return hook_repo_root
=======
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
>>>>>>> tmp155


<<<<<<< HEAD
def display_name(stem: str) -> str:
    """Derive a navigation label from a source module or package name.
||||||| 07086322
def _get_notes_dir(config: Union[MkDocsConfig, MutableMapping[str, Any], Any]) -> Optional[str]:
    """Resolve the notes directory from configuration if present.
=======
def _get_notes_dir(config: Any) -> Optional[str]:
    """Resolve the notes directory from configuration.
>>>>>>> tmp155

    Args:
<<<<<<< HEAD
        stem: Python identifier.
||||||| 07086322
        config (Union[MkDocsConfig, MutableMapping[str, Any], Any]): The MkDocs configuration object or dictionary.
=======
        config: The documentation configuration object or dictionary.
>>>>>>> tmp155

    Returns:
<<<<<<< HEAD
        Readable source-derived label.
||||||| 07086322
        Optional[str]: Absolute path to the notes directory if it exists, None otherwise.
=======
        Absolute path to the notes directory, or None when it does not exist.
>>>>>>> tmp155
    """
<<<<<<< HEAD
    return stem.replace("_", " ").title()
||||||| 07086322
    custom_notes = (
        config.get("notes_dir") if hasattr(config, "get") else getattr(config, "notes_dir", None)
    )
    if custom_notes and os.path.isdir(custom_notes):
        return os.path.abspath(custom_notes)

    repo_root = _get_repo_root(config)
    notes_dir = os.path.join(repo_root, "notes")
    return notes_dir if os.path.isdir(notes_dir) else None
=======
    custom = (
        config.get("notes_dir") if hasattr(config, "get") else getattr(config, "notes_dir", None)
    )
    if custom and os.path.isdir(custom):
        return os.path.abspath(custom)

    notes_dir = os.path.join(_get_repo_root(config), "notes")
    return notes_dir if os.path.isdir(notes_dir) else None
>>>>>>> tmp155


<<<<<<< HEAD
def pages_for(root: Path = ROOT) -> list[tuple[str, str]]:
    """Create API and homepage content from package source and its docstrings.
||||||| 07086322
def on_config(
    config: Union[MkDocsConfig, MutableMapping[str, Any]],
) -> Union[MkDocsConfig, MutableMapping[str, Any]]:
    """Inspect notes directory and dynamically populate the Notes navigation section.
=======
def _module_pages(repo_root: str) -> List[Page]:
    """Build one page per Python module found under the source roots.

    A package directory yields an ``index.md`` for its ``__init__.py``; every other module
    yields a page named after it. The dotted path is what ``mkdocstrings`` resolves, so it
    is derived from the directory layout rather than declared anywhere.
>>>>>>> tmp155

    Args:
<<<<<<< HEAD
        root: Source repository to document.
||||||| 07086322
        config (Union[MkDocsConfig, MutableMapping[str, Any]]): The MkDocs configuration object.
=======
        repo_root: Absolute path to the repository root.
>>>>>>> tmp155

    Returns:
<<<<<<< HEAD
        Virtual Markdown paths and generated content with no static page inputs.

    Raises:
        SyntaxError: A Python module cannot be parsed.
        ValueError: No importable Python source or colliding page paths are found.
||||||| 07086322
        Union[MkDocsConfig, MutableMapping[str, Any]]: The updated MkDocs configuration object with notes navigation.
=======
        List of (doc_path, nav_label, markdown_body) triples, sorted by doc_path.
>>>>>>> tmp155
    """
<<<<<<< HEAD
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
||||||| 07086322
    # Finding 5: If nav is not configured in mkdocs.yml (nav is None), preserve auto-navigation
    nav = config.get("nav") if hasattr(config, "get") else getattr(config, "nav", None)
    if nav is None:
        return config
=======
    pages: List[Page] = []
    for source_dir, doc_root in SOURCE_ROOTS:
        base = os.path.join(repo_root, source_dir)
        if not os.path.isdir(base):
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = sorted(d for d in dirnames if d != "__pycache__")
            rel_dir = os.path.relpath(dirpath, base)
            parts: List[str] = [] if rel_dir == os.curdir else rel_dir.split(os.sep)
            doc_parts = [doc_root] + parts
>>>>>>> tmp155

<<<<<<< HEAD
||||||| 07086322
    notes_dir = _get_notes_dir(config)
    if not notes_dir:
        # Clean up empty Notes placeholder if notes directory does not exist
        if isinstance(config.get("nav"), list):
            config["nav"] = [
                item
                for item in config["nav"]
                if not (isinstance(item, dict) and "Notes" in item and not item["Notes"])
            ]
        return config
=======
            if "__init__.py" in filenames:
                dotted = ".".join(doc_parts)
                doc_path = "/".join(doc_parts + ["index.md"])
                label = f"{parts[-1] if parts else doc_root} package ({dotted})"
                title = (parts[-1] if parts else doc_root).capitalize()
                pages.append((doc_path, label, f"# {title}\n\n::: {dotted}\n"))
>>>>>>> tmp155

<<<<<<< HEAD
def navigation(pages: list[tuple[str, str]]) -> list[dict[str, Any]]:
    """Generate hierarchical navigation from the emitted module paths.
||||||| 07086322
    try:
        dir_entries = sorted(os.listdir(notes_dir))
    except OSError as e:
        print(f"Warning: Failed to list notes directory {notes_dir}: {e}")
        dir_entries = []
=======
            for name in sorted(filenames):
                if not name.endswith(".py") or name == "__init__.py":
                    continue
                dotted = ".".join(doc_parts + [name[:-3]])
                doc_path = "/".join(doc_parts + [name[:-3] + ".md"])
                label = f"{name[:-3]} ({dotted})"
                pages.append((doc_path, label, f"# {name[:-3].capitalize()}\n\n::: {dotted}\n"))
    return sorted(pages, key=lambda page: page[0])
>>>>>>> tmp155

<<<<<<< HEAD
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
||||||| 07086322
    note_files = [
        f
        for f in dir_entries
        if f.endswith(".md") and f != "index.md" and os.path.isfile(os.path.join(notes_dir, f))
    ]
    notes_index_path = os.path.join(notes_dir, "index.md")
    has_notes = bool(note_files or os.path.isfile(notes_index_path))

    if not has_notes:
        if isinstance(config.get("nav"), list):
            config["nav"] = [
                item
                for item in config["nav"]
                if not (isinstance(item, dict) and "Notes" in item and not item["Notes"])
            ]
        return config

    notes_section: Optional[List[Any]] = None
    for item in config["nav"]:
        if isinstance(item, dict) and "Notes" in item:
            if item["Notes"] is None:
                item["Notes"] = []
            elif not isinstance(item["Notes"], list):
                item["Notes"] = [item["Notes"]]
            notes_section = item["Notes"]
            break

    if notes_section is None:
        notes_section = []
        config["nav"].append({"Notes": notes_section})

    def _is_present(target_path: str) -> bool:
        for entry in notes_section:
            if entry == target_path:
                return True
            if isinstance(entry, dict) and target_path in entry.values():
                return True
        return False

    if not _is_present("notes/index.md"):
        notes_section.insert(0, "notes/index.md")

    for f in note_files:
        note_uri = f"notes/{f}"
        if not _is_present(note_uri):
            notes_section.append(note_uri)

=======

def _note_pages(notes_dir: Optional[str]) -> List[Page]:
    """Build one page per Markdown file in the notes directory.

    Args:
        notes_dir: Absolute path to the notes directory, or None when absent.

    Returns:
        List of (doc_path, nav_label, markdown_body) triples.
    """
    if not notes_dir or not os.path.isdir(notes_dir):
        return []

    pages: List[Page] = []
    for name in sorted(os.listdir(notes_dir)):
        if not name.endswith(".md") or name == "index.md":
            continue
        path = os.path.join(notes_dir, name)
        if not os.path.isfile(path):
            continue
        try:
            with open(path, "r", encoding="utf-8") as handle:
                content = handle.read()
        except (OSError, UnicodeDecodeError) as error:
            print(f"Warning: Failed to read note {path}: {error}")
            continue
        title = os.path.splitext(name)[0].replace("_", " ").title()
        pages.append((f"notes/{name}", title, content))

    index_path = os.path.join(notes_dir, "index.md")
    if os.path.isfile(index_path):
        try:
            with open(index_path, "r", encoding="utf-8") as handle:
                # A stored hub is published as authored. It gains a trailing newline it did not
                # have, which is harmless for Markdown and is what the test suite pins.
                pages.append(("notes/index.md", "Overview", handle.read() + "\n"))
        except (OSError, UnicodeDecodeError) as error:
            print(f"Warning: Failed to read notes index {index_path}: {error}")
    if pages:
        hub_content = ["# Architecture & Design Notes", ""]
        for doc_path, label, _ in pages:
            if doc_path == "notes/index.md":
                continue
            hub_content.append(f"- [{label}]({os.path.basename(doc_path)})")
        if not any(doc_path == "notes/index.md" for doc_path, _, _ in pages):
            pages.append(("notes/index.md", "Overview", "\n".join(hub_content) + "\n"))
    return pages


def _overview_page(repo_root: str, note_pages: List[Page]) -> Page:
    """Build the site overview from the README, with links to the notes appended.

    Args:
        repo_root: Absolute path to the repository root.
        note_pages: The generated note pages, linked from the overview.

    Returns:
        The (doc_path, nav_label, markdown_body) triple for the overview.
    """
    readme_path = os.path.join(repo_root, "README.md")
    body = ""
    if os.path.isfile(readme_path):
        try:
            with open(readme_path, "r", encoding="utf-8") as handle:
                body = handle.read()
        except (OSError, UnicodeDecodeError) as error:
            print(f"Warning: Failed to read README {readme_path}: {error}")
    if not body:
        body = "# ChessWithQuests\n"

    body += "\n---\n\n## Reference Architecture Diagram\n"
    body += (
        "- [Architecture Diagram](https://app.diagrams.net/#G19OY7iySOQWRAZDFKy1r-7tJKG_L-_Qn8"
        "#%7B%22pageId%22%3A%22C5RBs43oDa-KdzZeNtuy%22%7D)\n"
    )
    if note_pages:
        body += "\n## Architecture & Reference Notes\n"
        body += "- [Notes Overview](notes/index.md)\n"
        for doc_path, label, _ in note_pages:
            if doc_path == "notes/index.md":
                continue
            body += f"- [{label}]({doc_path})\n"
    return ("index.md", "Overview", body)


def _nest(pages: List[Page]) -> Dict[str, Any]:
    """Group pages into a directory tree keyed by path segment.

    A segment maps to a page path when it is a leaf and to a nested dictionary otherwise,
    so ``model/game/board.md`` becomes ``{"model": {"game": {"board.md": ...}}}``.

    Args:
        pages: The generated pages.

    Returns:
        Nested dictionary mirroring the documentation directory layout.
    """
    tree: Dict[str, Any] = {}
    for doc_path, label, _ in pages:
        segments = doc_path[: -len(".md")].split("/")
        node = tree
        for segment in segments[:-1]:
            child = node.setdefault(segment, {})
            if not isinstance(child, dict):
                child = {}
                node[segment] = child
            node = child
        node[segments[-1]] = (doc_path, label)
    return tree


def _order_key(item: Tuple[str, Any]) -> Tuple[int, str]:
    """Sort a navigation segment so package overviews precede their modules.

    Args:
        item: The (segment, value) pair being sorted.

    Returns:
        A sort key placing ``index`` first and everything else alphabetically.
    """
    return (0 if item[0] == "index" else 1, item[0])


def _render(node: Dict[str, Any], labels: Optional[Dict[str, str]] = None) -> List[Any]:
    """Render a nested page tree as a properdocs navigation.

    Args:
        node: The nested page tree for one section.
        labels: Optional segment-to-label overrides, used for the top-level sections.

    Returns:
        A navigation fragment.
    """
    rendered: List[Any] = []
    for segment, value in sorted(node.items(), key=_order_key):
        label = (labels or {}).get(segment, segment)
        if isinstance(value, dict):
            rendered.append({label: _render(value)})
        else:
            doc_path, entry_label = value
            rendered.append({entry_label: doc_path})
    return rendered


def build_nav(config: Any) -> Tuple[List[Any], List[Page]]:
    """Build the complete navigation and the pages it refers to.

    Args:
        config: The documentation configuration object or dictionary.

    Returns:
        A (navigation, pages) pair. Every page in ``pages`` has exactly one navigation
        entry and every navigation entry has exactly one page.
    """
    repo_root = _get_repo_root(config)
    module_pages = _module_pages(repo_root)
    note_pages = _note_pages(_get_notes_dir(config))
    overview = _overview_page(repo_root, note_pages)

    nav: List[Any] = [{"Overview": overview[0]}]

    per_root: Dict[str, List[Page]] = {}
    for doc_path, label, body in module_pages:
        per_root.setdefault(doc_path.split("/")[0], []).append((doc_path, label, body))
    for _, doc_root in SOURCE_ROOTS:
        pages = per_root.get(doc_root)
        if pages:
            nav.append({SECTION_LABELS[doc_root]: _render(_nest(pages))})

    if note_pages:
        nav.append({"Notes": _render(_nest(note_pages))})

    return nav, [overview] + module_pages + note_pages


def on_config(config: Any) -> Any:
    """Replace the configured navigation with one generated from the repository layout.

    Args:
        config: The documentation configuration object or dictionary.

    Returns:
        The configuration, with ``nav`` set to the generated navigation.
    """
    nav, _ = build_nav(config)
    config["nav"] = nav
>>>>>>> tmp155
    return config


<<<<<<< HEAD
def on_files(files: Files, config: Any) -> Files:
    """Supply virtual source API pages, theme assets and live architecture SVGs.
||||||| 07086322
def on_files(files: Files, config: Union[MkDocsConfig, MutableMapping[str, Any]]) -> Files:
    """Dynamically generate virtual markdown documentation pages for Python modules and notes.
=======
def on_files(files: Files, config: Any) -> Files:
    """Emit every documentation page as a virtual file.
>>>>>>> tmp155

    Args:
<<<<<<< HEAD
        files: Files collected by MkDocs.
        config: Resolved MkDocs configuration.
||||||| 07086322
        files (Files): The MkDocs collection of File objects.
        config (Union[MkDocsConfig, MutableMapping[str, Any]]): The MkDocs configuration object.
=======
        files: The collection of files properdocs discovered in ``docs_dir``.
        config: The documentation configuration object or dictionary.
>>>>>>> tmp155

    Returns:
<<<<<<< HEAD
        File collection containing only generated documentation pages and assets.
||||||| 07086322
        Files: The updated collection of File objects including virtual documentation.
=======
        The collection of files including every generated page.
>>>>>>> tmp155
    """
<<<<<<< HEAD
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
||||||| 07086322
    plugins = getattr(config, "plugins", None)
    if plugins is not None and not hasattr(plugins, "_current_plugin"):
        try:
            plugins._current_plugin = None
        except AttributeError:
            pass

    repo_root = _get_repo_root(config)
    src_dir = (
        config.get("docs_dir") if hasattr(config, "get") else getattr(config, "docs_dir", None)
    )
    if not src_dir:
        src_dir = os.path.join(repo_root, "src")

    notes_dir = _get_notes_dir(config)

    note_entries: List[Tuple[str, str]] = []
    if notes_dir and os.path.isdir(notes_dir):
        try:
            dir_entries = sorted(os.listdir(notes_dir))
        except OSError as e:
            print(f"Warning: Failed to list notes directory {notes_dir}: {e}")
            dir_entries = []

        for f in dir_entries:
            if f.endswith(".md") and f != "index.md":
                note_path = os.path.join(notes_dir, f)
                if os.path.isfile(note_path):
                    try:
                        with open(note_path, "r", encoding="utf-8") as nf:
                            content = nf.read()
                    except (OSError, UnicodeDecodeError) as e:
                        print(f"Warning: Failed to read note {note_path}: {e}")
                        continue

                    title = os.path.splitext(f)[0].replace("_", " ").title()
                    note_entries.append((f, title))

                    doc_uri = f"notes/{f}"
                    if not files.get_file_from_path(doc_uri):
                        gen_file = File.generated(
                            config,
                            doc_uri,
                            content=content,
                        )
                        files.append(gen_file)

    # Dynamically generate virtual notes/index.md hub page if notes directory exists and has notes or index.md
    if notes_dir and os.path.isdir(notes_dir):
        notes_index_path = os.path.join(notes_dir, "index.md")
        has_index_on_disk = os.path.isfile(notes_index_path)
        if note_entries or has_index_on_disk:
            if not files.get_file_from_path("notes/index.md"):
                notes_hub_content = None
                if has_index_on_disk:
                    try:
                        with open(notes_index_path, "r", encoding="utf-8") as f:
                            notes_hub_content = f.read()
                    except (OSError, UnicodeDecodeError) as e:
                        print(f"Warning: Failed to read notes index {notes_index_path}: {e}")

                if notes_hub_content is None:
                    hub_lines = [
                        "# Architecture & Design Notes",
                        "",
                        "Authoritative architectural references, design decisions, and baseline rules for the ChessWithQuests project.",
                        "",
                        "## Table of Contents",
                        "",
                    ]
                    for f, title in note_entries:
                        hub_lines.append(f"- [{title}]({f})")
                    hub_lines.append("")
                    notes_hub_content = "\n".join(hub_lines)

                notes_index_file = File.generated(
                    config,
                    "notes/index.md",
                    content=notes_hub_content,
                )
                files.append(notes_index_file)

    # Generate virtual index.md overview from README.md if no index.md on disk
    if not files.get_file_from_path("index.md"):
        readme_path = os.path.join(repo_root, "README.md")
        overview_content = ""
        if os.path.isfile(readme_path):
            try:
                with open(readme_path, "r", encoding="utf-8") as rf:
                    overview_content = rf.read()
            except (OSError, UnicodeDecodeError) as e:
                print(f"Warning: Failed to read README {readme_path}: {e}")
                overview_content = "# ChessWithQuests\n\nAutogenerated API Documentation.\n"
        else:
            overview_content = "# ChessWithQuests\n\nAutogenerated API Documentation.\n"

        overview_content += "\n\n---\n\n## Reference Architecture Diagram\n- [Architecture Diagram](https://app.diagrams.net/#G19OY7iySOQWRAZDFKy1r-7tJKG_L-_Qn8#%7B%22pageId%22%3A%22C5RBs43oDa-KdzZeNtuy%22%7D)\n"

        if (
            notes_dir
            and os.path.isdir(notes_dir)
            and (note_entries or os.path.isfile(os.path.join(notes_dir, "index.md")))
        ):
            overview_content += (
                "\n\n---\n\n## Architecture & Reference Notes\n- [Notes Overview](notes/index.md)\n"
            )
            for f, title in note_entries:
                overview_content += f"- [{title}](notes/{f})\n"

        index_file = File.generated(
            config,
            "index.md",
            content=overview_content,
        )
        files.append(index_file)

    if os.path.isdir(src_dir):
        for root, _, filenames in os.walk(src_dir):
            for f in sorted(filenames):
                if not f.endswith(".py"):
                    continue

                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, src_dir)
                parts = rel_path.split(os.sep)
                parts[-1] = os.path.splitext(parts[-1])[0]

                if parts[-1] == "__init__":
                    if len(parts) == 1:
                        # Root package overview is covered by docs/index.md
                        continue
                    dotted_path = ".".join(parts[:-1])
                    doc_uri = "/".join(parts[:-1]) + "/index.md"
                    title = f"{parts[-2].capitalize()} Package (`{dotted_path}`)"
                else:
                    dotted_path = ".".join(parts)
                    doc_uri = "/".join(parts) + ".md"
                    title = f"{parts[-1].capitalize()} (`{dotted_path}`)"

                # Avoid collisions with static docs if already present
                if files.get_file_from_path(doc_uri):
                    continue

                content = f"# {title}\n\n::: {dotted_path}\n"
                gen_file = File.generated(
                    config,
                    doc_uri,
                    content=content,
                )
                files.append(gen_file)

=======
    plugins = getattr(config, "plugins", None)
    if plugins is not None and not hasattr(plugins, "_current_plugin"):
        # `File.generated` stamps the file with the plugin that produced it. A bare
        # configuration object built outside a plugin run has no such attribute.
        plugins._current_plugin = None

    _, pages = build_nav(config)
    for doc_path, _, body in pages:
        if files.get_file_from_path(doc_path) is None:
            files.append(File.generated(config, doc_path, content=body))
>>>>>>> tmp155
    return files
<<<<<<< HEAD
||||||| 07086322


def on_post_build(config: Union[MkDocsConfig, MutableMapping[str, Any]]) -> None:
    """Ensure site/index.html is available.

    Args:
        config (Union[MkDocsConfig, MutableMapping[str, Any]]): The MkDocs configuration object.

    Returns:
        None
    """
    site_dir = (
        config.get("site_dir") if hasattr(config, "get") else getattr(config, "site_dir", None)
    )
    if not site_dir:
        site_dir = os.path.join(_get_repo_root(config), "site")

    index_html = os.path.join(site_dir, "index.html")
    if not os.path.exists(index_html):
        for candidate in ["index.html", "__init__/index.html", "src/index.html"]:
            src = os.path.join(site_dir, candidate)
            if os.path.exists(src):
                shutil.copyfile(src, index_html)
                print(f"Generated site/index.html from {candidate}")
                break
=======


def on_post_build(config: Any) -> None:
    """Ensure the site root holds an ``index.html``.

    Args:
        config: The documentation configuration object or dictionary.

    Returns:
        None
    """
    site_dir = (
        config.get("site_dir") if hasattr(config, "get") else getattr(config, "site_dir", None)
    ) or os.path.join(_get_repo_root(config), "site")

    index_html = os.path.join(site_dir, "index.html")
    if not os.path.exists(index_html):
        for candidate in ("index.html", "__init__/index.html"):
            source = os.path.join(site_dir, candidate)
            if os.path.exists(source):
                shutil.copyfile(source, index_html)
                print(f"Generated site/index.html from {candidate}")
                break
>>>>>>> tmp155
