"""Generate connected UML diagrams from the currently tracked Python AST.

Both views are diagrams, not an inventory of file names. Their notation mirrors
the reference diagrams.net class drawing: separate class compartments, parent
triangles, typed associations, and explicit component boundaries.

No class, relationship or component is declared by hand. The only fixed nodes
are the package lanes observed from current source; their
contents are discovered from source files. SVG layout is performed by Graphviz.
"""

from __future__ import annotations

import ast
from collections import defaultdict
from dataclasses import dataclass
from html import escape
from pathlib import Path
import re
import shutil
import subprocess

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib


@dataclass(frozen=True)
class UMLClass:
    """Information extracted from one class definition."""

    module: str
    name: str
    bases: tuple[str, ...]
    attributes: tuple[str, ...]
    methods: tuple[str, ...]

    @property
    def key(self) -> str:
        """Qualified identifier unique among source modules."""
        return f"{self.module}.{self.name}"


@dataclass(frozen=True)
class SourceModule:
    """Tracked Python module and its parsed syntax tree."""

    module: str
    tree: ast.Module
    path: Path


def _tracked_modules(root: Path) -> list[SourceModule]:
    """Collect only Python files tracked in Git, never site-packages or examples."""
    raw = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z", "--", "packages"],
        check=True,
        capture_output=True,
    ).stdout
    modules = []
    for entry in raw.split(b"\0"):
        if not entry:
            continue
        path = root / entry.decode("utf-8")
        if path.suffix != ".py" or not path.is_file():
            continue
        relative = path.relative_to(root / "packages").with_suffix("")
        parts = relative.parts[:-1] if relative.parts[-1] == "__init__" else relative.parts
        name = ".".join(parts)
        modules.append(SourceModule(name, ast.parse(path.read_text(encoding="utf-8")), path))
    return sorted(modules, key=lambda item: item.module)


def _aliases(record: SourceModule) -> dict[str, str]:
    """Resolve imported symbols to their actual package/module paths."""
    aliases = {}
    for node in ast.walk(record.tree):
        if isinstance(node, ast.Import):
            for imported in node.names:
                aliases[imported.asname or imported.name.split(".")[0]] = (
                    imported.name if imported.asname else imported.name.split(".")[0]
                )
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                pieces = record.module.split(".")[:-1]
                parent = pieces[: len(pieces) - node.level + 1]
                base = ".".join([*parent, *(node.module.split(".") if node.module else [])])
            else:
                base = node.module or ""
            for imported in node.names:
                if imported.name == "*":
                    continue
                aliases[imported.asname or imported.name] = (
                    f"{base}.{imported.name}" if base else imported.name
                )
    return aliases


def _class_ref(
    node: ast.AST,
    module: str,
    aliases: dict[str, str],
    known: set[str],
    unambiguous: dict[str, str],
) -> str | None:
    """Resolve a class expression against a qualified class dictionary."""
    if not isinstance(node, (ast.Name, ast.Attribute)):
        return None
    expression = ast.unparse(node)
    first, _, tail = expression.partition(".")
    mapped = aliases.get(first, first)
    expanded = f"{mapped}.{tail}" if tail else mapped
    possible = (expanded, f"{module}.{expression}", expression)
    for name in possible:
        if name in known:
            return name
    return unambiguous.get(expression) if not tail else None


