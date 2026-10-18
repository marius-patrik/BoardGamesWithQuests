"""Generate Mermaid diagrams from the Git-tracked repository and syntax trees."""

from __future__ import annotations

import ast
import hashlib
import html
import subprocess
from collections import defaultdict
from pathlib import Path, PurePosixPath
from typing import Any


def tracked_paths(root: Path) -> list[Path]:
    raw = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z", "--cached"],
        check=True,
        capture_output=True,
    ).stdout
    return sorted(
        (
            root / rawpath.decode("utf-8", "surrogateescape")
            for rawpath in raw.split(b"\0")
            if rawpath
        ),
        key=lambda p: p.relative_to(root).as_posix(),
    )


def _node(text: str) -> str:
    return "n" + hashlib.sha256(text.encode("utf-8")).hexdigest()[:17]


def _label(text: str) -> str:
    """Escape display labels while retaining unambiguous filenames."""
    return (
        html.escape(text.replace("\n", " ").replace("\r", " "), quote=True)
        .replace("#", "#35;")
        .replace(chr(96), "#96;")
    )


def _declarations(path: Path) -> list[tuple[str, str]]:
    """Read syntax structure for any language supported by Tree-sitter."""
    if not path.is_file() or path.is_symlink():
        return []
    from tree_sitter_language_pack import detect_language, get_parser

    language = "json" if path.name.endswith(".dfconfig") else detect_language(str(path))
    if not language:
        return []
    source = path.read_bytes()
    if b"\0" in source:
        return []
    tree = get_parser(language).parse(source)
    nodes: list[tuple[str, str]] = []
    # The global diagram shows structural declarations. The original content
    # of every file is available from its generated documentation page.
    stack: list[tuple[Any, int]] = [(tree.root_node, 0)]
    while stack:
        node, depth = stack.pop()
        kind = node.type
        if depth > 0 and (
            "definition" in kind
            or "declaration" in kind
            or kind in {"class_body", "function_item", "impl_item", "method", "interface"}
        ):
            label = kind
            name = node.child_by_field_name("name")
            if name is not None:
                label += (
                    " "
                    + source[name.start_byte : name.end_byte].decode("utf-8", errors="replace")[
                        :120
                    ]
                )
            nodes.append((kind, label))
        if depth < 5 and len(nodes) < 180:
            stack.extend((child, depth + 1) for child in reversed(node.named_children))
    return nodes


def repository_ast(root: Path) -> str:
    """Mermaid tree of every tracked file and its discovered syntax declarations."""
    lines = ["flowchart LR", '  root["Tracked repository"]']
    directories: set[str] = set()
    for file in tracked_paths(root):
        path = file.relative_to(root).as_posix()
        parts = PurePosixPath(path).parts
        parent = "root"
        prefix: list[str] = []
        for part in parts[:-1]:
            prefix.append(part)
            name = "/".join(prefix)
            ident = _node("dir:" + name)
            if name not in directories:
                lines.append(f'  {ident}["{_label(part)}/"]')
                lines.append(f"  {parent} --> {ident}")
                directories.add(name)
            parent = ident
        fileid = _node("file:" + path)
        lines.append(f'  {fileid}["{_label(parts[-1])}"]')
        lines.append(f"  {parent} --> {fileid}")
        for index, (kind, label) in enumerate(_declarations(file)):
            sym = _node(f"syntax:{path}:{index}:{kind}")
            lines.append(f'  {sym}["{_label(label)}"]')
            lines.append(f"  {fileid} --> {sym}")
    return "\n".join(lines) + "\n"


def implementation_uml(root: Path) -> str:
    """Mermaid class diagram from actual tracked Python classes and inheritance."""
    modules: dict[str, ast.Module] = {}
    for path in tracked_paths(root):
        # Application UML describes production packages, not repository tests or
        # CI helpers. The repository AST still inventories every tracked file.
        if path.relative_to(root).parts[0] != "packages":
            continue
        if path.suffix != ".py" or not path.is_file() or path.is_symlink():
            continue
        relative = path.relative_to(root).with_suffix("")
        name = ".".join(relative.parts)
        modules[name] = ast.parse(path.read_text(encoding="utf-8"))
    classes: dict[str, ast.ClassDef] = {}
    simple: dict[str, list[str]] = defaultdict(list)
    for module, tree in modules.items():
        for item in ast.walk(tree):
            if isinstance(item, ast.ClassDef):
                key = module + "." + item.name
                classes[key] = item
                simple[item.name].append(key)
    lines = ["classDiagram", "direction LR"]
    if not classes:
        return "classDiagram\n  class NoPythonClasses\n"
    keys: dict[str, str] = {}
    for key, cls in sorted(classes.items()):
        ident = _node("class:" + key)
        keys[key] = ident
        lines.append(f'  class {ident}["{_label(cls.name)}"]')
        for item in cls.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                lines.append(f"  {ident} : +{item.name}()")
            elif isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                lines.append(f"  {ident} : +{item.target.id}")
    for key, cls in sorted(classes.items()):
        for base in cls.bases:
            expr = ast.unparse(base)
            if expr in classes:
                parent = expr
            else:
                matches = simple.get(expr.split(".")[-1], [])
                parent = matches[0] if len(matches) == 1 else None
            if parent and parent != key:
                lines.append(f"  {keys[parent]} <|-- {keys[key]}")
    # Associations come exclusively from explicit source-level type hints.
    # Do not infer links from matching spellings or ad-hoc method calls.
    associations: set[tuple[str, str, str]] = set()
    for key, cls in sorted(classes.items()):
        for node in ast.walk(cls):
            if not isinstance(node, ast.AnnAssign) or not isinstance(node.target, ast.Attribute):
                continue
            target = node.target
            if not isinstance(target.value, ast.Name) or target.value.id != "self":
                continue
            annotation_types = {
                item.id for item in ast.walk(node.annotation) if isinstance(item, ast.Name)
            }
            for type_name in sorted(annotation_types):
                matches = simple.get(type_name, [])
                if len(matches) == 1 and matches[0] != key:
                    associations.add((key, matches[0], target.attr))
    for source, target, attribute in sorted(associations):
        lines.append(f"  {keys[source]} --> {keys[target]} : {attribute}")
    return "\n".join(lines) + "\n"


def generated_assets(root: Path) -> dict[str, str]:
    """Return solely Mermaid assets, under the repository diagrams folder."""
    return {
        "agents/architecture/diagrams/ast.mmd": repository_ast(root),
        "agents/architecture/diagrams/uml.mmd": implementation_uml(root),
    }


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2]
    for path, data in generated_assets(root).items():
        target = root / ("." + path if path.startswith("agents/") else path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(data, encoding="utf-8")
        print(path)
