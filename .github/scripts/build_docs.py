"""Single authoritative repository documentation build and ProperDocs hooks.

The repository declares configuration in repo.dfconfig; Git supplies the tracked
file inventory. Site navigation, code documentation, generated diagrams and the
deployment selector manifest are projections of those two sources.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[2]


def load_builder_module(filename: str) -> Any:
    """Load the specialized generator from its actual checked-out file path."""
    from importlib.util import module_from_spec, spec_from_file_location

    source = Path(__file__).resolve().with_name(filename)
    key = "_documentation_" + source.stem
    if key in sys.modules:
        return sys.modules[key]
    spec = spec_from_file_location(key, source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load generator at {source}")
    module = module_from_spec(spec)
    sys.modules[key] = module
    spec.loader.exec_module(module)
    return module


def diagram_generator() -> Any:
    return load_builder_module("generate_diagrams.py")


def tracked_files(root: Path = ROOT) -> list[Path]:
    """Discover every tracked file and symlink through the Git index."""
    # A Git submodule is a gitlink in the index but a directory in a working tree.
    # Document its pinned source through .gitmodules; never attempt read_bytes() on it.
    return [path for path in diagram_generator().tracked_paths(root) if not path.is_dir()]


def public_path(path: Path) -> str:
    """Publish hidden tracked directories under ordinary URL-safe names."""
    return "/".join(part.lstrip(".") if part.startswith(".") else part for part in path.parts)


def diagram_viewer_markup(content: str) -> str:
    """Render a readable, pan-and-zoom-capable diagram without duplicating source views."""
    return (
        '<div class="diagram-viewer" data-diagram-viewer>'
        '<div class="diagram-viewer__viewport" tabindex="0" role="region"'
        ' aria-label="Diagram: drag to pan, scroll to zoom">'
        '<div class="diagram-viewer__canvas">' + content + "</div></div></div>"
    )


def pages_for(root: Path = ROOT) -> list[tuple[str, str, str]]:
    """Mirror every tracked repository file as one page, irrespective of language.

    Each tuple is (original Git path, generated documentation path, page body).
    Markdown links follow the generated pages for tracked targets; all other files get code, text,
    or binary metadata pages. Only Git's tracked-file inventory determines scope.
    """
    import hashlib

    paths = tracked_files(root)
    markdown_urls = {
        public_path(p.relative_to(root))
        for p in paths
        if p.suffix.lower() == ".md" and p.name.lower() != "readme.md"
    }
    # Source pages live under a collision-free URL namespace, keeping original
    # binary assets at their native URLs. The source tree/nav still uses Git paths.
    namespace = "repository-files"
    source_prefixes = {public_path(path.relative_to(root)).split("/", 1)[0] for path in paths}
    while namespace in source_prefixes:
        namespace = "_" + namespace
    pages: list[tuple[str, str, str]] = []
    used: set[str] = set()
    for path in paths:
        rel = path.relative_to(root)
        name = rel.as_posix()
        markdown = path.suffix.lower() == ".md"
        if markdown:
            if path.name.lower() == "readme.md":
                dest = public_path(rel.parent / "index.md") if len(rel.parts) > 1 else "index.md"
            else:
                dest = public_path(rel)
        else:
            dest = namespace + "/" + public_path(rel) + ".md"
            while dest in markdown_urls or dest in used:
                dest = dest[:-3] + ".source.md"
        if dest in used:
            raise ValueError(f"Two tracked files resolve to one page: {name} -> {dest}")
        used.add(dest)
        raw = path.read_bytes()
        try:
            decoded = raw.decode("utf-8")
        except UnicodeDecodeError:
            decoded = None
        if markdown and decoded is not None and len(raw) <= 256_000:
            body = decoded
        else:
            digest = hashlib.sha256(raw).hexdigest()
            header = f"# {rel.name}\n\nRepository path: `{name}`  \nSize: {len(raw)} bytes  \nSHA-256: `{digest}`\n\n"
            if decoded is None or len(raw) > 256_000:
                # Include the file in navigation without producing megabytes of HTML.
                # Link to its exact Git revision for full-byte inspection.
                from urllib.parse import quote

                import yaml

                config = yaml.safe_load((root / "properdocs.yml").read_text(encoding="utf-8"))
                repository_url = (config.get("repo_url") or "").rstrip("/")
                revision = subprocess.run(
                    ["git", "-C", str(root), "rev-parse", "HEAD"],
                    check=True,
                    capture_output=True,
                    text=True,
                ).stdout.strip()
                if repository_url.startswith("https://"):
                    url = f"{repository_url}/blob/{revision}/{quote(name, safe=chr(47))}"
                    body = header + f"[View complete file at this commit]({url})\n"
                else:
                    body = header + "Original bytes are retained in the Git repository.\n"
            else:
                import re

                blocks = re.findall(r"`+", decoded)
                fence = "`" * max(4, 1 + max((len(t) for t in blocks), default=0))
                lang = rel.suffix.lstrip(".")
                body = header + f"{fence}{lang}\n{decoded}\n{fence}\n"
        # A source-diagram page is a diagram viewer, never a fenced source dump.
        # The original file remains separately available at its published URL.
        if decoded is not None and rel.suffix.lower() in {".mmd", ".svg"}:
            from html import escape
            from posixpath import relpath

            title = escape(name, quote=False)
            if rel.suffix.lower() == ".mmd":
                graphic = '<pre class="mermaid">' + escape(decoded, quote=False) + "</pre>"
            else:
                # A committed SVG in images/ is an image, not editable diagram
                # source. Render the original bytes with the same pan/zoom UI.
                original_url = relpath(public_path(rel), start=dest.removesuffix(".md"))
                graphic = (
                    f'<img src="{escape(original_url, quote=True)}" '
                    f'alt="{escape(rel.stem.replace("_", " "), quote=True)}" '
                    'loading="lazy" draggable="false">'
                )
            body = f"# {title}\n\n" + diagram_viewer_markup(graphic) + "\n"
        pages.append((name, dest, body))
    # Rebase tracked Markdown links to the generated page corresponding to
    # their target file. This includes non-Markdown source files, which live
    # under the dynamically chosen repository-files namespace, and README
    # symlinks whose contents originate in another source directory.
    import posixpath
    import re
    from urllib.parse import unquote, urlsplit

    destinations = {source: dest for source, dest, _ in pages}
    anchor = re.compile(r"(?<!!)(\[[^\]\n]+\]\()([^\s)]+)(\))")
    linked_pages: list[tuple[str, str, str]] = []
    for source, dest, body in pages:
        if not source.lower().endswith(".md"):
            linked_pages.append((source, dest, body))
            continue
        actual = (root / source).resolve()
        if not actual.is_relative_to(root.resolve()):
            raise ValueError(f"Tracked Markdown symlink escapes repository: {source}")
        source_dir = actual.relative_to(root.resolve()).parent

        def link(match: re.Match[str]) -> str:
            original = match.group(2)
            parsed = urlsplit(original)
            if parsed.scheme or parsed.netloc or not parsed.path or original.startswith("#"):
                return match.group(0)
            target = (root / source_dir / unquote(parsed.path)).resolve()
            if not target.is_relative_to(root.resolve()):
                return match.group(0)
            other = destinations.get(target.relative_to(root.resolve()).as_posix())
            if not other:
                return match.group(0)
            relative = posixpath.relpath(other, start=posixpath.dirname(dest) or ".")
            suffix = ("?" + parsed.query if parsed.query else "") + (
                "#" + parsed.fragment if parsed.fragment else ""
            )
            return match.group(1) + relative + suffix + match.group(3)

        linked_pages.append((source, dest, anchor.sub(link, body)))
    # Generated AST and implementation UML are derived from this commit's
    # *actual* Git-tracked code. Never retain stale Mermaid snapshot blobs:
    # dynamically publish navigable viewers plus raw .mmd assets.
    from html import escape

    for source_path, diagram in sorted(diagram_generator().generated_assets(root).items()):
        original = "." + source_path if source_path.startswith("agents/") else source_path
        if original in destinations:
            raise ValueError(
                f"Generated diagram must not also be a committed authority: {original}"
            )
        dest = namespace + "/" + public_path(Path(original)) + ".md"
        if dest in used:
            raise ValueError(f"Generated diagram page collision: {dest}")
        used.add(dest)
        graphic = '<pre class="mermaid">' + escape(diagram, quote=False) + "</pre>"
        viewer = f"# {escape(original, quote=False)}\\n\\n" + diagram_viewer_markup(graphic) + "\\n"
        linked_pages.append((original, dest, viewer))
    return linked_pages


def navigation(pages: list[tuple[str, str, str]]) -> list[dict[str, Any]]:
    """Use original Git paths for both navigation and the generated file tree."""
    folders: dict[str, Any] = {}
    for original, target, _ in pages:
        parts = Path(original).parts
        cursor = folders
        for dirname in parts[:-1]:
            cursor = cursor.setdefault(dirname, {})
        filename = parts[-1]
        if filename in cursor:
            raise ValueError(f"Navigation collision at {original}")
        cursor[filename] = target

    def entries(node: dict[str, Any]) -> list[dict[str, Any]]:
        return [
            {name: entries(value) if isinstance(value, dict) else value}
            for name, value in sorted(node.items(), key=lambda item: item[0])
        ]

    return entries(folders)


def build_nav(root: Path = ROOT) -> tuple[list[dict[str, Any]], list[tuple[str, str, str]]]:
    """Build one navigation entry for every tracked file page."""
    pages = pages_for(root)
    return navigation(pages), pages


def on_config(config: Any) -> Any:
    """Populate navigation from repository content before rendering."""
    config["nav"] = build_nav()[0]
    return config


def on_files(files: Any, config: Any) -> Any:
    """Materialize virtual pages without writing documentation sources to disk."""
    from properdocs.structure.files import File

    plugins = getattr(config, "plugins", None)
    if plugins is not None and not hasattr(plugins, "_current_plugin"):
        plugins._current_plugin = None
    for _, dest, body in build_nav()[1]:
        if files.get_file_from_path(dest) is None:
            files.append(File.generated(config, dest, content=body))
    # All source files and syntax nodes are discovered by the parser, not a
    # curated list of repository packages or language-specific templates.
    import sys

    scripts = str(Path(__file__).resolve().parent)
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    grammar = diagram_generator()

    for dest, source in grammar.generated_assets(ROOT).items():
        current = files.get_file_from_path(dest)
        if current is not None:
            files.remove(current)
        files.append(File.generated(config, dest, content=source))
    # Preserve every tracked SVG at its source-derived publication path.
    # Their existence is discovered, never hard-coded by directory or filename.
    for path in grammar.tracked_paths(ROOT):
        if path.suffix.lower() != ".svg":
            continue
        dest = public_path(path.relative_to(ROOT))
        current = files.get_file_from_path(dest)
        if current is not None:
            files.remove(current)
        files.append(File.generated(config, dest, content=path.read_text(encoding="utf-8")))
    return files


def project_registry(repository: Path) -> list[dict[str, str]]:
    """Return and validate the documentation projects declared in repo.dfconfig."""
    config = json.loads((repository / "repo.dfconfig").read_text(encoding="utf-8"))
    repo = config.get("repo", {})
    if not isinstance(repo, dict):
        raise ValueError("repo.dfconfig requires a 'repo' object")
    docs = repo.get("documentation") or {}
    if not isinstance(docs, dict):
        raise ValueError("repo.documentation must be an object")
    declared = docs.get("projects", [])
    if not isinstance(declared, list):
        raise ValueError("repo.documentation.projects must be a list")

    projects: list[dict[str, str]] = []
    names: set[str] = set()
    urls: set[str] = set()
    for index, entry in enumerate(declared):
        if not isinstance(entry, dict):
            raise ValueError(f"Project {index} must be an object")
        name, url = entry.get("name"), entry.get("url")
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"Project {index} requires a nonempty name")
        if not isinstance(url, str):
            raise ValueError(f"Project {index} requires an HTTPS URL")
        parsed = urlsplit(url)
        if (
            parsed.scheme != "https"
            or not parsed.netloc
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError(f"Project {index} requires an absolute public HTTPS URL")
        canonical_name = name.strip()
        canonical_url = url.rstrip("/") + "/"
        if canonical_name in names or canonical_url in urls:
            raise ValueError(f"Duplicate documentation project: {canonical_name}")
        names.add(canonical_name)
        urls.add(canonical_url)
        projects.append({"name": canonical_name, "url": canonical_url})
    return projects


def manifest(site: Path, repository: Path) -> dict[str, list[dict[str, str]]]:
    """Describe only sites whose root HTML is present in the deployment artifact."""
    if not (site / "index.html").is_file():
        raise ValueError(f"Documentation site is missing {site / 'index.html'}")

    config = json.loads((repository / "repo.dfconfig").read_text(encoding="utf-8"))
    identity = config.get("repo", {}).get("identity", {})
    default_branch = identity.get("default_branch") if isinstance(identity, dict) else None
    if not isinstance(default_branch, str) or not default_branch:
        default_branch = "repository root"
    versions = [{"name": default_branch, "path": ""}]
    branches = site / "branch"
    if branches.is_dir():
        for path in sorted(branches.iterdir()):
            if path.is_dir() and (path / "index.html").is_file():
                versions.append({"name": path.name, "path": f"branch/{path.name}"})
    previews = sorted(
        (
            path
            for path in site.iterdir()
            if path.is_dir()
            and path.name.startswith("pr-")
            and path.name[3:].isdigit()
            and (path / "index.html").is_file()
        ),
        key=lambda path: int(path.name[3:]),
        reverse=True,
    )
    for path in previews:
        versions.append({"name": f"PR #{path.name[3:]}", "path": path.name})
    return {"versions": versions, "projects": project_registry(repository)}


def render_published_mermaid(site: Path) -> None:
    """Pre-render every published Mermaid source to SVG and verify real output.

    Mermaid remains the canonical diagram source. The generated SVGs exist only
    inside the deployment artifact, where our existing SVG pan/zoom viewer can
    display them without relying on a third-party browser CDN or a live parser.
    """
    import hashlib
    import html
    import os
    import re
    from urllib.parse import quote

    pages = []
    for page in site.rglob("index.html"):
        text = page.read_text(encoding="utf-8")
        if '<pre class="mermaid">' in text:
            pages.append((page, text))
    if not pages:
        return

    executable = shutil.which("mmdc")
    if executable is None:
        raise RuntimeError("Documentation build requires the pinned Mermaid CLI (mmdc)")

    assets = site / "assets" / "diagrams"
    assets.mkdir(parents=True, exist_ok=True)
    compiled: dict[str, Path] = {}
    pattern = re.compile(r'<pre class="mermaid">([\s\S]*?)</pre>')
    with tempfile.TemporaryDirectory(prefix="render-mermaid-") as temporary:
        work = Path(temporary)
        config = work / "mermaid.json"
        config.write_text(
            json.dumps(
                {
                    "securityLevel": "strict",
                    "maxTextSize": 1000000,
                    "maxEdges": 10000,
                    "flowchart": {"htmlLabels": False, "useMaxWidth": False},
                }
            ),
            encoding="utf-8",
        )

        browser_options: list[str] = []
        # GitHub's isolated Linux runners do not permit Chromium's sandbox.
        if os.environ.get("GITHUB_ACTIONS") == "true" and sys.platform == "linux":
            browser = work / "puppeteer.json"
            browser.write_text(
                json.dumps({"args": ["--no-sandbox", "--disable-setuid-sandbox"]}),
                encoding="utf-8",
            )
            browser_options = ["--puppeteerConfigFile", str(browser)]

        for page, document in pages:

            def replace_diagram(match: Any) -> str:
                source = html.unescape(match.group(1)).strip() + "\n"
                digest = hashlib.sha256(source.encode("utf-8")).hexdigest()[:20]
                if digest not in compiled:
                    input_file = work / (digest + ".mmd")
                    target = assets / (digest + ".svg")
                    input_file.write_text(source, encoding="utf-8")
                    subprocess.run(
                        [
                            executable,
                            "--input",
                            str(input_file),
                            "--output",
                            str(target),
                            "--configFile",
                            str(config),
                            "--backgroundColor",
                            "transparent",
                            *browser_options,
                        ],
                        check=True,
                        timeout=240,
                        cwd=ROOT,
                    )
                    data = target.read_text(encoding="utf-8")
                    if "<svg" not in data or "</svg>" not in data:
                        raise RuntimeError(f"Mermaid did not produce an SVG: {target}")
                    # Mermaid emits width="100%" without an intrinsic height.
                    # That produces an incorrectly sized image in the viewer.
                    # Use the actual rendered bounds to give both axes real units.
                    opening = re.search(r"<svg\b[^>]*>", data)
                    viewbox = re.search(r'viewBox="([^"]+)"', opening.group(0) if opening else "")
                    if opening is None or viewbox is None:
                        raise RuntimeError(f"Mermaid SVG has no intrinsic bounds: {target}")
                    bounds = viewbox.group(1).split()
                    if len(bounds) != 4 or float(bounds[2]) <= 0 or float(bounds[3]) <= 0:
                        raise RuntimeError(f"Mermaid SVG has invalid bounds: {target}")
                    from math import ceil

                    svg_tag = re.sub(r'\s(?:width|height)="[^"]*"', "", opening.group(0))
                    svg_tag = svg_tag.replace(
                        "<svg",
                        f'<svg width="{ceil(float(bounds[2]))}" height="{ceil(float(bounds[3]))}"',
                        1,
                    )
                    data = data.replace(opening.group(0), svg_tag, 1)
                    target.write_text(data, encoding="utf-8")
                    compiled[digest] = target
                relative = os.path.relpath(compiled[digest], page.parent).replace(os.sep, "/")
                return (
                    '<img src="'
                    + quote(relative, safe="/.-_")
                    + '" alt="Rendered Mermaid architecture diagram" '
                    'loading="lazy" draggable="false">'
                )

            rendered, count = pattern.subn(replace_diagram, document)
            if count < 1:
                raise RuntimeError(f"Expected Mermaid diagram is missing from {page}")
            page.write_text(rendered, encoding="utf-8")


def build() -> None:
    """Build the strict documentation site and validate dynamically generated assets."""
    import yaml

    with tempfile.TemporaryDirectory(prefix="repo-docs-") as temporary:
        work = Path(temporary)
        source = work / "source"
        source.mkdir()
        config = yaml.safe_load((ROOT / "properdocs.yml").read_text(encoding="utf-8"))
        config["docs_dir"] = str(source)
        config["site_dir"] = str(ROOT / "site")
        config["hooks"] = [str((ROOT / hook).resolve()) for hook in config.get("hooks", [])]
        theme = config.get("theme", {})
        if theme.get("custom_dir"):
            theme["custom_dir"] = str((ROOT / theme["custom_dir"]).resolve())
        ephemeral = work / "properdocs.yml"
        ephemeral.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
        subprocess.run(
            [sys.executable, "-m", "properdocs", "build", "--strict", "-f", str(ephemeral)],
            cwd=ROOT,
            check=True,
        )
        # Validate generated source outputs without rerunning the diagram parser.
        diagram_paths = diagram_generator().generated_assets(ROOT)
        for asset in diagram_paths:
            if not (ROOT / "site" / asset).is_file():
                raise RuntimeError(f"Missing generated site asset: {asset}")
    render_published_mermaid(ROOT / "site")
    write_manifest(ROOT / "site")


def write_manifest(site: Path) -> None:
    """Write selector state after all deployable preview/branch builds are staged."""
    data = manifest(site, ROOT)
    (site / "versions.json").write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Build or finalize repository documentation")
    parser.add_argument(
        "--manifest",
        action="store_true",
        help="Only regenerate the selector after staging preview builds",
    )
    parser.add_argument("--site", type=Path, default=ROOT / "site")
    args = parser.parse_args()
    if args.manifest:
        write_manifest(args.site.resolve())
    else:
        build()


if __name__ == "__main__":
    main()