def _annotation_classes(node: ast.AST, candidates: set[str]) -> set[str]:
    """Find candidate class names inside a forward-ref or generic annotation."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return {
            name
            for name in candidates
            if re.search(rf"(?<![\w.]){re.escape(name)}(?!\w)", node.value)
        }
    return {sub.id for sub in ast.walk(node) if isinstance(sub, ast.Name) and sub.id in candidates}


def _members(node: ast.ClassDef) -> tuple[tuple[str, ...], tuple[str, ...], set[str]]:
    """Extract declared fields, self-assigned fields, methods and field type refs."""
    fields: list[str] = []
    methods: list[str] = []
    used_types: set[str] = set()
    for part in node.body:
        if isinstance(part, ast.AnnAssign) and isinstance(part.target, ast.Name):
            fields.append(f"{part.target.id}: {ast.unparse(part.annotation)}")
            used_types.update(_annotation_classes(part.annotation, set()))
        if not isinstance(part, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        # The reference depicts method signatures and instance fields as
        # distinct compartments, so include both from AST rather than prose.
        params = [
            arg.arg
            for arg in [*part.args.posonlyargs, *part.args.args, *part.args.kwonlyargs]
            if arg.arg not in {"self", "cls"}
        ]
        signature = f"{part.name}({', '.join(params[:3])}{', …' if len(params) > 3 else ''})"
        if part.name not in {"__init__"} and not part.name.startswith("__"):
            methods.append(signature)
        if part.name == "__init__":
            for child in ast.walk(part):
                if isinstance(child, ast.AnnAssign) and isinstance(child.target, ast.Attribute):
                    if isinstance(child.target.value, ast.Name) and child.target.value.id == "self":
                        fields.append(f"{child.target.attr}: {ast.unparse(child.annotation)}")
                elif isinstance(child, ast.Assign):
                    for target in child.targets:
                        if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name):
                            if target.value.id == "self":
                                fields.append(target.attr)
    return tuple(dict.fromkeys(fields))[:9], tuple(dict.fromkeys(methods))[:8], used_types


def class_model(root: Path) -> tuple[list[UMLClass], dict[str, set[tuple[str, str]]]]:
    """Extract code-proven inheritance and typed ownership relationships."""
    modules = _tracked_modules(root)
    classes = []
    nodes: list[tuple[SourceModule, ast.ClassDef]] = []
    for record in modules:
        for node in record.tree.body:
            if isinstance(node, ast.ClassDef):
                fields, methods, _ = _members(node)
                classes.append(
                    UMLClass(
                        record.module,
                        node.name,
                        tuple(ast.unparse(base) for base in node.bases),
                        fields,
                        methods,
                    )
                )
                nodes.append((record, node))
    classes.sort(key=lambda cls: cls.key)
    known = {cls.key for cls in classes}
    by_name: dict[str, set[str]] = defaultdict(set)
    for cls in classes:
        by_name[cls.name].add(cls.key)
    unique = {name: next(iter(ids)) for name, ids in by_name.items() if len(ids) == 1}
    edges: dict[str, set[tuple[str, str]]] = {
        "inherits": set(),
        "references": set(),
    }
    for record, node in nodes:
        origin = f"{record.module}.{node.name}"
        aliases = _aliases(record)
        for base in node.bases:
            target = _class_ref(base, record.module, aliases, known, unique)
            if target and target != origin:
                edges["inherits"].add((origin, target))
        for part in node.body:
            annotations = []
            if isinstance(part, ast.AnnAssign):
                annotations.append(part.annotation)
            if (
                isinstance(part, (ast.FunctionDef, ast.AsyncFunctionDef))
                and part.name == "__init__"
            ):
                annotations.extend(arg.annotation for arg in part.args.args if arg.annotation)
                for element in ast.walk(part):
                    if isinstance(element, ast.AnnAssign):
                        annotations.append(element.annotation)
                    # A self.attr = Type(...) constructor is direct evidence
                    # that the object contains a collaborator of this class.
                    if isinstance(element, ast.Assign) and isinstance(element.value, ast.Call):
                        if any(
                            isinstance(t, ast.Attribute)
                            and isinstance(t.value, ast.Name)
                            and t.value.id == "self"
                            for t in element.targets
                        ):
                            target = _class_ref(
                                element.value.func, record.module, aliases, known, unique
                            )
                            if target and target != origin:
                                edges["references"].add((origin, target))
            for annotation in annotations:
                for name in _annotation_classes(annotation, set(by_name)):
                    target = _class_ref(
                        ast.Name(id=name, ctx=ast.Load()), record.module, aliases, known, unique
                    )
                    if target and target != origin:
                        edges["references"].add((origin, target))
    # Do not depict a subclass's base reference twice with unrelated semantics.
    edges["references"] -= edges["inherits"]
    return classes, edges


def _quote(value: str) -> str:
    """Escape a DOT identifier or attribute."""
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


def _html(value: str) -> str:
    """Escape one HTML-like Graphviz label segment."""
    return escape(value, quote=True).replace("…", "...")


def _run_dot(source: str) -> str:
    """Render a validated graph as standalone SVG; never fabricate graph edges."""
    binary = shutil.which("dot")
    if binary is None:
        raise RuntimeError(
            "Graphviz 'dot' is required for generated UML SVGs. "
            "Install graphviz before the strict documentation build."
        )
    process = subprocess.run(
        [binary, "-Tsvg"],
        input=source,
        text=True,
        capture_output=True,
        check=False,
    )
    if process.returncode:
        raise RuntimeError(f"UML rendering failed: {process.stderr[-2800:]}")
    if "<svg " not in process.stdout:
        raise RuntimeError("Graphviz returned no SVG diagram")
    return process.stdout


def _class_label(cls: UMLClass, detailed: bool) -> str:
    """UML table: header, fields and operations, matching reference compartments."""
    heading = _html(cls.name)
    module = _html(cls.module)
    lines = [
        '<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="6" '
        'COLOR="#344054" BGCOLOR="#FFFFFF">',
        f'<TR><TD BGCOLOR="#e5eaf8" ALIGN="CENTER"><B>{heading}</B></TD></TR>',
        f'<TR><TD ALIGN="LEFT"><FONT POINT-SIZE="9" COLOR="#475467">{module}</FONT></TD></TR>',
    ]
    if detailed:
        attrs = cls.attributes[:7] or ("—",)
        operations = cls.methods[:6] or ("—",)
        lines.append('<TR><TD BORDER="1" SIDES="T" ALIGN="LEFT">')
        for entry in attrs:
            lines.append(f'<FONT POINT-SIZE="10">+ {_html(entry[:64])}</FONT><BR ALIGN="LEFT"/>')
        lines.append("</TD></TR>")
        lines.append('<TR><TD BORDER="1" SIDES="T" ALIGN="LEFT">')
        for entry in operations:
            lines.append(f'<FONT POINT-SIZE="10">+ {_html(entry[:64])}</FONT><BR ALIGN="LEFT"/>')
        lines.append("</TD></TR>")
    else:
        lines.append(
            f'<TR><TD ALIGN="LEFT"><FONT POINT-SIZE="9" COLOR="#475467">'
            f"{len(cls.attributes)} fields | {len(cls.methods)} methods</FONT></TD></TR>"
        )
    lines.append("</TABLE>")
    return "".join(lines)


def render_class_diagram(root: Path, detailed: bool = True) -> str:
    """Render a true connected UML class graph extracted from implementation."""
    classes, relationships = class_model(root)
    if not classes:
        raise RuntimeError("Cannot draw the implementation: no tracked Python classes")
    dot = [
        "digraph classes {",
        'graph [rankdir=TB, bgcolor="white", pad="0.38", nodesep="0.40", '
        'ranksep="1.05", splines=polyline, compound=true, outputorder=edgesfirst, '
        'fontname="DejaVu Sans", label="Implemented Object Model (Python AST)", '
        "labelloc=t, labeljust=l, fontsize=24];",
        'node [shape=plain, fontname="DejaVu Sans", margin=0];',
        'edge [color="#667085", penwidth=1.5, arrowsize=0.85, fontname="DejaVu Sans"];',
    ]
    for index, cls in enumerate(classes):
        dot.append(f"  {_quote(cls.key)} [label=<{_class_label(cls, detailed)}>];")
    # Package clusters are derived from actual top-level import roots.
    by_package: dict[str, list[str]] = defaultdict(list)
    for cls in classes:
        by_package[cls.module.split(".")[0]].append(cls.key)
    for index, (package, names) in enumerate(sorted(by_package.items())):
        dot.append(
            f'subgraph cluster_{index} {{ label={_quote("packages/" + package + "/")}; '
            'style="rounded,dashed"; color="#b2bdd0"; bgcolor="#f8faff"; '
            'fontname="DejaVu Sans"; fontsize=17;'
        )
        for name in names:
            dot.append(f"{_quote(name)};")
        dot.append("}")
    for child, parent in sorted(relationships["inherits"]):
        dot.append(
            f"{_quote(child)} -> {_quote(parent)} "
            '[arrowhead=empty, color="#334155", penwidth=2, minlen=2];'
        )
    for owner, owned in sorted(relationships["references"]):
        dot.append(
            f"{_quote(owner)} -> {_quote(owned)} "
            '[style=dashed, arrowhead=vee, color="#64748b", constraint=false];'
        )
    dot.append("}")
    return _run_dot("\n".join(dot))


def render_component_diagram(root: Path) -> str:
    """Render an MVC/package UML component graph from observed import statements."""
    modules = _tracked_modules(root)
    packages = sorted({module.module.split(".")[0] for module in modules})
    components: dict[str, set[str]] = defaultdict(set)
    dependencies: set[tuple[str, str]] = set()
    allowed_dependencies = set(packages)
    allowed_dependencies.update(f"engine.{name}" for name in ("model", "controller", "view", "app"))
    for module in modules:
        parts = module.module.split(".")
        # Group engine internals by first child; other packages by name.
        node = ".".join(parts[:2]) if parts[0] == "engine" and len(parts) > 1 else parts[0]
        components[parts[0]].add(node)
        for alias in _aliases(module).values():
            incoming = alias.split(".")
            if incoming[0] not in packages:
                continue
            other = (
                ".".join(incoming[:2])
                if incoming[0] == "engine" and len(incoming) > 1
                else incoming[0]
            )
            if other != node and other != "engine" and other in allowed_dependencies:
                dependencies.add((node, other))
    # The plugin connection is not an import: the engine discovers games
    # dynamically via project metadata. Draw it only when the distribution
    # actually registers a concrete game package in pyproject.toml.
    project = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    plugins = (
        project.get("project", {}).get("entry-points", {}).get("boardgameswithquests.games", {})
    )
    registrations = {
        value.split(":", 1)[0].split(".", 1)[0]
        for value in plugins.values()
        if isinstance(value, str)
    }
    # The engine __main__ and app belong to the application entrypoint.
    # Every displayed relationship still must come from actual imports.
    dot = [
        "digraph architecture {",
        'graph [rankdir=TB, bgcolor="white", pad="0.45", nodesep="0.8", ranksep="1.2", '
        "splines=polyline, compound=true, outputorder=edgesfirst, "
        'fontname="DejaVu Sans", fontsize=24, label="Implemented MVC + Game Packages", '
        "labelloc=t, labeljust=l];",
        'node [shape=plain, fontname="DejaVu Sans"];',
        'edge [color="#344054", penwidth=1.8, arrowsize=0.9];',
    ]
    for i, package in enumerate(packages):
        dot.append(
            f'subgraph cluster_package_{i} {{ label={_quote("packages/" + package + "/")}; '
            'style=rounded; color="#98a2b3"; bgcolor="#f8faff"; fontsize=18;'
        )
        for component in sorted(components[package]):
            if component == "engine":
                continue
            label = _html(component)
            rows = [
                '<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="12" '
                'COLOR="#344054" BGCOLOR="white">',
                f'<TR><TD BGCOLOR="#e5eaf8"><B>{label}</B></TD></TR>',
                '<TR><TD ALIGN="LEFT"><FONT POINT-SIZE="11" COLOR="#475467">'
                "&lt;&lt;component&gt;&gt;</FONT></TD></TR>",
                "</TABLE>",
            ]
            dot.append(f"{_quote(component)} [label=<" + "".join(rows) + ">];")
        dot.append("}")
    for source, target in sorted(dependencies):
        if source in {x for entries in components.values() for x in entries} and target in {
            x for entries in components.values() for x in entries
        }:
            dot.append(
                f"{_quote(source)} -> {_quote(target)} "
                '[style=dashed, arrowhead=vee, color="#475467"];'
            )
    for package in sorted(registrations & set(packages)):
        if "engine.model" in components.get("engine", set()):
            dot.append(
                f'{_quote(package)} -> {_quote("engine.model")} '
                '[style=dashed, arrowhead=vee, color="#2563eb", '
                'label="entry point: game config", fontsize=10];'
            )
    dot.append("}")
    return _run_dot("\n".join(dot))


if __name__ == "__main__":
    repository = Path(__file__).resolve().parents[2]
    (repository / ".agents/notes/diagrams/implementation.svg").write_text(
        render_component_diagram(repository), encoding="utf-8"
    )
    (repository / ".agents/notes/diagrams/implementation-classes.svg").write_text(
        render_class_diagram(repository), encoding="utf-8"
    )
